from collections import defaultdict
from datetime import date
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.middleware.error_handler import AppException
from app.models import (
    Attendance,
    AttendanceAudit,
    AttendanceStatus,
    Batch,
    BatchStudent,
    ClassSession,
    ClassSessionStatus,
    Instructor,
    User,
)
from app.schemas.attendance import AttendanceBulkRequest, AttendanceSingleCreate


def _ensure_batch_write_access(db: Session, batch_id: int, current_user: User) -> Batch:
    batch = db.scalar(select(Batch).where(Batch.id == batch_id))
    if not batch:
        raise AppException(404, "Batch not found.", "BATCH_NOT_FOUND")

    role_name = current_user.role.name if current_user.role else ""
    if role_name == "Admin":
        return batch
    if role_name == "Instructor":
        inst_id = db.scalar(select(Instructor.id).where(Instructor.user_id == current_user.id))
        if inst_id and batch.instructor_id == inst_id:
            return batch
    raise AppException(403, "You do not have permission to manage attendance for this batch.", "FORBIDDEN")


def get_roster_for_date(
    db: Session, batch_id: int, class_date: date, current_user: User
) -> dict:
    batch = _ensure_batch_write_access(db, batch_id, current_user)

    session_row = db.scalar(
        select(ClassSession).where(
            ClassSession.batch_id == batch_id,
            ClassSession.class_date == class_date,
        )
    )
    session_status = (
        session_row.status.value if session_row and hasattr(session_row.status, "value") else "held"
    )

    student_rows = db.execute(
        select(BatchStudent, User)
        .join(User, User.id == BatchStudent.student_id)
        .where(
            BatchStudent.batch_id == batch_id,
            BatchStudent.is_active == True,  # noqa: E712
        )
        .order_by(User.full_name.asc())
    ).all()

    att_rows = list(
        db.scalars(
            select(Attendance).where(
                Attendance.batch_id == batch_id,
                Attendance.class_date == class_date,
            )
        ).all()
    )
    att_by_student = {a.student_id: a for a in att_rows}

    students = []
    for _bs, u in student_rows:
        att = att_by_student.get(u.id)
        students.append(
            {
                "student_id": u.id,
                "full_name": u.full_name,
                "email": u.email,
                "status": (
                    att.status.value if att and hasattr(att.status, "value") else (att.status if att else None)
                ),
                "remarks": att.remarks if att else None,
            }
        )

    return {
        "batch_id": batch.id,
        "batch_name": batch.name,
        "class_date": class_date,
        "session_status": session_status,
        "notes": session_row.notes if session_row else None,
        "students": students,
    }


def create_single_attendance(
    db: Session, payload: AttendanceSingleCreate, current_user: User
) -> dict:
    _ensure_batch_write_access(db, payload.batch_id, current_user)

    in_batch = db.scalar(
        select(BatchStudent.id).where(
            BatchStudent.batch_id == payload.batch_id,
            BatchStudent.student_id == payload.student_id,
            BatchStudent.is_active == True,  # noqa: E712
        )
    )
    if not in_batch:
        raise AppException(400, "Student is not enrolled in this batch.", "STUDENT_NOT_IN_BATCH")

    existing = db.scalar(
        select(Attendance).where(
            Attendance.student_id == payload.student_id,
            Attendance.batch_id == payload.batch_id,
            Attendance.class_date == payload.class_date,
        )
    )
    if existing:
        raise AppException(
            409,
            "Attendance already recorded for this student, batch, and date.",
            "DUPLICATE_ATTENDANCE",
        )

    att = Attendance(
        student_id=payload.student_id,
        batch_id=payload.batch_id,
        class_date=payload.class_date,
        status=AttendanceStatus(payload.status),
        marked_by=current_user.id,
        remarks=payload.remarks,
    )
    db.add(att)
    db.flush()

    db.add(
        AttendanceAudit(
            attendance_id=att.id,
            student_id=att.student_id,
            batch_id=att.batch_id,
            class_date=att.class_date,
            old_status=None,
            new_status=att.status.value,
            changed_by=current_user.id,
            remarks=payload.remarks,
        )
    )
    db.commit()
    db.refresh(att)
    return {
        "id": att.id,
        "student_id": att.student_id,
        "batch_id": att.batch_id,
        "batch_name": None,
        "class_date": att.class_date,
        "status": att.status.value,
        "remarks": att.remarks,
        "session_status": "held",
        "marked_by": att.marked_by,
        "created_at": att.created_at,
        "updated_at": att.updated_at,
    }


def bulk_upsert_attendance(
    db: Session, payload: AttendanceBulkRequest, current_user: User
) -> dict:
    """Upsert class session status and student attendance records with audit logging."""
    _ensure_batch_write_access(db, payload.batch_id, current_user)

    # 1. Upsert ClassSession
    session_row = db.scalar(
        select(ClassSession).where(
            ClassSession.batch_id == payload.batch_id,
            ClassSession.class_date == payload.class_date,
        )
    )
    if session_row:
        session_row.status = ClassSessionStatus(payload.session_status)
        session_row.notes = payload.notes
        session_row.updated_by = current_user.id
    else:
        session_row = ClassSession(
            batch_id=payload.batch_id,
            class_date=payload.class_date,
            status=ClassSessionStatus(payload.session_status),
            notes=payload.notes,
            updated_by=current_user.id,
        )
        db.add(session_row)

    # 2. Upsert Attendance records + write AttendanceAudit on create or change
    enrolled_ids = set(
        db.scalars(
            select(BatchStudent.student_id).where(
                BatchStudent.batch_id == payload.batch_id,
                BatchStudent.is_active == True,  # noqa: E712
            )
        ).all()
    )

    for rec in payload.records:
        if rec.student_id not in enrolled_ids:
            raise AppException(
                400,
                f"Student {rec.student_id} is not active in batch {payload.batch_id}.",
                "STUDENT_NOT_IN_BATCH",
            )

        existing = db.scalar(
            select(Attendance).where(
                Attendance.student_id == rec.student_id,
                Attendance.batch_id == payload.batch_id,
                Attendance.class_date == payload.class_date,
            )
        )
        new_enum = AttendanceStatus(rec.status)
        if existing:
            old_val = existing.status.value if hasattr(existing.status, "value") else existing.status
            if old_val != new_enum.value or existing.remarks != rec.remarks:
                existing.status = new_enum
                existing.remarks = rec.remarks
                existing.marked_by = current_user.id
                db.add(
                    AttendanceAudit(
                        attendance_id=existing.id,
                        student_id=rec.student_id,
                        batch_id=payload.batch_id,
                        class_date=payload.class_date,
                        old_status=old_val,
                        new_status=new_enum.value,
                        changed_by=current_user.id,
                        remarks=rec.remarks,
                    )
                )
        else:
            att = Attendance(
                student_id=rec.student_id,
                batch_id=payload.batch_id,
                class_date=payload.class_date,
                status=new_enum,
                marked_by=current_user.id,
                remarks=rec.remarks,
            )
            db.add(att)
            db.flush()
            db.add(
                AttendanceAudit(
                    attendance_id=att.id,
                    student_id=rec.student_id,
                    batch_id=payload.batch_id,
                    class_date=payload.class_date,
                    old_status=None,
                    new_status=new_enum.value,
                    changed_by=current_user.id,
                    remarks=rec.remarks,
                )
            )

    db.commit()
    return get_roster_for_date(db, payload.batch_id, payload.class_date, current_user)


def compute_student_attendance_summary(
    db: Session, student_id: int, batch_id: int | None = None
) -> dict:
    """Compute attendance %, monthly breakdown, and history excluding cancelled/holiday/leave."""
    stmt = (
        select(Attendance, Batch, ClassSession)
        .join(Batch, Batch.id == Attendance.batch_id)
        .outerjoin(
            ClassSession,
            (ClassSession.batch_id == Attendance.batch_id)
            & (ClassSession.class_date == Attendance.class_date),
        )
        .where(Attendance.student_id == student_id)
        .order_by(Attendance.class_date.desc())
    )
    if batch_id is not None:
        stmt = stmt.where(Attendance.batch_id == batch_id)

    rows = db.execute(stmt).all()

    total_present = 0
    total_absent = 0
    total_leave = 0
    monthly: dict[str, dict[str, int]] = defaultdict(
        lambda: {"present": 0, "absent": 0, "approved_leave": 0}
    )
    records = []

    for att, batch, sess in rows:
        sess_status = (
            sess.status.value if sess and hasattr(sess.status, "value") else "held"
        )
        att_status = att.status.value if hasattr(att.status, "value") else att.status
        month_key = att.class_date.strftime("%Y-%m")

        records.append(
            {
                "id": att.id,
                "student_id": att.student_id,
                "batch_id": att.batch_id,
                "batch_name": batch.name,
                "class_date": att.class_date,
                "status": att_status,
                "remarks": att.remarks,
                "session_status": sess_status,
                "marked_by": att.marked_by,
                "created_at": att.created_at,
                "updated_at": att.updated_at,
            }
        )

        # Cancelled classes & holidays are excluded from numerator and denominator
        if sess_status in (ClassSessionStatus.CANCELLED.value, ClassSessionStatus.HOLIDAY.value):
            continue

        if att_status == AttendanceStatus.PRESENT.value:
            total_present += 1
            monthly[month_key]["present"] += 1
        elif att_status == AttendanceStatus.ABSENT.value:
            total_absent += 1
            monthly[month_key]["absent"] += 1
        elif att_status == AttendanceStatus.APPROVED_LEAVE.value:
            total_leave += 1
            monthly[month_key]["approved_leave"] += 1

    eligible = total_present + total_absent
    overall_pct = round((total_present / eligible) * 100.0, 2) if eligible > 0 else 0.0

    monthly_summary = []
    for m_key in sorted(monthly.keys(), reverse=True):
        m_data = monthly[m_key]
        m_elig = m_data["present"] + m_data["absent"]
        m_pct = round((m_data["present"] / m_elig) * 100.0, 2) if m_elig > 0 else 0.0
        monthly_summary.append(
            {
                "month": m_key,
                "present": m_data["present"],
                "absent": m_data["absent"],
                "approved_leave": m_data["approved_leave"],
                "eligible_classes": m_elig,
                "percentage": m_pct,
            }
        )

    return {
        "student_id": student_id,
        "total_present": total_present,
        "total_absent": total_absent,
        "total_approved_leave": total_leave,
        "total_eligible_classes": eligible,
        "attendance_percentage": overall_pct,
        "monthly_summary": monthly_summary,
        "records": records,
    }
