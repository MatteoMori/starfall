from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from typing import List

# Import Off the shelf tools
from crewai_tools import BraveSearchTool, ScrapeWebsiteTool

# Import Custom tools
from starfall.tools.k8s_scanner import ScanK8sCluster

# Import Pydantic models
from starfall.pydantic_models import K8sClusterScanResult # Used for K8s Scanner Agent output


# Initialize Web search tool
brave_search_tool = BraveSearchTool(
    n_results=10,
)

# Initialize Web scrape tool
scrape_website_tool = ScrapeWebsiteTool()



@CrewBase
class Starfall():
    """Starfall crew"""

    agents: List[BaseAgent]
    tasks: List[Task]

    @agent
    def platform_engineer(self) -> Agent:
        return Agent(
            config=self.agents_config['platform_engineer'],  # type: ignore[index]
            verbose=True,
            tools=[ScanK8sCluster()]
        )

    @agent
    def latest_version_discovery_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['latest_version_discovery_agent'],
            verbose=True,
            tools=[brave_search_tool, scrape_website_tool]
        )

    # @agent
    # def technical_web_searcher(self) -> Agent:
    #     return Agent(
    #         config=self.agents_config['technical_web_searcher'],
    #         verbose=True,
    #         tools=[brave_search_tool, scrape_website_tool]
    #     )

    @task
    def k8s_cluster_scanner(self) -> Task:
        return Task(
            config=self.tasks_config['k8s_cluster_scanner'],  # type: ignore[index]
            output_file='outputs/k8s_scanner_report_current.md',
            output_pydantic=K8sClusterScanResult
        )

    @task
    def latest_version_discovery_task(self) -> Task:
        return Task(
            config=self.tasks_config['latest_version_discovery_task'],  # type: ignore[index]
            output_pydantic=K8sClusterScanResult,
            output_file='outputs/k8s_scanner_report_full.md',
            #context=[self.k8s_cluster_scanner]
        )

    # @task
    # def technical_web_search_task(self) -> Task:
    #     return Task(
    #         config=self.tasks_config['technical_web_search_task'],  # type: ignore[index]
    #         output_file='report2.md'
    #     )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )
