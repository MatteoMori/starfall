from crewai import Agent, Crew, Process, Task
from crewai_tools import BraveSearchTool, ScrapeWebsiteTool

# Import Custom tools
from starfall.tools.k8s_scanner import ScanK8sCluster

# Define tools once
brave_search_tool = BraveSearchTool(n_results=10)
scrape_website_tool = ScrapeWebsiteTool()

# --- K8sScan Crew ---
def create_k8s_scan_crew() -> Crew:
    """
    Creates a sequential crew for scanning a Kubernetes cluster.
    """
    platform_engineer = Agent(
        role='Senior Kubernetes Platform Engineer',
        goal="""Deliver a comprehensive, accurate scan of the Kubernetes cluster, identifying all namespaces 
        and deployments with the label "starfall.io/enabled=true", and reporting details such as deployment names, 
        namespaces, container images, image versions, and relevant labels for upgrade planning.""",
        backstory="""As a highly experienced Kubernetes platform engineer, you are responsible for ensuring the safety, reliability, 
        and scalability of infrastructure upgrades. You know that missing even a single versioned container image 
        or deployment label can lead to outages or security gaps. Your mission is to methodically inspect the cluster, 
        focusing only on resources marked for Starfall upgrades, and to produce a JSON structured report for downstream 
        automation and human review. You avoid assumptions and ignore resources not explicitly labeled for Starfall.""",
        tools=[ScanK8sCluster()],
        verbose=True,
    )

    k8s_scanner_task = Task(
        description="""Perform a meticulous scan of the Kubernetes cluster to identify all namespaces and deployments explicitly labeled with "starfall.io/enabled=true".
For each matching deployment, extract and report:
  - Namespace name
  - Deployment name
  - For every container: name, image, image tag, and current version
  - All deployment labels
Additionally, capture the Kubernetes cluster's current version and the timestamp of the scan.
The output must be a structured, machine-readable, JSON, report that enables downstream agents 
and humans to easily assess upgrade eligibility, plan actions, and track changes over time.
Exclude any deployments or namespaces that do not have the specified label.
Do not perform any upgrade or modification actions; your sole responsibility is to scan and report.""",
        expected_output="""A validated K8sClusterScanResult object with the following structure:
  kubernetes_control_plane:
    current_version: <Current Kubernetes control plane version string>
    latest_version: <Latest available Kubernetes version (to be filled by discovery task)>
    name: "Kubernetes"
    scanned_at: <ISO8601 UTC timestamp of scan>
  apps: List of deployments, each with:
    - name: <Deployment name>
    - namespace: <Namespace name>
    - deployment: <Deployment identifier>
    - containers: List of containers, each with:
        - name: <Container name>
        - image: <Full image path>
        - current_version: <Image tag or version>
    - labels: Dictionary of deployment labels""",
        agent=platform_engineer,
    )

    return Crew(
        agents=[platform_engineer],
        tasks=[k8s_scanner_task],
        process=Process.sequential,
        verbose=True,
    )

# --- VersionDiscovery Crew (Refactored for hierarchical process) ---
def create_version_discovery_crew() -> Crew:
    """
    Creates a hierarchical crew for discovering the latest versions.
    The manager agent is responsible for delegating the single task.
    """
    manager_agent = Agent(
        role='Software Release Version Manager',
        goal="""Coordinate and delegate tasks to specialized agents to update a JSON report with accurate, authoritative latest release information. Your ONLY job is to orchestrate the process.""",
        backstory="""You are the process orchestrator for software release intelligence. You receive a cluster scan JSON report, 
        break down the work, and delegate each specific latest release lookup to a trusted specialist. You are FORBIDDEN from performing any research yourself.
        Your ONLY job is to delegate tasks to your specialized coworker and then meticulously combine their results into a comprehensive, fully-updated report.""",
        verbose=True,
        allow_delegation=True,
    )
    
    coworker_agent = Agent(
        role='Software Release Intelligence Specialist',
        goal="""Accurately identify and provide the latest upstream release version and release information URL for a single software target, using only official sources.""",
        backstory="""You are a trusted authority in software release tracking. Organizations depend on your research to stay current, secure, and compliant. 
        You meticulously search official sources like GitHub and vendor sites to validate the most recent releases. You never speculate or rely on unofficial data.""",
        tools=[brave_search_tool, scrape_website_tool],
        verbose=True,
    )

    # This is the SINGLE task given to the hierarchical crew. The manager will handle it.
    manager_task = Task(
        description="""You have been provided with a JSON string representing a Kubernetes cluster scan report: {k8s_data}.
Your primary task is to orchestrate the discovery of the latest stable versions for each item in the report.

**Process:**
1.  First, parse the provided JSON string `{k8s_data}` into a structured object.
2.  Identify the 'kubernetes_control_plane' object and delegate a task to the 'Software Release Intelligence Specialist' to find its latest version. The input for this delegation must be ONLY the content of the 'kubernetes_control_plane' key.
3.  Next, iterate through the 'apps' array. For EACH application object within this array, delegate a task to the 'Software Release Intelligence Specialist' to find the latest versions of its containers. The input for this delegation must be ONLY the content of the specific application object.
4.  Once all delegation sub-tasks are complete and you have received the updated JSON snippets from the specialist, merge the results back into the original, full report.
5.  Return the final, complete, fully-updated JSON object.

You MUST delegate the work for each component individually. You are not to perform any search or data retrieval yourself.""",
        expected_output="""The complete, updated JSON report with the `latest_version` and `latest_version_info_url` fields populated for all components.""",
        agent=manager_agent,
    )
    
    # This is the task for the worker agent, which will be delegated by the manager.
    coworker_task = Task(
        description="""You receive an input JSON object representing a single Kubernetes cluster item (either the control plane, 
or a single application/container). Your task is to inspect ONLY this item and determine the latest available stable version and 
its official release information URL.
For the control plane:
  - Search ONLY the official Kubernetes releases page or site for the latest stable version.
  - Update 'latest_version' and 'latest_version_info_url' accordingly.
For applications/containers:
  - For the given container, search ONLY the official vendor website or official GitHub repository releases page for the latest stable (non-pre-release, non-RC) version of the underlying software.
  - Update the 'latest_version' and 'latest_version_info_url' fields in the input JSON accordingly.
Do NOT use DockerHub, third-party registries, or unofficial sources.
Do NOT perform upgrade analysis or summarize release notes.
Your ONLY responsibility is to update the 'latest_version' and 'latest_version_info_url' fields for this item, based on official sources.""",
        expected_output="""The output must match the input JSON structure, with the addition or update of:
  - latest_version: <Latest available stable release version string>
  - latest_version_info_url: <URL to official release notes or version listing>
All other fields must be preserved as in the input.""",
        agent=coworker_agent,
    )
    
    return Crew(
        agents=[coworker_agent],
        tasks=[manager_task, coworker_task],
        process=Process.hierarchical,
        manager_agent=manager_agent,
        verbose=True,
    )