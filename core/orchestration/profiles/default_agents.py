from core.orchestration.agent_registry import AgentProfile


def get_default_agents():

    return [

        AgentProfile(
            name="software_engineer",
            role="Software Development Specialist",
            skills=[
                "backend",
                "frontend",
                "mobile",
                "architecture",
                "testing"
            ],
            tools=[
                "project_scanner",
                "code_analyzer"
            ]
        ),


        AgentProfile(
            name="creative_director",
            role="Creative Design and Visual Production Specialist",
            skills=[
                "branding",
                "graphic_design",
                "video_production",
                "3d_design",
                "storytelling"
            ],
            tools=[
                "image_analyzer",
                "prompt_engine",
                "design_reviewer"
            ]
        ),


        AgentProfile(
            name="research_agent",
            role="Research and Knowledge Specialist",
            skills=[
                "web_research",
                "documentation",
                "technology_analysis",
                "knowledge_validation"
            ],
            tools=[
                "web_search",
                "documentation_reader"
            ]
        ),


        AgentProfile(
            name="smart_systems_engineer",
            role="Smart Systems and IoT Specialist",
            skills=[
                "iot",
                "automation",
                "industrial_systems",
                "hardware_integration"
            ],
            tools=[
                "system_analyzer",
                "device_connector"
            ]
        ),


        AgentProfile(
            name="quality_engineer",
            role="Quality and Security Specialist",
            skills=[
                "testing",
                "security",
                "performance_analysis",
                "quality_review"
            ],
            tools=[
                "test_runner",
                "security_scanner"
            ]
        )
    ]
