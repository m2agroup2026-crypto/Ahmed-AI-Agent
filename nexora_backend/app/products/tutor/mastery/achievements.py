from dataclasses import dataclass


@dataclass
class Achievement:

    name: str

    description: str

    required_level: str



ACHIEVEMENTS = [

    Achievement(
        name="knowledge_explorer",
        description="Student shows consistent learning progress.",
        required_level="learner",
    ),


    Achievement(
        name="advanced_thinker",
        description="Student demonstrates strong problem solving skills.",
        required_level="advanced",
    ),


    Achievement(
        name="nexora_creator",
        description="Student unlocked creative AI capabilities.",
        required_level="creator",
    ),


    Achievement(
        name="innovation_master",
        description="Student reached the highest Nexora mastery level.",
        required_level="genius",
    ),

]



def get_achievements(
    level: str,
):

    unlocked = []

    level_order = [
        "explorer",
        "learner",
        "advanced",
        "creator",
        "genius",
    ]


    current_index = level_order.index(
        level
    )


    for achievement in ACHIEVEMENTS:

        required_index = level_order.index(
            achievement.required_level
        )


        if current_index >= required_index:

            unlocked.append(
                achievement.name
            )


    return unlocked
