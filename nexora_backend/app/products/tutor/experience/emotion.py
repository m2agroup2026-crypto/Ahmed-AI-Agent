from dataclasses import dataclass


@dataclass
class EmotionalState:

    emotion: str
    intensity: float
    recommended_style: str


class EmotionEngine:

    def analyze(
        self,
        success: bool,
        confidence: float,
    ) -> EmotionalState:

        if not success and confidence < 0.4:
            return EmotionalState(
                emotion="frustrated",
                intensity=0.8,
                recommended_style="supportive",
            )

        if success and confidence >= 0.85:
            return EmotionalState(
                emotion="confident",
                intensity=0.9,
                recommended_style="challenging",
            )

        if success:
            return EmotionalState(
                emotion="progressing",
                intensity=0.6,
                recommended_style="encouraging",
            )

        return EmotionalState(
            emotion="uncertain",
            intensity=0.5,
            recommended_style="adaptive",
        )
