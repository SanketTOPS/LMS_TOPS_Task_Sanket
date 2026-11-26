from datetime import datetime, timezone
from pathlib import Path

from fastapi import UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.middleware.error_handler import AppException
from app.models import (
    Batch,
    Course,
    CourseModule,
    Enrollment,
    Instructor,
    Lecture,
    LectureProgress,
    StudyMaterial,
    User,
)
from app.schemas.lecture import LectureCreate, LectureUpdate
from app.services.storage_service import (
    STUDY_MATERIAL_EXTENSIONS,
    VIDEO_EXTENSIONS,
    get_storage_backend,
    validate_and_save_upload,
)


def _get_instructor_id(db: Session, user_id: int) -> int | None:
    return db.scalar(select(Instructor.id).where(Instructor.user_id == user_id))


def _is_instructor_assigned_to_course(db: Session, user_id: int, course: Course) -> bool:
    inst_id = _get_instructor_id(db, user_id)
    if not inst_id:
        return False
    if course.instructor_id == inst_id:
        return True
    return (
        db.scalar(
            select(Batch.id).where(
                Batch.course_id == course.id,
                Batch.instructor_id == inst_id,
            )
        )
        is not None
    )


def _is_student_enrolled(db: Session, student_id: int, course_id: int) -> bool:
    return (
        db.scalar(
            select(Enrollment.id).where(
                Enrollment.student_id == student_id,
                Enrollment.course_id == course_id,
            )
        )
        is not None
    )


def ensure_course_read_access(db: Session, course_id: int, current_user: User) -> Course:
    course = db.scalar(select(Course).where(Course.id == course_id))
    if not course:
        raise AppException(404, "Course not found.", "COURSE_NOT_FOUND")

    role_name = current_user.role.name if current_user.role else ""
    if role_name == "Admin":
        return course
    if role_name == "Instructor" and _is_instructor_assigned_to_course(db, current_user.id, course):
        return course
    if role_name == "Student" and _is_student_enrolled(db, current_user.id, course.id):
        return course

    raise AppException(403, "You do not have access to this course's content.", "FORBIDDEN")


def ensure_course_write_access(db: Session, course_id: int, current_user: User) -> Course:
    course = db.scalar(select(Course).where(Course.id == course_id))
    if not course:
        raise AppException(404, "Course not found.", "COURSE_NOT_FOUND")

    role_name = current_user.role.name if current_user.role else ""
    if role_name == "Admin":
        return course
    if role_name == "Instructor" and _is_instructor_assigned_to_course(db, current_user.id, course):
        return course

    raise AppException(403, "You do not have permission to manage lectures in this course.", "FORBIDDEN")


def _serialize_lecture(
    db: Session,
    lecture: Lecture,
    student_id: int | None = None,
) -> dict:
    materials = list(
        db.scalars(
            select(StudyMaterial)
            .where(StudyMaterial.lecture_id == lecture.id)
            .order_by(StudyMaterial.id.asc())
        ).all()
    )
    is_completed = False
    completed_at = None
    if student_id is not None:
        prog = db.scalar(
            select(LectureProgress).where(
                LectureProgress.student_id == student_id,
                LectureProgress.lecture_id == lecture.id,
            )
        )
        if prog:
            is_completed = prog.is_completed
            completed_at = prog.completed_at

    return {
        "id": lecture.id,
        "module_id": lecture.module_id,
        "batch_id": lecture.batch_id,
        "title": lecture.title,
        "description": lecture.description,
        "video_url": lecture.video_url,
        "duration_minutes": lecture.duration_minutes,
        "sort_order": lecture.sort_order,
        "is_published": lecture.is_published,
        "created_by": lecture.created_by,
        "created_at": lecture.created_at,
        "updated_at": lecture.updated_at,
        "materials": materials,
        "is_completed": is_completed,
        "completed_at": completed_at,
    }


