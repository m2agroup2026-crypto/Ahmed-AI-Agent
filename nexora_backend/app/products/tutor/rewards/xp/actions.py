from dataclasses import dataclass


@dataclass
class XPAction:

    name: str

    points: int



XP_ACTIONS = {

    "question_solved": XPAction(
        name="question_solved",
        points=5,
    ),

    "hard_question_solved": XPAction(
        name="hard_question_solved",
        points=15,
    ),

    "lesson_completed": XPAction(
        name="lesson_completed",
        points=50,
    ),

    "streak_7_days": XPAction(
        name="streak_7_days",
        points=200,
    ),

    "project_completed": XPAction(
        name="project_completed",
        points=500,
    ),

}
