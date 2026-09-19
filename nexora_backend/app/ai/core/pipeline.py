from app.ai.intents.detector import detect_intent
from app.ai.assistant.security import authorize_ai_action
from app.ai.decision.engine import DecisionEngine
from app.ai.memory.events import EventLogger, AIEvent


class AgentPipeline:


    def __init__(self):

        self.decision_engine = DecisionEngine()

        self.event_logger = EventLogger()


    def run(
        self,
        state,
        db
    ):

        intent_result = detect_intent(
            state.input_text
        )


        state.intent = intent_result["intent"]

        state.permission = (
            intent_result["definition"]["permission"]
        )


        authorization = authorize_ai_action(
            db,
            state.user_id,
            state.intent
        )


        decision = self.decision_engine.evaluate(
            authorization["allowed"],
            authorization["permission"]
        )


        self.event_logger.log(
            AIEvent(
                "AI_DECISION",
                state.user_id,
                state.intent,
                decision.status
            )
        )


        state.status = decision.status


        return {
            "state": state,
            "decision": decision,
            "events": self.event_logger.all()
        }