def list_course_lectures(db: Session, course_id: int, current_user: User) -> list[dict]:
    ensure_course_read_access(db, course_id, current_user)
    role_name = current_user.role.name if current_user.role else ""

    stmt = (
        select(Lecture)
        .join(CourseModule, CourseModule.id == Lecture.module_id)
        .where(CourseModule.course_id == course_id)
        .order_by(CourseModule.sort_order.asc(), Lecture.sort_order.asc(), Lecture.id.asc())
    )
    if role_name == "Student":
        stmt = stmt.where(Lecture.is_published == True)  # noqa: E712

    lectures = list(db.scalars(stmt).all())
    stu_id = current_user.id if role_name == "Student" else None
    return [_serialize_lecture(db, lec, student_id=stu_id) for lec in lectures]


def create_lecture(db: Session, payload: LectureCreate, current_user: User) -> dict:
    module = db.scalar(select(CourseModule).where(CourseModule.id == payload.module_id))
    if not module:
        raise AppException(404, "Course module not found.", "MODULE_NOT_FOUND")

    ensure_course_write_access(db, module.course_id, current_user)

    lecture = Lecture(
        module_id=payload.module_id,
        batch_id=payload.batch_id,
        title=payload.title.strip(),
        description=payload.description,
        video_url=payload.video_url,
        duration_minutes=payload.duration_minutes,
        sort_order=payload.sort_order,
        is_published=payload.is_published,
        created_by=current_user.id,
    )
    db.add(lecture)
    db.commit()
    db.refresh(lecture)
    return _serialize_lecture(db, lecture)


def get_lecture(db: Session, lecture_id: int, current_user: User) -> dict:
    lecture = db.scalar(select(Lecture).where(Lecture.id == lecture_id))
    if not lecture:
        raise AppException(404, "Lecture not found.", "LECTURE_NOT_FOUND")

    module = db.scalar(select(CourseModule).where(CourseModule.id == lecture.module_id))
    ensure_course_read_access(db, module.course_id, current_user)

    role_name = current_user.role.name if current_user.role else ""
    if role_name == "Student" and not lecture.is_published:
        raise AppException(403, "This lecture is not published.", "FORBIDDEN")

    stu_id = current_user.id if role_name == "Student" else None
    return _serialize_lecture(db, lecture, student_id=stu_id)


def update_lecture(db: Session, lecture_id: int, payload: LectureUpdate, current_user: User) -> dict:
    lecture = db.scalar(select(Lecture).where(Lecture.id == lecture_id))
    if not lecture:
        raise AppException(404, "Lecture not found.", "LECTURE_NOT_FOUND")

    module = db.scalar(select(CourseModule).where(CourseModule.id == lecture.module_id))
    ensure_course_write_access(db, module.course_id, current_user)

    if payload.module_id is not None and payload.module_id != lecture.module_id:
        new_mod = db.scalar(select(CourseModule).where(CourseModule.id == payload.module_id))
        if not new_mod or new_mod.course_id != module.course_id:
            raise AppException(400, "Target module must belong to the same course.", "INVALID_MODULE")
        lecture.module_id = payload.module_id

    if payload.batch_id is not None:
        lecture.batch_id = payload.batch_id
    if payload.title is not None:
        lecture.title = payload.title.strip()
    if payload.description is not None:
        lecture.description = payload.description
    if payload.video_url is not None:
        lecture.video_url = payload.video_url or None
    if payload.duration_minutes is not None:
        lecture.duration_minutes = payload.duration_minutes
    if payload.sort_order is not None:
        lecture.sort_order = payload.sort_order
    if payload.is_published is not None:
        lecture.is_published = payload.is_published

    db.commit()
    db.refresh(lecture)
    return _serialize_lecture(db, lecture)


