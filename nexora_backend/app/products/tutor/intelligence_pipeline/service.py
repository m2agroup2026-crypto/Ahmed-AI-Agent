from .pipeline import NexoraIntelligencePipeline


class NexoraIntelligenceService:

    def __init__(self):

        self.pipeline = (
            NexoraIntelligencePipeline()
        )


    def execute(

        self,

        student_id: int,

        skill: str,

        cognitive_result: dict,

        experience_result: dict,

        confidence: float = 0.0,

    ):

        return self.pipeline.run(

            student_id=student_id,

            skill=skill,

            cognitive_result=cognitive_result,

            experience_result=experience_result,

            confidence=confidence,

        )


intelligence_service = NexoraIntelligenceService()
