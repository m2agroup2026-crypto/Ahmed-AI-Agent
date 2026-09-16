class TaskCollaborator:
    """
    Coordinates multiple Ahmed AI agents working together.
    """


    def __init__(self, agent_manager, router):

        self.agent_manager = agent_manager
        self.router = router



    def assign_task(self, task):

        decision = self.router.route(task)

        return {
            "task": task,
            "assigned_agent": decision["agent"],
            "score": decision["score"],
            "skills_matched": decision["skills_matched"]
        }



    def create_team_plan(self, tasks):

        plan = []

        for task in tasks:

            plan.append(
                self.assign_task(task)
            )

        return plan



    def collaborate(self, tasks):

        team_plan = self.create_team_plan(tasks)

        return {
            "team_size": len(
                set(
                    item["assigned_agent"]
                    for item in team_plan
                    if item["assigned_agent"]
                )
            ),
            "tasks": team_plan
        }