def delete_lecture(db: Session, lecture_id: int, current_user: User) -> None:
    lecture = db.scalar(select(Lecture).where(Lecture.id == lecture_id))
    if not lecture:
        raise AppException(404, "Lecture not found.", "LECTURE_NOT_FOUND")

    module = db.scalar(select(CourseModule).where(CourseModule.id == lecture.module_id))
    ensure_course_write_access(db, module.course_id, current_user)

    has_progress = db.scalar(
        select(LectureProgress.id).where(LectureProgress.lecture_id == lecture_id)
    ) is not None
    has_materials = db.scalar(
        select(StudyMaterial.id).where(StudyMaterial.lecture_id == lecture_id)
    ) is not None
    if has_progress or has_materials:
        raise AppException(
            409,
            "Cannot delete lecture with existing study materials or student progress.",
            "LECTURE_IN_USE",
        )

    db.delete(lecture)
    db.commit()


def reorder_lectures(
    db: Session, module_id: int, lecture_ids: list[int], current_user: User
) -> list[dict]:
    module = db.scalar(select(CourseModule).where(CourseModule.id == module_id))
    if not module:
        raise AppException(404, "Course module not found.", "MODULE_NOT_FOUND")

    ensure_course_write_access(db, module.course_id, current_user)

    lectures = list(
        db.scalars(select(Lecture).where(Lecture.module_id == module_id)).all()
    )
    by_id = {lec.id: lec for lec in lectures}

    for idx, lid in enumerate(lecture_ids, start=1):
        if lid not in by_id:
            raise AppException(400, f"Lecture {lid} does not belong to module {module_id}.", "INVALID_LECTURE")
        by_id[lid].sort_order = idx

    db.commit()
    ordered = sorted(lectures, key=lambda l: (l.sort_order, l.id))
    return [_serialize_lecture(db, l) for l in ordered]


async def upload_lecture_video(
    db: Session,
    lecture_id: int,
    file: UploadFile,
    current_user: User,
) -> dict:
    lecture = db.scalar(select(Lecture).where(Lecture.id == lecture_id))
    if not lecture:
        raise AppException(404, "Lecture not found.", "LECTURE_NOT_FOUND")

    module = db.scalar(select(CourseModule).where(CourseModule.id == lecture.module_id))
    ensure_course_write_access(db, module.course_id, current_user)

    storage = get_storage_backend()
    await validate_and_save_upload(
        file,
        allowed_extensions=VIDEO_EXTENSIONS,
        subdir=f"videos/{lecture.id}",
        storage=storage,
    )
    lecture.video_url = f"/api/lectures/{lecture.id}/video"
    db.commit()
    db.refresh(lecture)
    return _serialize_lecture(db, lecture)


def resolve_lecture_video_path(db: Session, lecture_id: int, current_user: User) -> Path:
    lecture = db.scalar(select(Lecture).where(Lecture.id == lecture_id))
    if not lecture:
        raise AppException(404, "Lecture not found.", "LECTURE_NOT_FOUND")

    module = db.scalar(select(CourseModule).where(CourseModule.id == lecture.module_id))
    ensure_course_read_access(db, module.course_id, current_user)

    storage = get_storage_backend()
    video_dir = storage.resolve_path(f"videos/{lecture.id}")
    if not video_dir.exists():
        raise AppException(404, "Video file not found.", "FILE_NOT_FOUND")

    files = [p for p in video_dir.iterdir() if p.is_file()]
    if not files:
        raise AppException(404, "Video file not found.", "FILE_NOT_FOUND")
    return files[-1]


def mark_lecture_complete(db: Session, lecture_id: int, current_user: User) -> LectureProgress:
    lecture = db.scalar(select(Lecture).where(Lecture.id == lecture_id))
    if not lecture:
        raise AppException(404, "Lecture not found.", "LECTURE_NOT_FOUND")

    module = db.scalar(select(CourseModule).where(CourseModule.id == lecture.module_id))
    ensure_course_read_access(db, module.course_id, current_user)

    existing = db.scalar(
        select(LectureProgress).where(
            LectureProgress.student_id == current_user.id,
            LectureProgress.lecture_id == lecture_id,
        )
    )
    if existing:
        if not existing.is_completed:
            existing.is_completed = True
            existing.completed_at = datetime.now(timezone.utc)
            db.commit()
            db.refresh(existing)
        return existing

    progress = LectureProgress(
        student_id=current_user.id,
        lecture_id=lecture_id,
        is_completed=True,
        completed_at=datetime.now(timezone.utc),
    )
    db.add(progress)
    db.commit()
    db.refresh(progress)
    return progress


