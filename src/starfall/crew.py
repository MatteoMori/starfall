from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from typing import List

# Import web search tools
from crewai_tools import BraveSearchTool, ScrapeWebsiteTool

# Import your tool so CrewAI can register it
from starfall.tools.k8s_scanner import ScanK8sCluster


# Initialize tools
brave_search_tool = BraveSearchTool(
    #search_query="Kubeentes version: 1.32", # TODO: This will need to come from an Agent output
    #country="UK",
    n_results=5,
)

scrape_website_tool = ScrapeWebsiteTool()

@CrewBase
class Starfall():
    """Starfall crew"""

    agents: List[BaseAgent]
    tasks: List[Task]

    @agent
    def platform_enginner(self) -> Agent:
        return Agent(
            config=self.agents_config['platform_enginner'],  # type: ignore[index]
            verbose=True,
            tools=[ScanK8sCluster()]
        )

    @agent
    def technical_web_searcher(self) -> Agent:
        return Agent(
            config=self.agents_config['technical_web_searcher'],
            verbose=True,
            tools=[brave_search_tool, scrape_website_tool]
        )

    @task
    def research_task(self) -> Task:
        return Task(
            config=self.tasks_config['research_task'],  # type: ignore[index]
            output_file='report.md'
        )

    @task
    def technical_web_search_task(self) -> Task:
        return Task(
            config=self.tasks_config['technical_web_search_task'],  # type: ignore[index]
            output_file='report2.md'
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )
