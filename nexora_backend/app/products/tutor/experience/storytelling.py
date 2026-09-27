from dataclasses import dataclass


@dataclass
class TeachingNarrative:

    style: str
    structure: str
    opening: str


class StorytellingEngine:

    def create(
        self,
        interaction_action: str,
        explanation_mode: str,
    ) -> TeachingNarrative:

        if interaction_action == "explain":
            return TeachingNarrative(
                style="guided_story",
                structure="simple_to_complex",
                opening="Let's build this idea step by step.",
            )

        if interaction_action == "challenge":
            return TeachingNarrative(
                style="expert_reasoning",
                structure="problem_to_solution",
                opening="Let's explore a deeper challenge.",
            )

        if interaction_action == "practice":
            return TeachingNarrative(
                style="interactive_learning",
                structure="example_and_feedback",
                opening="Let's practice this together.",
            )

        return TeachingNarrative(
            style="adaptive_conversation",
            structure="discover_student_need",
            opening="Let's find the best way to understand this.",
        )