def get_course_progress(db: Session, course_id: int, current_user: User) -> dict:
    ensure_course_read_access(db, course_id, current_user)

    published_lectures = list(
        db.scalars(
            select(Lecture.id)
            .join(CourseModule, CourseModule.id == Lecture.module_id)
            .where(CourseModule.course_id == course_id, Lecture.is_published == True)  # noqa: E712
        ).all()
    )
    total = len(published_lectures)
    if total == 0:
        return {
            "course_id": course_id,
            "total_lectures": 0,
            "completed_lectures": 0,
            "progress_percentage": 0.0,
            "completed_lecture_ids": [],
        }

    completed_ids = list(
        db.scalars(
            select(LectureProgress.lecture_id).where(
                LectureProgress.student_id == current_user.id,
                LectureProgress.lecture_id.in_(published_lectures),
                LectureProgress.is_completed == True,  # noqa: E712
            )
        ).all()
    )
    pct = round((len(completed_ids) / total) * 100.0, 2)
    return {
        "course_id": course_id,
        "total_lectures": total,
        "completed_lectures": len(completed_ids),
        "progress_percentage": pct,
        "completed_lecture_ids": completed_ids,
    }


async def upload_study_material(
    db: Session,
    *,
    course_id: int,
    module_id: int | None,
    lecture_id: int | None,
    title: str,
    file: UploadFile,
    current_user: User,
) -> StudyMaterial:
    ensure_course_write_access(db, course_id, current_user)

    material = StudyMaterial(
        course_id=course_id,
        module_id=module_id,
        lecture_id=lecture_id,
        title=title.strip(),
        file_name=Path(file.filename or "material").name,
        file_url="",
        file_size_bytes=0,
        mime_type=file.content_type,
        uploaded_by=current_user.id,
    )
    db.add(material)
    db.flush()

    storage = get_storage_backend()
    try:
        stored = await validate_and_save_upload(
            file,
            allowed_extensions=STUDY_MATERIAL_EXTENSIONS,
            subdir=f"materials/{material.id}",
            storage=storage,
        )
    except Exception:
        db.rollback()
        raise

    material.file_name = stored.original_name
    material.file_size_bytes = stored.size_bytes
    material.mime_type = stored.mime_type
    material.file_url = f"/api/materials/{material.id}/download"
    db.commit()
    db.refresh(material)
    return material


def resolve_material_download(
    db: Session, material_id: int, current_user: User
) -> tuple[StudyMaterial, Path]:
    material = db.scalar(select(StudyMaterial).where(StudyMaterial.id == material_id))
    if not material:
        raise AppException(404, "Study material not found.", "MATERIAL_NOT_FOUND")

    ensure_course_read_access(db, material.course_id, current_user)

    storage = get_storage_backend()
    mat_dir = storage.resolve_path(f"materials/{material.id}")
    if not mat_dir.exists():
        raise AppException(404, "Material file not found on storage.", "FILE_NOT_FOUND")

    files = [p for p in mat_dir.iterdir() if p.is_file()]
    if not files:
        raise AppException(404, "Material file not found on storage.", "FILE_NOT_FOUND")
    return material, files[0]


def delete_study_material(db: Session, material_id: int, current_user: User) -> None:
    material = db.scalar(select(StudyMaterial).where(StudyMaterial.id == material_id))
    if not material:
        raise AppException(404, "Study material not found.", "MATERIAL_NOT_FOUND")

    ensure_course_write_access(db, material.course_id, current_user)

    storage = get_storage_backend()
    mat_dir = storage.resolve_path(f"materials/{material.id}")
    if mat_dir.exists():
        for p in mat_dir.iterdir():
            if p.is_file():
                p.unlink()
        mat_dir.rmdir()

    db.delete(material)
    db.commit()
