import math
from sqlalchemy import asc, desc, func, or_, select
from sqlalchemy.orm import Session

from app.middleware.error_handler import AppException
from app.models import (
    Assignment,
    Batch,
    Course,
    CourseModule,
    CourseStatus,
    Enrollment,
    Instructor,
    Lecture,
    StudyMaterial,
    User,
)
from app.schemas.course import (
    CourseCreate,
    CourseModuleCreate,
    CourseModuleUpdate,
    CourseUpdate,
)

ALLOWED_COURSE_SORT = {
    "id": Course.id,
    "title": Course.title,
    "code": Course.code,
    "category": Course.category,
    "fee_amount": Course.fee_amount,
    "status": Course.status,
    "created_at": Course.created_at,
}


def _get_instructor_id_for_user(db: Session, user_id: int) -> int | None:
    return db.scalar(select(Instructor.id).where(Instructor.user_id == user_id))


def _is_instructor_assigned(db: Session, instructor_id: int | None, course: Course) -> bool:
    if not instructor_id:
        return False
    if course.instructor_id == instructor_id:
        return True
    batch_match = db.scalar(
        select(Batch.id).where(
            Batch.course_id == course.id,
            Batch.instructor_id == instructor_id,
        )
    )
    return batch_match is not None


def _instructor_name(db: Session, instructor_id: int | None) -> str | None:
    if not instructor_id:
        return None
    return db.scalar(
        select(User.full_name)
        .join(Instructor, Instructor.user_id == User.id)
        .where(Instructor.id == instructor_id)
    )


def _serialize_course(db: Session, course: Course) -> dict:
    return {
        "id": course.id,
        "title": course.title,
        "code": course.code,
        "category": course.category,
        "description": course.description,
        "duration_weeks": course.duration_weeks,
        "fee_amount": course.fee_amount,
        "thumbnail_url": course.thumbnail_url,
        "status": course.status.value if hasattr(course.status, "value") else course.status,
        "instructor_id": course.instructor_id,
        "instructor_name": _instructor_name(db, course.instructor_id),
        "created_by": course.created_by,
        "created_at": course.created_at,
        "updated_at": course.updated_at,
    }


def list_courses(
    db: Session,
    current_user: User,
    *,
    q: str | None = None,
    category: str | None = None,
    status_filter: str | None = None,
    sort_by: str = "created_at",
    sort_dir: str = "desc",
    page: int = 1,
    page_size: int = 10,
) -> dict:
    role_name = current_user.role.name if current_user.role else ""
    stmt = select(Course)
    count_stmt = select(func.count(Course.id))

    # Role scoping
    if role_name == "Instructor":
        inst_id = _get_instructor_id_for_user(db, current_user.id)
        if not inst_id:
            return {"items": [], "total": 0, "page": page, "page_size": page_size, "total_pages": 1}
        batch_course_ids = select(Batch.course_id).where(Batch.instructor_id == inst_id)
        scope = or_(Course.instructor_id == inst_id, Course.id.in_(batch_course_ids))
        stmt = stmt.where(scope)
        count_stmt = count_stmt.where(scope)
    elif role_name == "Student":
        enrolled_course_ids = select(Enrollment.course_id).where(
            Enrollment.student_id == current_user.id
        )
        scope = or_(Course.status == CourseStatus.PUBLISHED, Course.id.in_(enrolled_course_ids))
        stmt = stmt.where(scope)
        count_stmt = count_stmt.where(scope)

    if q and q.strip():
        pattern = f"%{q.strip()}%"
        search_filter = or_(Course.title.ilike(pattern), Course.code.ilike(pattern))
        stmt = stmt.where(search_filter)
        count_stmt = count_stmt.where(search_filter)

    if category and category.strip():
        stmt = stmt.where(Course.category == category.strip())
        count_stmt = count_stmt.where(Course.category == category.strip())

    if status_filter:
        try:
            enum_status = CourseStatus(status_filter)
        except ValueError as exc:
            raise AppException(400, f"Invalid course status '{status_filter}'.", "INVALID_STATUS") from exc
        stmt = stmt.where(Course.status == enum_status)
        count_stmt = count_stmt.where(Course.status == enum_status)

    sort_col = ALLOWED_COURSE_SORT.get(sort_by, Course.created_at)
    order_fn = asc if sort_dir.lower() == "asc" else desc
    stmt = stmt.order_by(order_fn(sort_col))

    total = db.scalar(count_stmt) or 0
    total_pages = max(1, math.ceil(total / page_size)) if total > 0 else 1
    offset = (page - 1) * page_size

    courses = list(db.scalars(stmt.offset(offset).limit(page_size)).all())
    return {
        "items": [_serialize_course(db, c) for c in courses],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
    }


