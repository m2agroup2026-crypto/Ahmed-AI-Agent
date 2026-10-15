from datetime import UTC, timedelta
import hashlib
import secrets

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.auth.dependencies import get_current_user
from app.api.auth.permission_dependencies import require_permission
from app.database.dependencies import get_db
from app.models.role import Role
from app.models.user import User
from app.products.tutor.teachers.models import TeacherProfile
from .models import Assignment, Classroom, Enrollment, ExamAttempt, ExternalBook, now
from .schemas import (AssignmentCreate, BookCreate, ClassCreate, ClassUpdate, Join,
                      ProfileUpdate, Submission, numeric)

router = APIRouter(prefix="/api/v1/classroom", tags=["Human classrooms"])


def role_name(user):
    return user.role.name if user.role else "STUDENT"


def teacher(user: User = Depends(get_current_user)):
    if role_name(user) != "TEACHER":
        raise HTTPException(403, "Teacher role required")
    return user


def student(user: User = Depends(get_current_user)):
    if role_name(user) != "STUDENT":
        raise HTTPException(403, "Student role required")
    return user


def owned(db, class_id, user, active=False):
    item = db.get(Classroom, class_id)
    if not item or item.teacher_id != user.id:
        raise HTTPException(404, "Classroom not found")
    if active and item.archived:
        raise HTTPException(409, "Classroom is archived")
    return item


def accessible(db, class_id, user):
    item = db.get(Classroom, class_id)
    if not item or not (
        role_name(user) == "TEACHER" and item.teacher_id == user.id
        or role_name(user) == "STUDENT" and db.get(Enrollment, (class_id, user.id))
    ):
        raise HTTPException(404, "Classroom not found")
    return item


def assignment_access(db, assignment_id, user):
    item = db.get(Assignment, assignment_id)
    if not item:
        raise HTTPException(404, "Assignment not found")
    accessible(db, item.classroom_id, user)
    return item


def class_view(item):
    return {"id": item.id, "name": item.name, "archived": item.archived}


def public_questions(item):
    return [{"id": str(i), "prompt": q["prompt"]} for i, q in enumerate(item.questions, 1)]


def assignment_view(item, show_questions=True):
    return {"id": item.id, "classroom_id": item.classroom_id, "title": item.title,
            "lesson": item.lesson, "duration_minutes": item.duration_minutes,
            "provenance": item.provenance, "subject": "mathematics",
            "question_count": len(item.questions),
            "questions": public_questions(item) if show_questions else []}


def utc(value):
    # SQLite strips timezone information on reload; all stored times are UTC.
    return value.replace(tzinfo=UTC) if value is not None and value.tzinfo is None else value


def attempt_view(item, assignment):
    return {"id": item.id, "assignment_id": item.assignment_id, "student_id": item.student_id,
            "started_at": utc(item.started_at), "deadline": utc(item.deadline),
            "submitted_at": utc(item.submitted_at), "score": item.score,
            "total": len(assignment.questions)}


def invite_hash(code):
    return hashlib.sha256(code.encode()).hexdigest()


@router.get("/me")
def identity(user: User = Depends(get_current_user)):
    return {"id": user.id, "name": user.name, "role": role_name(user)}


@router.put("/teachers/{user_id}", dependencies=[Depends(require_permission("users.manage"))])
def provision_teacher(user_id: int, db: Session = Depends(get_db)):
    """Explicit identity administration using the platform's existing permission guard."""
    target = db.get(User, user_id)
    if not target:
        raise HTTPException(404, "Account not found")
    if not target.is_active or role_name(target) not in {"STUDENT", "TEACHER"}:
        raise HTTPException(409, "Account cannot be assigned the teacher role")
    role = db.query(Role).filter_by(name="TEACHER").first()
    if not role:
        role = Role(name="TEACHER")
        db.add(role)
        db.flush()
    target.role = role
    db.commit()
    return {"id": target.id, "name": target.name, "role": "TEACHER"}


