class AgentRouter:
    """
    Routes user tasks to the most suitable Ahmed AI agent.
    """


    def __init__(self, agent_registry):
        self.registry = agent_registry


    def analyze_task(self, task):

        task_lower = task.lower()

        required_skills = []


        if any(word in task_lower for word in [
            "code",
            "software",
            "application",
            "backend",
            "frontend",
            "api",
            "website"
        ]):
            required_skills.extend([
                "backend",
                "frontend",
                "architecture"
            ])


        if any(word in task_lower for word in [
            "design",
            "video",
            "branding",
            "advertisement",
            "creative"
        ]):
            required_skills.extend([
                "branding",
                "video_production",
                "graphic_design"
            ])


        if any(word in task_lower for word in [
            "research",
            "compare",
            "documentation",
            "technology"
        ]):
            required_skills.extend([
                "web_research",
                "technology_analysis"
            ])


        if any(word in task_lower for word in [
            "iot",
            "factory",
            "automation",
            "sensor",
            "smart"
        ]):
            required_skills.extend([
                "iot",
                "automation",
                "hardware_integration"
            ])


        return required_skills



    def route(self, task):

        required_skills = self.analyze_task(task)

        best_agent = None
        best_score = 0


        for agent_name in self.registry.list_agents():

            agent = self.registry.get(agent_name)

            score = len(
                set(required_skills)
                &
                set(agent.skills)
            )


            if score > best_score:
                best_score = score
                best_agent = agent


        if best_agent:

            return {
                "agent": best_agent.name,
                "score": best_score,
                "skills_matched": required_skills
            }


        return {
            "agent": None,
            "score": 0,
            "skills_matched": required_skills
        }
