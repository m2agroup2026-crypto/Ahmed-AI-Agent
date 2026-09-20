AI_ACTION_COSTS = {

    "GENERAL_QUERY": 0,

    "VIEW_USERS": 1,

    "VIEW_DASHBOARD": 1,

    "CHECK_SYSTEM_STATUS": 1,

    "REPORT_GENERATION": 10,

}



def get_action_cost(action: str):

    return AI_ACTION_COSTS.get(
        action,
        0
    )