def create_course(db: Session, payload: CourseCreate, admin_user: User) -> dict:
    code = payload.code.strip().upper()
    if db.scalar(select(Course).where(Course.code == code)):
        raise AppException(409, "A course with this code already exists.", "DUPLICATE_COURSE_CODE")

    if payload.instructor_id is not None:
        inst = db.scalar(select(Instructor).where(Instructor.id == payload.instructor_id))
        if not inst:
            raise AppException(404, "Instructor not found.", "INSTRUCTOR_NOT_FOUND")

    course = Course(
        title=payload.title.strip(),
        code=code,
        category=payload.category.strip() if payload.category else None,
        description=payload.description,
        duration_weeks=payload.duration_weeks,
        fee_amount=payload.fee_amount,
        thumbnail_url=payload.thumbnail_url,
        instructor_id=payload.instructor_id,
        status=CourseStatus(payload.status),
        created_by=admin_user.id,
    )
    db.add(course)
    db.commit()
    db.refresh(course)
    return _serialize_course(db, course)


def get_course_detail(db: Session, course_id: int, current_user: User) -> dict:
    course = db.scalar(select(Course).where(Course.id == course_id))
    if not course:
        raise AppException(404, "Course not found.", "COURSE_NOT_FOUND")

    role_name = current_user.role.name if current_user.role else ""
    is_enrolled = False

    if role_name == "Instructor":
        inst_id = _get_instructor_id_for_user(db, current_user.id)
        if not _is_instructor_assigned(db, inst_id, course):
            raise AppException(403, "You are not assigned to this course.", "FORBIDDEN")
    elif role_name == "Student":
        enr = db.scalar(
            select(Enrollment.id).where(
                Enrollment.student_id == current_user.id,
                Enrollment.course_id == course.id,
            )
        )
        is_enrolled = enr is not None
        if course.status != CourseStatus.PUBLISHED and not is_enrolled:
            raise AppException(403, "You do not have access to this course.", "FORBIDDEN")

    modules = list(
        db.scalars(
            select(CourseModule)
            .where(CourseModule.course_id == course.id)
            .order_by(CourseModule.sort_order.asc(), CourseModule.id.asc())
        ).all()
    )
    enrollment_count = db.scalar(
        select(func.count(Enrollment.id)).where(Enrollment.course_id == course.id)
    ) or 0

    data = _serialize_course(db, course)
    data["modules"] = modules
    data["enrollment_count"] = enrollment_count
    data["is_enrolled"] = is_enrolled
    return data


def update_course(db: Session, course_id: int, payload: CourseUpdate, current_user: User) -> dict:
    course = db.scalar(select(Course).where(Course.id == course_id))
    if not course:
        raise AppException(404, "Course not found.", "COURSE_NOT_FOUND")

    role_name = current_user.role.name if current_user.role else ""
    if role_name == "Instructor":
        inst_id = _get_instructor_id_for_user(db, current_user.id)
        if not _is_instructor_assigned(db, inst_id, course):
            raise AppException(403, "You cannot edit an unassigned course.", "FORBIDDEN")
        # Limited edit: instructors may only update description and thumbnail_url
        if any(
            val is not None
            for val in (
                payload.title,
                payload.code,
                payload.category,
                payload.duration_weeks,
                payload.fee_amount,
                payload.instructor_id,
            )
        ):
            raise AppException(
                403,
                "Instructors can only update description and thumbnail URL.",
                "FORBIDDEN",
            )
        if payload.description is not None:
            course.description = payload.description
        if payload.thumbnail_url is not None:
            course.thumbnail_url = payload.thumbnail_url
        db.commit()
        db.refresh(course)
        return _serialize_course(db, course)

    if role_name != "Admin":
        raise AppException(403, "Only Admins or assigned Instructors can edit courses.", "FORBIDDEN")

    if payload.code is not None:
        new_code = payload.code.strip().upper()
        if new_code != course.code and db.scalar(select(Course).where(Course.code == new_code)):
            raise AppException(409, "A course with this code already exists.", "DUPLICATE_COURSE_CODE")
        course.code = new_code

    if payload.instructor_id is not None:
        if not db.scalar(select(Instructor).where(Instructor.id == payload.instructor_id)):
            raise AppException(404, "Instructor not found.", "INSTRUCTOR_NOT_FOUND")
        course.instructor_id = payload.instructor_id

    if payload.title is not None:
        course.title = payload.title.strip()
    if payload.category is not None:
        course.category = payload.category.strip() or None
    if payload.description is not None:
        course.description = payload.description
    if payload.duration_weeks is not None:
        course.duration_weeks = payload.duration_weeks
    if payload.fee_amount is not None:
        course.fee_amount = payload.fee_amount
    if payload.thumbnail_url is not None:
        course.thumbnail_url = payload.thumbnail_url

    db.commit()
    db.refresh(course)
    return _serialize_course(db, course)


