from .actions import XP_ACTIONS


class NexoraXPEngine:


    def calculate(
        self,
        action: str,
    ):

        xp_action = XP_ACTIONS.get(
            action
        )


        if not xp_action:
            return {
                "action": action,
                "xp": 0,
                "status": "unknown_action",
            }


        return {

            "action": xp_action.name,

            "xp": xp_action.points,

            "status": "awarded",

        }
