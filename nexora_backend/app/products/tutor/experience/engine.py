from .emotion import EmotionEngine
from .interaction import InteractionEngine
from .storytelling import StorytellingEngine


class NexoraExperienceEngine:

    def __init__(self):
        self.emotion_engine = EmotionEngine()
        self.interaction_engine = InteractionEngine()
        self.storytelling_engine = StorytellingEngine()


    def create_experience(
        self,
        success: bool,
        confidence: float,
    ):

        emotion = self.emotion_engine.analyze(
            success,
            confidence,
        )


        interaction = self.interaction_engine.decide(
            emotion.emotion,
            emotion.recommended_style,
        )


        narrative = self.storytelling_engine.create(
            interaction.action,
            interaction.explanation_mode,
        )


        return {
            "emotion": {
                "state": emotion.emotion,
                "intensity": emotion.intensity,
                "style": emotion.recommended_style,
            },

            "interaction": {
                "action": interaction.action,
                "mode": interaction.explanation_mode,
                "strategy": interaction.engagement_strategy,
            },

            "narrative": {
                "style": narrative.style,
                "structure": narrative.structure,
                "opening": narrative.opening,
            },
        }
