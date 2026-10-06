from .achievements import get_achievements


class NexoraUnlockEngine:


    def unlock(

        self,

        student_id: int,

        level: str,

    ):


        achievements = get_achievements(
            level
        )


        features = []


        if level in [
            "learner",
            "advanced",
            "creator",
            "genius",
        ]:

            features.extend([
                "smart_notes",
                "ai_summaries",
            ])


        if level in [
            "advanced",
            "creator",
            "genius",
        ]:

            features.extend([
                "project_assistant",
                "presentation_creator",
            ])


        if level in [
            "creator",
            "genius",
        ]:

            features.extend([
                "image_studio",
                "video_studio",
            ])


        if level == "genius":

            features.extend([
                "research_mode",
                "innovation_challenges",
            ])


        return {

            "student_id": student_id,

            "level": level,

            "achievements": achievements,

            "features": features,

        }
