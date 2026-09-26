from dataclasses import dataclass, field


@dataclass
class LearningPlan:
    priority_topics: list[str] = field(default_factory=list)
    daily_steps: list[str] = field(default_factory=list)


class LearningPathEngine:

    def build(
        self,
        weaknesses: list[str],
        recommended_topics: list[str],
    ) -> LearningPlan:

        topics = list(
            dict.fromkeys(
                weaknesses + recommended_topics
            )
        )

        steps = []

        for topic in topics:
            steps.append(
                f"Study foundation and practice: {topic}"
            )

        return LearningPlan(
            priority_topics=topics,
            daily_steps=steps,
        )
