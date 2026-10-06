from .context import ContextAssembler
from .decision import DecisionEngine


class NexoraIntelligencePipeline:

    def __init__(self):

        self.context_builder = (
            ContextAssembler()
        )

        self.decision_engine = (
            DecisionEngine()
        )


    def run(
        self,
        student_id: int,
        skill: str,
        cognitive_result: dict,
        experience_result: dict,
        confidence: float = 0.0,
    ):

        context = self.context_builder.build(
            student_id=student_id,
            skill=skill,
            cognitive_result=cognitive_result,
            experience_result=experience_result,
            confidence=confidence,
        )


        decision = self.decision_engine.decide(
            context
        )


        return {

            "context": {
                "student_id": context.student_id,
                "skill": context.skill,
                "learning_state": context.learning_state,
                "emotion": context.emotion,
                "teaching_style": context.teaching_style,
            },


            "decision": {
                "action": decision.action,
                "response_mode": decision.response_mode,
                "priority": decision.priority,
                "reason": decision.reason,
            },
        }
