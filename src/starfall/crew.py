from crewai import Agent, Crew, Process, Task
from crewai_tools import BraveSearchTool, ScrapeWebsiteTool

# Import Custom tools
from starfall.tools.k8s_scanner import ScanK8sCluster

# Define tools once
brave_search_tool = BraveSearchTool(n_results=6)
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
    latest_version: None
    latest_version_info_url: None
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
        - latest_version: None
        - latest_version_info_url: None
    - labels: Dictionary of deployment labels""",
        agent=platform_engineer,
        output_file='outputs/initial_k8s_scanner_report.json',
    )

    return Crew(
        agents=[platform_engineer],
        tasks=[k8s_scanner_task],
        process=Process.sequential,
        verbose=True,
    )

# --- VersionDiscovery Crew ---
def create_version_discovery_crew() -> Crew:
    """
    Creates a hierarchical crew for discovering the latest versions.
    The manager agent is responsible for delegating the single task.
    """
    manager_agent = Agent(
        role='Software Release Version Manager',
        goal="""As the ultimate delegator, coordinate and break down tasks to the 'Software Release Intelligence Specialist' to update a JSON report. Your sole purpose is to split the work and send it piece by piece.""",
        backstory="""You are the process orchestrator for software release intelligence. Your reputation is built on your ability to break down complex tasks and delegate them one at a time. You receive a cluster scan JSON report, identify each component, and delegate each specific latest release lookup to your coworker, the 'Software Release Intelligence Specialist'. You are FORBIDDEN from performing any research yourself. Your ONLY job is to delegate tasks one-by-one and then meticulously combine their results into a comprehensive, fully-updated report.""",
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

    # The manager's task is a strict, multi-step process with an explicit format example.
    manager_task = Task(
        description="""You have been provided with a JSON string representing a Kubernetes cluster scan report: {k8s_data}.
Your primary task is to orchestrate the discovery of the latest stable versions for each item in the report.

**Delegation Process - Follow these steps PRECISELY:**
1.  **First, parse the entire JSON string `{k8s_data}` into a structured object.**
2.  **Delegate the Control Plane lookup:** Create a **single** delegation task for the `kubernetes_control_plane` object. This task must be sent to your coworker. The value for the `coworker` key must be **'software release intelligence specialist'** (all lowercase).
    * **Step 2.1:** The parsed JSON object for the `kubernetes_control_plane` must be serialized back into a JSON string before being passed to the tool's `context` argument.
    * The 'task' for the coworker must contain the following instructions: 'Search ONLY the official vendor website or official GitHub repository releases page for the latest stable (non-pre-release, non-RC) version of the underlying software. **Do NOT use DockerHub, third-party registries, or unofficial sources. Do NOT perform upgrade analysis or summarize release notes. ALWAYS return back the same JSON object you are given. Your ONLY responsibility is to update the 'latest_version' and 'latest_version_info_url' fields for this item, based on official sources.**'
    * The `expected_output` for the coworker's task is: 'The output must match the input JSON structure, with the addition or update of: - latest_version: <Latest available stable release version string> - latest_version_info_url: <URL to official release notes or version listing> All other fields must be preserved as in the input JSON.'
    * The input to this tool must be a single, flat JSON object. It is absolutely critical that the input is NOT a list of objects.
    * **The input must look EXACTLY like this:**
        `{ "task": "...", "context": "...", "coworker": "software release intelligence specialist" }`
    * The `context` key must contain the JSON object for the `kubernetes_control_plane`.

3.  **Delegate EACH App lookup Individually:** After delegating the control plane, you will iterate through the `apps` array. For EACH app object you find in the array, you will perform a **new, separate delegation step**.
    * For each delegation, you must again create a **single** flat JSON object as the tool input, using the same format as above.
    * The 'task' for the coworker must contain the following instructions: 'Search ONLY the official vendor website or official GitHub repository releases page for the latest stable (non-pre-release, non-RC) version of the underlying software. **Do NOT use DockerHub, third-party registries, or unofficial sources. Do NOT perform upgrade analysis or summarize release notes. ALWAYS return back the same JSON object you are given. Your ONLY responsibility is to update the 'latest_version' and 'latest_version_info_url' fields for this item, based on official sources.**'
    * The `expected_output` for the coworker's task is: 'The output must match the input JSON structure, with the addition or update of: - latest_version: <Latest available stable release version string> - latest_version_info_url: <URL to official release notes or version listing> All other fields must be preserved as in the input JSON.'
    * The `context` key must contain the JSON object for the specific app you are delegating.
    * The `coworker` key must be **'software release intelligence specialist'** (all lowercase).
    * **Do NOT** bundle multiple delegations into a single list.

4.  **Assemble the Final Report:** Once you have received the output for **every single** delegation (the control plane and all apps), you must merge the updated JSON snippets back into a single, complete JSON report. Your final answer must be this complete report.

You MUST delegate each lookup as a separate, single-item task. Your output must be a single, complete JSON object.
""",
        expected_output="""The output must match the input JSON structure, with the addition or update of:
  - latest_version: <Latest available stable release version string>
  - latest_version_info_url: <URL to official release notes or version listing>
All other fields must be preserved as in the input.""",
        output_file='outputs/final_k8s_scanner_report.json',
    )

    return Crew(
        agents=[coworker_agent],
        tasks=[manager_task],
        process=Process.hierarchical,
        manager_agent=manager_agent,
        verbose=True,
    )