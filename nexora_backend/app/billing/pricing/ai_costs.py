AI_COSTS = {

    "GENERAL_QUERY": 1,

    "REPORT_GENERATION": 10,

    "ANALYTICS": 25,

    "EXPORT": 5,

}


def get_ai_cost(action):

    return AI_COSTS.get(
        action,
        1
    )
