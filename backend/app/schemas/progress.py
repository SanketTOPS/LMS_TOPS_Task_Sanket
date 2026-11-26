from pydantic import BaseModel


class CourseProgressItem(BaseModel):
    course_id: int
    course_title: str
    course_code: str
    lectures_completed: int
    lectures_total: int
    lecture_percentage: float
    assignments_submitted: int
    assignments_total: int
    assignment_percentage: float
    quizzes_attempted: int
    quizzes_total: int
    quiz_percentage: float
    course_progress_percentage: float
    attendance_percentage: float
    all_quizzes_attempted: bool
    is_complete: bool


class StudentProgressResponse(BaseModel):
    student_id: int
    student_name: str
    courses: list[CourseProgressItem]
    overall_progress_percentage: float
    overall_attendance_percentage: float
