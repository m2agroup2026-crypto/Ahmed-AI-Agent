from app.ai.core.state import AgentState


def test_agent_state_creation():

    state = AgentState(
        1,
        "اعرض المستخدمين"
    )

    assert state.user_id == 1

    assert state.input_text == "اعرض المستخدمين"

    assert state.status == "initialized"
