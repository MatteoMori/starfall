from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from typing import List

# Import your tool so CrewAI can register it
from starfall.tools.k8s_scanner import ScanK8sCluster

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

    # @agent
    # def reporting_analyst(self) -> Agent:
    #     return Agent(
    #         config=self.agents_config['reporting_analyst'],  # type: ignore[index]
    #         verbose=True
    #     )

    @task
    def research_task(self) -> Task:
        return Task(
            config=self.tasks_config['research_task'],  # type: ignore[index]
            output_file='report.md'
        )

    # @task
    # def reporting_task(self) -> Task:
    #     return Task(
    #         config=self.tasks_config['reporting_task'],  # type: ignore[index]
    #         output_file='report.md'
    #     )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )
