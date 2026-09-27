from dataclasses import dataclass


@dataclass
class MasteryLevel:

    name: str

    minimum_score: int

    unlocks: list[str]


LEVELS = [

    MasteryLevel(
        name="explorer",
        minimum_score=0,
        unlocks=[
            "basic_tutor",
        ],
    ),


    MasteryLevel(
        name="learner",
        minimum_score=40,
        unlocks=[
            "smart_notes",
            "ai_summaries",
        ],
    ),


    MasteryLevel(
        name="advanced",
        minimum_score=65,
        unlocks=[
            "project_assistant",
            "presentation_creator",
        ],
    ),


    MasteryLevel(
        name="creator",
        minimum_score=85,
        unlocks=[
            "image_studio",
            "video_studio",
        ],
    ),


    MasteryLevel(
        name="genius",
        minimum_score=95,
        unlocks=[
            "research_mode",
            "innovation_challenges",
        ],
    ),
]


def get_level(
    score: int,
):

    current = LEVELS[0]

    for level in LEVELS:

        if score >= level.minimum_score:
            current = level

    return current