@router.put("/teacher-profile")
def save_profile(data: ProfileUpdate, user: User = Depends(teacher), db: Session = Depends(get_db)):
    item = db.query(TeacherProfile).filter_by(user_id=user.id).first()
    if not item:
        item = TeacherProfile(user_id=user.id)
        db.add(item)
    item.bio = data.bio
    db.commit()
    return {"user_id": user.id, "bio": item.bio, "verification_status": item.verification_status}


@router.get("/classes")
def classes(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    query = db.query(Classroom)
    if role_name(user) == "TEACHER":
        query = query.filter(Classroom.teacher_id == user.id)
    elif role_name(user) == "STUDENT":
        query = query.join(Enrollment).filter(Enrollment.student_id == user.id)
    else:
        raise HTTPException(403, "Classroom role required")
    return [class_view(item) for item in query.all()]


@router.post("/classes", status_code=201)
def create_class(data: ClassCreate, user: User = Depends(teacher), db: Session = Depends(get_db)):
    code = secrets.token_urlsafe(32)
    item = Classroom(name=data.name, teacher_id=user.id, invite_hash=invite_hash(code))
    db.add(item)
    db.commit()
    return {**class_view(item), "invite": code}


@router.patch("/classes/{class_id}")
def manage_class(class_id: str, data: ClassUpdate, user: User = Depends(teacher), db: Session = Depends(get_db)):
    item = owned(db, class_id, user)
    item.name, item.archived = data.name, data.archived
    db.commit()
    return class_view(item)


@router.post("/classes/{class_id}/invite")
def rotate_invite(class_id: str, user: User = Depends(teacher), db: Session = Depends(get_db)):
    item = owned(db, class_id, user, active=True)
    code = secrets.token_urlsafe(32)
    item.invite_hash = invite_hash(code)
    db.commit()
    return {"invite": code}


@router.post("/join")
def join(data: Join, user: User = Depends(student), db: Session = Depends(get_db)):
    item = db.query(Classroom).filter_by(invite_hash=invite_hash(data.invite), archived=False).first()
    if not item:
        raise HTTPException(404, "Invitation not found")
    if not db.get(Enrollment, (item.id, user.id)):
        db.add(Enrollment(classroom_id=item.id, student_id=user.id))
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            if not db.get(Enrollment, (item.id, user.id)):
                raise
    return class_view(item)


@router.get("/classes/{class_id}/students")
def roster(class_id: str, user: User = Depends(teacher), db: Session = Depends(get_db)):
    owned(db, class_id, user)
    return [{"id": u.id, "name": u.name} for u in db.query(User).join(
        Enrollment, Enrollment.student_id == User.id).filter(Enrollment.classroom_id == class_id).all()]


@router.delete("/classes/{class_id}/students/{student_id}")
def remove_student(class_id: str, student_id: int, user: User = Depends(teacher), db: Session = Depends(get_db)):
    owned(db, class_id, user)
    item = db.get(Enrollment, (class_id, student_id))
    if not item:
        raise HTTPException(404, "Enrollment not found")
    db.delete(item)
    db.commit()
    return {"removed": True}


@router.post("/classes/{class_id}/assignments", status_code=201)
def create_assignment(class_id: str, data: AssignmentCreate, user: User = Depends(teacher), db: Session = Depends(get_db)):
    owned(db, class_id, user, active=True)
    item = Assignment(classroom_id=class_id, **data.model_dump(exclude={"original_content_confirmed"}))
    db.add(item)
    db.commit()
    return assignment_view(item)


@router.get("/classes/{class_id}/assignments")
def assignments(class_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    accessible(db, class_id, user)
    return [assignment_view(a, show_questions=role_name(user) == "TEACHER")
            for a in db.query(Assignment).filter_by(classroom_id=class_id).all()]


@router.post("/assignments/{assignment_id}/start")
def start(assignment_id: str, user: User = Depends(student), db: Session = Depends(get_db)):
    assignment = assignment_access(db, assignment_id, user)
    if db.get(Classroom, assignment.classroom_id).archived:
        raise HTTPException(409, "Classroom is archived")
    item = db.query(ExamAttempt).filter_by(assignment_id=assignment_id, student_id=user.id).first()
    if not item:
        item = ExamAttempt(assignment_id=assignment_id, student_id=user.id,
                           deadline=now() + timedelta(minutes=assignment.duration_minutes))
        db.add(item)
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            item = db.query(ExamAttempt).filter_by(assignment_id=assignment_id, student_id=user.id).one()
    return {**attempt_view(item, assignment), "questions": public_questions(assignment)}


@router.post("/attempts/{attempt_id}/submit")
def submit(attempt_id: str, data: Submission, user: User = Depends(student), db: Session = Depends(get_db)):
    item = db.get(ExamAttempt, attempt_id)
    if not item or item.student_id != user.id:
        raise HTTPException(404, "Attempt not found")
    assignment = assignment_access(db, item.assignment_id, user)
    if set(data.answers) != {str(i) for i in range(1, len(assignment.questions) + 1)}:
        raise HTTPException(422, "Submit exactly one answer for every question")
    if item.submitted_at:
        if item.answers != data.answers:
            raise HTTPException(409, "Attempt already submitted")
        return attempt_view(item, assignment)
    timestamp = now()
    score = sum(numeric(data.answers[str(i)]) == numeric(q["answer"])
                for i, q in enumerate(assignment.questions, 1))
    # Conditional update makes the first submission final, including concurrent requests.
    changed = db.execute(update(ExamAttempt).where(
        ExamAttempt.id == item.id, ExamAttempt.submitted_at.is_(None),
        ExamAttempt.deadline >= timestamp,
    ).values(answers=data.answers, score=score, submitted_at=timestamp),
        execution_options={"synchronize_session": False}).rowcount
    db.commit()
    db.refresh(item)
    if not changed:
        if item.submitted_at and item.answers == data.answers:
            return attempt_view(item, assignment)
        raise HTTPException(409, "Attempt expired or already submitted")
    return attempt_view(item, assignment)


@router.get("/classes/{class_id}/results")
def results(class_id: str, user: User = Depends(teacher), db: Session = Depends(get_db)):
    owned(db, class_id, user)
    rows = db.query(ExamAttempt, Assignment, User).join(
        Assignment, Assignment.id == ExamAttempt.assignment_id).join(
        User, User.id == ExamAttempt.student_id).filter(Assignment.classroom_id == class_id).all()
    return [{**attempt_view(a, task), "student_name": u.name} for a, task, u in rows]


@router.get("/progress")
def progress(user: User = Depends(student), db: Session = Depends(get_db)):
    rows = db.query(ExamAttempt, Assignment).join(Assignment).filter(ExamAttempt.student_id == user.id).all()
    return {"attempts": [attempt_view(a, task) for a, task in rows],
            "completed": sum(a.submitted_at is not None for a, _ in rows),
            "earned": sum(a.score or 0 for a, _ in rows),
            "possible": sum(len(task.questions) for a, task in rows if a.submitted_at)}


@router.post("/books", status_code=201)
def add_book(data: BookCreate, user: User = Depends(teacher), db: Session = Depends(get_db)):
    if data.license in {"permission_documented", "open_license"} and not data.rights_reference:
        raise HTTPException(422, "Documented rights require an evidence reference")
    item = ExternalBook(teacher_id=user.id, metadata_record=data.model_dump())
    db.add(item)
    db.commit()
    return {"id": item.id, **item.metadata_record, "content_import_enabled": False}


@router.get("/books")
def books(user: User = Depends(teacher), db: Session = Depends(get_db)):
    return [{"id": b.id, **b.metadata_record, "content_import_enabled": False}
            for b in db.query(ExternalBook).filter_by(teacher_id=user.id).all()]