def set_course_publish(db: Session, course_id: int, publish: bool) -> dict:
    course = db.scalar(select(Course).where(Course.id == course_id))
    if not course:
        raise AppException(404, "Course not found.", "COURSE_NOT_FOUND")
    if course.status == CourseStatus.ARCHIVED:
        raise AppException(400, "Archived courses cannot be published directly.", "COURSE_ARCHIVED")
    course.status = CourseStatus.PUBLISHED if publish else CourseStatus.DRAFT
    db.commit()
    db.refresh(course)
    return _serialize_course(db, course)


def archive_course(db: Session, course_id: int) -> dict:
    course = db.scalar(select(Course).where(Course.id == course_id))
    if not course:
        raise AppException(404, "Course not found.", "COURSE_NOT_FOUND")
    course.status = CourseStatus.ARCHIVED
    db.commit()
    db.refresh(course)
    return _serialize_course(db, course)


def delete_course(db: Session, course_id: int) -> None:
    course = db.scalar(select(Course).where(Course.id == course_id))
    if not course:
        raise AppException(404, "Course not found.", "COURSE_NOT_FOUND")

    has_batches = db.scalar(select(Batch.id).where(Batch.course_id == course_id)) is not None
    has_enrollments = db.scalar(select(Enrollment.id).where(Enrollment.course_id == course_id)) is not None
    if has_batches or has_enrollments:
        raise AppException(
            409,
            "Cannot delete course with active enrollments or batches; archive it instead.",
            "COURSE_IN_USE",
        )

    db.delete(course)
    db.commit()


def _ensure_module_write_access(db: Session, course_id: int, current_user: User) -> Course:
    course = db.scalar(select(Course).where(Course.id == course_id))
    if not course:
        raise AppException(404, "Course not found.", "COURSE_NOT_FOUND")
    role_name = current_user.role.name if current_user.role else ""
    if role_name == "Admin":
        return course
    if role_name == "Instructor":
        inst_id = _get_instructor_id_for_user(db, current_user.id)
        if _is_instructor_assigned(db, inst_id, course):
            return course
    raise AppException(403, "You do not have permission to manage modules for this course.", "FORBIDDEN")


def create_module(
    db: Session, course_id: int, payload: CourseModuleCreate, current_user: User
) -> CourseModule:
    _ensure_module_write_access(db, course_id, current_user)
    mod = CourseModule(
        course_id=course_id,
        title=payload.title.strip(),
        description=payload.description,
        sort_order=payload.sort_order,
    )
    db.add(mod)
    db.commit()
    db.refresh(mod)
    return mod


def update_module(
    db: Session,
    course_id: int,
    module_id: int,
    payload: CourseModuleUpdate,
    current_user: User,
) -> CourseModule:
    _ensure_module_write_access(db, course_id, current_user)
    mod = db.scalar(
        select(CourseModule).where(
            CourseModule.id == module_id,
            CourseModule.course_id == course_id,
        )
    )
    if not mod:
        raise AppException(404, "Course module not found.", "MODULE_NOT_FOUND")

    if payload.title is not None:
        mod.title = payload.title.strip()
    if payload.description is not None:
        mod.description = payload.description
    if payload.sort_order is not None:
        mod.sort_order = payload.sort_order

    db.commit()
    db.refresh(mod)
    return mod


def delete_module(db: Session, course_id: int, module_id: int, current_user: User) -> None:
    _ensure_module_write_access(db, course_id, current_user)
    mod = db.scalar(
        select(CourseModule).where(
            CourseModule.id == module_id,
            CourseModule.course_id == course_id,
        )
    )
    if not mod:
        raise AppException(404, "Course module not found.", "MODULE_NOT_FOUND")

    has_children = any([
        db.scalar(select(Lecture.id).where(Lecture.module_id == module_id)) is not None,
        db.scalar(select(StudyMaterial.id).where(StudyMaterial.module_id == module_id)) is not None,
        db.scalar(select(Assignment.id).where(Assignment.module_id == module_id)) is not None,
    ])
    if has_children:
        raise AppException(
            409,
            "Cannot delete module with linked lectures, materials, or assignments.",
            "MODULE_IN_USE",
        )

    db.delete(mod)
    db.commit()
