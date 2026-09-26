from dataclasses import dataclass, field


@dataclass
class DiagnosticResult:
    strengths: list[str] = field(default_factory=list)
    weaknesses: list[str] = field(default_factory=list)
    recommended_topics: list[str] = field(default_factory=list)


class DiagnosisEngine:

    def analyze(self, answers: list[dict]) -> DiagnosticResult:

        strengths = []
        weaknesses = []
        topics = []

        for answer in answers:
            skill = answer.get("skill")
            correct = answer.get("correct", False)

            if correct:
                strengths.append(skill)
            else:
                weaknesses.append(skill)
                topics.append(skill)

        return DiagnosticResult(
            strengths=list(set(strengths)),
            weaknesses=list(set(weaknesses)),
            recommended_topics=list(set(topics)),
        )
