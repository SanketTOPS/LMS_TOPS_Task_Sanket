from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import get_current_user, require_role
from app.models.user import User
from app.schemas.auth import MessageResponse
from app.schemas.quiz import (
    AttemptActiveResponse,
    AttemptResultResponse,
    PaginatedQuizzesResponse,
    QuestionAdminResponse,
    QuestionCreate,
    QuestionUpdate,
    QuizCreate,
    QuizResponse,
    QuizResultRow,
    QuizUpdate,
    SaveAnswerRequest,
)
from app.services import quiz_service

router = APIRouter(tags=["Quizzes"])


@router.get("/api/quizzes", response_model=PaginatedQuizzesResponse)
def list_quizzes(
    course_id: int | None = Query(default=None),
    batch_id: int | None = Query(default=None),
    within_window: bool = Query(default=False),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PaginatedQuizzesResponse:
    """List quizzes scoped by role."""
    return PaginatedQuizzesResponse(
        **quiz_service.list_quizzes(
            db,
            current_user,
            course_id=course_id,
            batch_id=batch_id,
            within_window=within_window,
            page=page,
            page_size=page_size,
        )
    )


@router.post("/api/quizzes", response_model=QuizResponse, status_code=status.HTTP_201_CREATED)
def create_quiz(
    payload: QuizCreate,
    current_user: User = Depends(require_role(["Admin", "Instructor"])),
    db: Session = Depends(get_db),
) -> QuizResponse:
    """Admin or assigned Instructor: create a quiz."""
    return QuizResponse(**quiz_service.create_quiz(db, payload, current_user))


@router.get("/api/quizzes/{quiz_id}", response_model=QuizResponse)
def get_quiz(
    quiz_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> QuizResponse:
    """Get quiz metadata."""
    return QuizResponse(**quiz_service.get_quiz(db, quiz_id, current_user))


@router.put("/api/quizzes/{quiz_id}", response_model=QuizResponse)
def update_quiz(
    quiz_id: int,
    payload: QuizUpdate,
    current_user: User = Depends(require_role(["Admin", "Instructor"])),
    db: Session = Depends(get_db),
) -> QuizResponse:
    """Admin or assigned Instructor: update quiz."""
    return QuizResponse(**quiz_service.update_quiz(db, quiz_id, payload, current_user))


@router.delete("/api/quizzes/{quiz_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_quiz(
    quiz_id: int,
    current_user: User = Depends(require_role(["Admin", "Instructor"])),
    db: Session = Depends(get_db),
) -> None:
    """Admin or assigned Instructor: delete quiz (409 if attempts exist)."""
    quiz_service.delete_quiz(db, quiz_id, current_user)


@router.get("/api/quizzes/{quiz_id}/questions", response_model=list[QuestionAdminResponse])
def list_questions(
    quiz_id: int,
    current_user: User = Depends(require_role(["Admin", "Instructor"])),
    db: Session = Depends(get_db),
) -> list[QuestionAdminResponse]:
    """Admin or assigned Instructor: list questions including correct_option_id."""
    return [
        QuestionAdminResponse(**q)
        for q in quiz_service.list_admin_questions(db, quiz_id, current_user)
    ]


@router.post(
    "/api/quizzes/{quiz_id}/questions",
    response_model=QuestionAdminResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_question(
    quiz_id: int,
    payload: QuestionCreate,
    current_user: User = Depends(require_role(["Admin", "Instructor"])),
    db: Session = Depends(get_db),
) -> QuestionAdminResponse:
    """Admin or assigned Instructor: add an MCQ question with options."""
    return QuestionAdminResponse(**quiz_service.add_question(db, quiz_id, payload, current_user))


@router.put("/api/quizzes/{quiz_id}/questions/{question_id}", response_model=QuestionAdminResponse)
def update_question(
    quiz_id: int,
    question_id: int,
    payload: QuestionUpdate,
    current_user: User = Depends(require_role(["Admin", "Instructor"])),
    db: Session = Depends(get_db),
) -> QuestionAdminResponse:
    """Admin or assigned Instructor: update an MCQ question."""
    return QuestionAdminResponse(
        **quiz_service.update_question(db, quiz_id, question_id, payload, current_user)
    )


@router.delete(
    "/api/quizzes/{quiz_id}/questions/{question_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_question(
    quiz_id: int,
    question_id: int,
    current_user: User = Depends(require_role(["Admin", "Instructor"])),
    db: Session = Depends(get_db),
) -> None:
    """Admin or assigned Instructor: delete a question (409 if attempts exist)."""
    quiz_service.delete_question(db, quiz_id, question_id, current_user)


@router.get("/api/quizzes/{quiz_id}/results", response_model=list[QuizResultRow])
def list_quiz_results(
    quiz_id: int,
    current_user: User = Depends(require_role(["Admin", "Instructor"])),
    db: Session = Depends(get_db),
) -> list[QuizResultRow]:
    """Admin or assigned Instructor: view all student attempts and scores."""
    return [QuizResultRow(**r) for r in quiz_service.list_quiz_results(db, quiz_id, current_user)]


@router.post("/api/quizzes/{quiz_id}/start", response_model=AttemptActiveResponse)
def start_quiz(
    quiz_id: int,
    current_user: User = Depends(require_role(["Student"])),
    db: Session = Depends(get_db),
) -> AttemptActiveResponse:
    """Student: start or resume a quiz attempt (returns questions WITHOUT correct answers)."""
    return AttemptActiveResponse(**quiz_service.start_quiz_attempt(db, quiz_id, current_user))


@router.get(
    "/api/quiz-attempts/{attempt_id}",
    response_model=AttemptActiveResponse | AttemptResultResponse,
)
def get_attempt(
    attempt_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get active attempt (without correct answers) or submitted result (with review)."""
    return quiz_service.get_attempt(db, attempt_id, current_user)


@router.put("/api/quiz-attempts/{attempt_id}/answer", response_model=MessageResponse)
def save_answer(
    attempt_id: int,
    payload: SaveAnswerRequest,
    current_user: User = Depends(require_role(["Student"])),
    db: Session = Depends(get_db),
) -> MessageResponse:
    """Student: save selected option for a question while attempt is active."""
    res = quiz_service.save_attempt_answer(
        db, attempt_id, payload.question_id, payload.selected_option_id, current_user
    )
    return MessageResponse(**res)


@router.post("/api/quiz-attempts/{attempt_id}/submit", response_model=AttemptResultResponse)
def submit_attempt(
    attempt_id: int,
    current_user: User = Depends(require_role(["Student"])),
    db: Session = Depends(get_db),
) -> AttemptResultResponse:
    """Student: submit attempt; server computes score and pass/fail."""
    return AttemptResultResponse(**quiz_service.submit_attempt(db, attempt_id, current_user))
