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


# --- Sequential ReleaseNotesDiscovery Crew ---
def create_sequential_release_notes_discovery_crew() -> Crew:
    """
    Creates a sequential crew for Identifying release notes from the web and build a report.
    """
    release_hunter = Agent(
        role='Software Release Feature Investigator',
        goal="""Thoroughly analyze the release notes and documentation for a specified Tool or Platform version, 
        identifying and extracting the most valuable new features and enhancements. 
        Clearly determine the intended audience and impact of each feature, distinguishing between developer/consumer-facing improvements, platform engineer/maintainer 
        enhancements, and strategic changes relevant to senior stakeholders or heads of engineering.""",
        
        backstory="""You are a highly skilled analyst specializing in software release intelligence. Your expertise lies in 
        interpreting official release notes, changelogs, and product documentation to surface the most important advancements 
        in new versions of cloud-native tools and platforms. You understand the technical and business context of 
        infrastructure upgrades, and are adept at assessing which features will benefit developers and application teams, 
        which will improve platform operations and reliability for maintainers, and which will drive strategic outcomes 
        for senior leadership. Your output is a concise, audience-segmented summary that enables teams to plan upgrades, 
        communicate business value, and reduce risk.""",
        tools=[brave_search_tool, scrape_website_tool],
        verbose=True,
    )


    risk_expert = Agent(
        role='Software Upgrade Risk and Breaking Change Analyst',
        goal="""Investigate and summarize all risks, breaking changes, and migration challenges that may arise when upgrading a Tool or Platform 
        from its current version to the latest available version. Clearly identify which risks and changes impact developers/consumers, 
        platform engineers/maintainers, or senior stakeholders, enabling comprehensive upgrade planning and communication.""",
        backstory="""You are an expert in software migration analysis and risk assessment. Your specialty is understanding upgrade paths for cloud-native tools 
        and platforms, with a focus on uncovering breaking changes, deprecated features, and unexpected behaviors that may affect system reliability, 
        developer experience, and strategic business outcomes. You scan official release notes, changelogs, migration guides, and community reports 
        to extract and categorize all risks and breaking changes, providing actionable insights for each audience: developers/consumers, platform engineers/maintainers, 
        and senior leadership. Your output is a structured, audience-segmented risk report that ensures every stakeholder is informed and prepared for a successful upgrade.""",
        tools=[brave_search_tool, scrape_website_tool],
        verbose=True,
    )



    new_features_task = Task(
        description="""
    You are provided with a JSON object describing a specific Tool or Application in a Kubernetes environment.
    The tool's information are:  {tool_info}
    The tool in question is: {tool_name}

    If the tool is Kubernetes itself, the input is in the below format:
    {'current_version': <string>, 'latest_version': <string>, 'latest_version_info_url': <url>, 'name': <string>, 'scanned_at': <ISO8601 UTC timestamp>}
    If it is an application, the input is in the below format:
    {'name': <string>, 'namespace': <string>, 'deployment': <string>, 'containers': [{'name': <string>, 'image': <string>, 'current_version': <string>, 'latest_version': <string>, 'latest_version_info_url': <url>}], 'labels': {...}}

    Your mission is to actively browse the internet, using ONLY official release notes, changelogs, or trusted vendor documentation, and identify the most valuable new features introduced in the 'latest_version' of {tool_name}.

    DO NOT use unofficial sources, not trustworthy blogs, forums, or DockerHub. Do not rely only on dry Changelogs as it will be hard to extrapolate useful information.

    If {tool_name} is Kubernetes, you can trust the content of https://kubernetes.io/blog
    If {tool_name} is Cilium, you can trust the content of the Isovalent's blog.

    Your input provides you with a starting point URL to browse (<latest_version_info_url>) but you DO NOT limit yourself to just that URL. You have to explore other official sources as needed.

    **Process - Follow These Steps Exactly:**
    1.  **Search for Release Highlights:** Go online and conduct a broad search using the tool name and version combined with terms like "new features," "release highlights," or "what's new." For example: "Kubernetes v1.33 new features" or "Cilium v1.33 release highlights."
    2.  **Select the Best Source:** Carefully review the search results and select the single most promising official URL (e.g., an official blog post or announcement) to scrape for detailed information.
    3.  **Synthesize Findings:** Systematically review the content of the selected URL to find all relevant new features.
    4.  **Extract and Categorize:** From the synthesized information, carefully extract the most important new features. For each feature, clearly determine who benefits most:
        - If the feature benefits developers/consumers, use the audience label: '👨‍💻 Devs'
        - If the feature benefits platform engineers/owners, use the audience label: '🛠️ Ops'
        - If a feature benefits both, use: '👨‍💻 Devs + 🛠️ Ops'
    4.  **Explain the 'Why':** For each feature, concisely explain WHY it matters for that audience (value, use case, impact).
    5.  **Organize your Output:** Format your answer as a Markdown table.

    ### 🌟 Highlights
    | Feature | Audience | Why It Matters |
    |---------|----------|----------------|
    <#highlights>
    | **<feature_name>** <feature_icon> | <audience> | <impact> |
    </highlights>

    - 'feature_icon' is an emoji that best represents the feature (e.g., 🚀, 🔒, ⚡️, 📅).
    - Use one row per feature.
    - Only include features newly introduced in the 'latest_version'.

    Your final answer MUST be a valid markdown table. Never include commentary outside the Markdown output.

    **Example Output Table:**
    ### 🌟 Highlights
    | Feature | Audience | Why It Matters |
    |---------|----------|----------------|
    | **Sidecar Containers GA** 🚀 | 👨‍💻 Devs + 🛠️ Ops | Developers can finally ship sidecars without ugly hacks → Operators gain predictable lifecycle mgmt. |
    | **CronJobs reach GA** 📅 | 🛠️ Ops | Reliable, production-ready scheduling → less pager noise for operators. |
    | **NetworkPolicy status field** 🔒 | 🛠️ Ops | Visibility on applied/failed policies → faster debugging & compliance. |
    | **Pod replacement speed improvements** ⚡ | 👨‍💻 Devs | Faster rollouts = happier developers waiting less on CI/CD pipelines. |
    """,
        expected_output="""
    A Markdown-formatted table listing the most important new features found in the official release notes for the specified tool or application version.

    The table must have these columns:
    | Feature | Audience | Why It Matters |

    Each row should contain:
    - Feature name and an emoji icon
    - Audience ('👨‍💻 Devs', '🛠️ Ops', or '👨‍💻 Devs + 🛠️ Ops')
    - Impact statement

    If no features are found, state "No major new features in this release."
    """,
        #output_file='outputs/new_features_report.md',
        agent=release_hunter,
        markdown=True,  # Enable automatic markdown formatting
    )

    return Crew(
        agents=[release_hunter],
        tasks=[new_features_task],
        process=Process.sequential,
        verbose=True,
    )