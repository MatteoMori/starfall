from crewai import Agent, Crew, Process, Task
from crewai_tools import BraveSearchTool, ScrapeWebsiteTool, FileReadTool

# Import Custom tools
from starfall.tools.k8s_scanner import ScanK8sCluster

# Define tools once
brave_search_tool = BraveSearchTool(n_results=6)
scrape_website_tool = ScrapeWebsiteTool()
file_read_tool = FileReadTool()



# --- K8sScan Crew ---
def k8s_scan_crew() -> Crew:
    """
    Creates a sequential crew for scanning a Kubernetes cluster.
    """
    platform_engineer = Agent(
        role='Senior Kubernetes Platform Engineer',
        goal="""Deliver a comprehensive, accurate scan of the Kubernetes cluster, identifying all namespaces 
        and deployments/daemonsets/ets with the label "starfall.io/enabled=true", and reporting details such as resource names, 
        namespaces, container images, image versions, and relevant labels for upgrade planning.""",
        backstory="""As a highly experienced Kubernetes platform engineer, you are responsible for ensuring the safety, reliability, 
        and scalability of infrastructure upgrades. You know that missing even a single versioned container image 
        or resource label can lead to outages or security gaps. Your mission is to methodically inspect the cluster, 
        focusing only on resources marked for Starfall upgrades, and to produce a JSON structured report for downstream 
        automation and human review. You avoid assumptions and ignore resources not explicitly labeled for Starfall.""",
        tools=[ScanK8sCluster()],
        verbose=True,
    )

    k8s_scanner_task = Task(
        description="""Perform a meticulous scan of the Kubernetes cluster to identify all namespaces and resource ( deployments/daemonsets/etc ) explicitly labeled with "starfall.io/enabled=true".
For each matching resource, extract and report:
  - Namespace name
  - Resource name
  - For every container: name, image, image tag, and current version
  - All resource labels
Additionally, capture the Kubernetes cluster's current version.
The output must be a structured, machine-readable, JSON, report that enables downstream agents
and humans to easily assess upgrade eligibility, plan actions, and track changes over time.
Exclude any resource or namespaces that do not have the specified label.
Do not perform any upgrade or modification actions; your sole responsibility is to scan and report.""",
        expected_output="""A validated K8sClusterScanResult object with the following structure:
  kubernetes_control_plane:
    current_version: <Current Kubernetes control plane version string>
    latest_version: None
    latest_version_info_url: None
    name: "Kubernetes"
  apps: List of resources, each with:
    - name: <Resource name>
    - namespace: <Namespace name>
    - kind: <Resource kind: Deployment, Daemonset, etc.>
    - containers: List of containers, each with:
        - name: <Container name>
        - image: <Full image path>
        - current_version: <Image tag or version>
        - latest_version: None
        - latest_version_info_url: None
    - labels: Dictionary of resource labels""",
        agent=platform_engineer,
        output_file='outputs/k8s-status/initial_k8s_scanner_report.json',
    )

    return Crew(
        agents=[platform_engineer],
        tasks=[k8s_scanner_task],
        process=Process.sequential,
        verbose=True,
    )

# --- VersionDiscovery Crew ---
def version_discovery_crew() -> Crew:
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
        You meticulously search official sources like GitHub and vendor sites to validate the most recent releases. You never speculate or rely on unofficial data.
        ALWAYS Use the BraveSearch tool with `search_query` set to a well-phrased query""",
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
        output_file='outputs/k8s-status/final_k8s_scanner_report.json',
    )

    return Crew(
        agents=[coworker_agent],
        tasks=[manager_task],
        process=Process.hierarchical,
        manager_agent=manager_agent,
        verbose=True,
    )


# --- Sequential ReleaseNotesDiscovery Crew ---
def sequential_report_generator_crew() -> Crew:
    """
    Creates a sequential crew for discovering release notes and producing a Markdown report.
    """

    # ===========================================
    # Define Agents
    # ===========================================
    release_analyst = Agent(
        role="Software Release Analyst",
        goal="""Identify and summarize the most important new features, fixes, and improvements 
        in the specified tool's latest release. Clearly explain why each matters and who benefits 
        (developers, operators, or both). Output strictly as a Markdown table.""",
        backstory="""
        You are `release_analyst`, an expert at analyzing official release notes for 
        Kubernetes and cloud-native tools. You specialize in separating signal from noise, 
        finding the features that truly matter, and framing them for the right audience:
        👨‍💻 Developers, 🛠️ Operators, or both.

        🔎 SOURCE PRIORITY:
          - Kubernetes: (1) kubernetes.io/blog release post, (2) kubernetes.io official notes, (3) GitHub release.
          - Other tools: (1) Vendor blog/site, (2) Official docs changelog, (3) GitHub/GitLab release.
          - Never use 3rd-party blogs, forums, or aggregators.

        ⚖️ RULES:
          - Short-circuit patch releases (x.y.Z with Z>0): return "No major new features in this release."
          - Focus on GA/Beta/Alpha capabilities, and major performance improvements.
          - Deduplicate overlaps, use concise titles.
          - Organize output as a Markdown table, no extra commentary.

        Use the BraveSearch tool with `search_query` set to a well-phrased query
        """,
        tools=[brave_search_tool, scrape_website_tool],
        verbose=True,
    )

    risk_expert = Agent(
        name="Risk Expert",
        role="Senior Platform Engineer Specialized in Risk Analysis",
        goal="""
        Identify potential risks, breaking changes, and critical deprecations in new software releases
        and provide a clean, concise risk assessment.
        """,
        backstory="""
        You are the 'Risk Expert,' a highly experienced and detail-oriented platform engineer.
        Your core task is to meticulously analyze software release notes for cloud-native tools,
        especially those running on Kubernetes.

        Your process is as follows:
        1.  **Search & Scrape**: Use the BraveSearch tool with `search_query` set to a well-phrased query to find and analyze the most authoritative release notes.
        2.  **Analyze**: Carefully identify all breaking changes, critical deprecations, and potential
            risks.
        3.  **Document**: For each risk, classify it with a severity level (low, medium, high),
            and a clear, short description of its impact.
        """,
        tools=[brave_search_tool, scrape_website_tool],
        verbose=True,
    )

    release_director = Agent(
        role="Software Release Director",
        goal="""
        Synthesize the feature highlights and risk assessments from your team into a cohesive,
        actionable recommendation for tool upgrades.
        """,
        backstory="""
        You are `release_director`, the main responsible for drafting final reports on tool upgrades.
        Your job is to receive structured reports from the `release_analyst` and `risk_expert`
        and use their findings to formulate a clear, high-level recommendation for management,
        developers, and operators. You must weigh the benefits (new features) against the risks
        (breaking changes) to provide a single, definitive action plan.

        Your recommendations should be concise and business-oriented, focusing on the "why"
        behind the decision and the specific benefits or risks for different stakeholders.
        You must always produce one of the following recommendations:
        - **Upgrade is strongly advised:** When there are significant new features with low to no risks.
        - **Upgrade with caution:** When there are notable features but also identified risks that require planning.
        - **Hold upgrade:** When the risks outweigh the benefits or there are no significant new features.
        """,
        verbose=True,
    )



    # ===========================================
    # Define Tasks
    # ===========================================
    release_notes_task = Task(
        name="release_notes_task",
        description="""
        You are provided with metadata about a tool running in a Kubernetes environment:
        {tool_name} - version {tool_latest_version}

        1. **Patch Release Check**:
           - If {tool_latest_version} is a patch release (e.g., x.y.Z where Z > 0), 
             immediately return a Markdown table with one row stating:
             "No major new features in this release."

        2. **Search**:
           - Use the BraveSearch tool with `search_query` set to find official release notes for {tool_name} {tool_latest_version}.
           - Query example: "{tool_name} v{tool_latest_version} release notes site:officialsite.com"
           - if you receive a "429 Client Error: Too Many Requests" error, sleep 1 sec and try again.

        3. **Scrape & Analyze**:
           - Scrape the most authoritative release notes page.
           - Extract only meaningful new features, fixes, or improvements.

        4. **Classify & Explain**:
           - For each change, assign the audience:
             👨‍💻 Devs, 🛠️ Ops, or 👨‍💻 Devs + 🛠️ Ops
           - Add a short "Why it matters" statement.
           - Include an emoji icon to represent the feature (🚀, 🔒, ⚡️, 📅).

        5. **Output**:
           Format strictly as a Markdown table:

        ### 🌟 Highlights
        | Feature | Audience | Why It Matters |
        |---------|----------|----------------|
        | **<feature_name>** <emoji> | <audience> | <impact> |

        Do NOT include commentary, prose, or code fences like ```.
        If no features are found, output one row stating:
        | No major new features in this release. | - | - |
        """,
        expected_output="""
        A Markdown table following the below template:

        ### 🌟 Highlights
        | Feature | Audience | Why It Matters |
        |---------|----------|----------------|
        | **<feature_name>** <emoji> | <audience> | <impact> |

        Rules:
        - Only include official features from the specified release.
        - Always include an emoji with each feature.
        - If no features are found, include a single row:
          | No major new features in this release. | - | - |
        - Do NOT include commentary, prose, or code fences like ```.
        """,
        agent=release_analyst,
        markdown=True,
    )


    upgrade_risks_task = Task(
        name="upgrade_risks_task",
        description="""
        Analyze the upgrade from version {tool_current_version} to {tool_latest_version} for {tool_name} and
        document all breaking changes and risks.
        """,
        expected_output="""
        A strict Markdown table of breaking changes and risks.
        
        ### ⚠️ Breaking Changes & Risks  
        | Change | Severity | Impact |
        |---|---|---|
        | **< risk_name >** <emoji> | <low|medium|high> | <impact_description> |

        Rules for output:
        - **MUST** be a single Markdown table, with no text before or after it.
        - **ABSOLUTELY NO** commentary, prose, or code fences (e.g., ```).
        - Title **MUST** be exactly "### ⚠️ Breaking Changes & Risks".
        - Headers **MUST** be exactly "Change", "Severity", and "Impact".
        - Each change **MUST** include an emoji (e.g., 🚀, 🔒, ⚡️, 📅) and be bolded.
        - If no risks are found, the table **MUST** contain only one single row:
        | No major risks are identified. | - | - |
        """,
        agent=risk_expert,
        markdown=True,
        verbose=True,
    )


    final_report_task = Task(
        name="final_report_task",
        description="""
        Based on the input received from the previous tasks, generate the final
        recommendation report as a single Markdown string.

        1. **Analyze Input**:
        - Review the features provided by the `release_analyst`.
        - Review the risks provided by the `risk_expert`.

        2. **Synthesize and Decide**:
        - Weigh the importance of new features against the severity of identified risks.
        - If there are significant features and low/no risks, generate a "strongly advised" recommendation.
        - If there are significant features but also medium/high risks, generate a "with caution" recommendation.
        - If risks outweigh benefits or there are no major features, generate a "hold upgrade" recommendation.

        3. **Format Output**:
        - The output MUST be a single, structured markdown block.
        - The heading MUST be `### ✅ Recommendation`.
        - The first line MUST be one of the exact phrases: **Upgrade is strongly advised.**, **Upgrade with caution.**, or **Hold upgrade.**
        - Use a bulleted list to summarize key takeaways for each audience: Developers, Operators, and Executives.
        - Do NOT include any commentary, prose, or code fences outside of the final markdown block.
        
        Example:
        ### ✅ Recommendation  
        **Upgrade is strongly advised.**
        - Developers → Huge productivity gains with Sidecars.  
        - Operators → More stability & observability.  
        - Executives → Faster delivery cycles with lower incident noise.  
        """,
        expected_output="""
        Rules for output:
        - **ABSOLUTELY NO** commentary, prose, or code fences (e.g., ```).
        """,
        agent=release_director,
        markdown=True,
        context=[upgrade_risks_task,release_notes_task],
    )



    return Crew(
        agents=[release_analyst, risk_expert, release_director],
        tasks=[release_notes_task, upgrade_risks_task, final_report_task],
        process=Process.sequential,
        verbose=True,
    )


# --- Final report summary Crew ---
def final_report_summary_crew() -> Crew:
    """
    Reads a report and summarizes the key findings for the Head of Engineering.
    """

    # ===========================================
    # Define Agents
    # ===========================================
    summary_generator = Agent(
        role="Director of Engineering",
        goal="""
        Read a technical report and distill it into a high-level executive summary,
        highlighting key business risks, rewards, and strategic priorities for senior leadership.
        """,
        backstory="""
        You are a `Director of Engineering` with a keen eye for business impact.
        Your main job is to take detailed technical reports and translate them into
        clear, concise, and actionable summaries for a C-suite or senior management audience.
        You cut through the noise, focusing on what matters most: strategic opportunities,
        potential risks, and the overall value proposition of technical changes.
        
        You **MUST NOT** invent any information, perform online lookups, or express doubt.
        Your entire output must be based **SOLEY** on the information inferred from the file
        provided to you.
        
        Your reports are not just summaries—they are a guide for business decisions.
        """,
        tools=[file_read_tool],
        verbose=True,
    )

    # ===========================================
    # Define Tasks
    # ===========================================
    generate_executive_summary_task = Task(
        name="Generate Executive Summary",
        description="""
        Read the contents of the file located at {file_path}. The file contains detailed technical
        information about tool upgrades. Your task is to extract the most critical
        business-focused insights and present them in a concise report.

        1. **Analyze for Business Impact**: Identify and categorize all key information from the file
        based on its significance to the business:
        - **Rewards (Features):** What are the most significant new features? How do they
            translate into developer productivity, operational stability, or business value?
        - **Risks (Breaking Changes):** What are the highest-severity risks or breaking changes?
            What is their potential impact on production systems or developer workflows?
        - **Priority:** Based on the balance of rewards vs. risks, determine the strategic priority
            of the upgrade (e.g., High, Medium, Low).
        
        2. **Synthesize & Format**: Synthesize your findings into the exact markdown report format
        provided below. Your goal is to fill in the table and key takeaways with the
        most critical information from the file, without any extra text or commentary.
        
        
        """,
        expected_output="""
        # 📰 Starfall Upgrade Report 
        
        > **At a glance:** Stay ahead of the curve with Starfall. Below is your **executive snapshot**, followed by detailed **feature spreads** for each tool.  
        
        ---
        
        ## 🚨 Executive Summary  
        
        | Tool | Current → Latest | 🚀 Reward | ⚠️ Risk | 🏷️ Priority |
        |------|-----------------|-----------|---------|-------------|
        | **< Tool Name >** | < Current → Latest > | < Rating: ⭐⭐⭐ > | < Rating: ⚠️ Medium > | < Rating: 🔥 High > |

        **Key Takeaway:** - **< Tool Name >** introduces long-awaited **< Key Feature >** 🎉 (< Impact >).  
        - **< Tool Name >** brings **< Key Feature >** ⚡ (< Impact >).  
        - **Risks** exist (< brief description of risks >), but Starfall flags them for you.  
        

        **Rules for Output:**
        - The output MUST be a single, structured markdown string.
        - It must follow the exact format, headings, and table structure from the example.
        - You MUST replace the placeholder data with the actual, extracted data.
        - It is MISSION CRITICAL that you DO NOT include any commentary, prose, or code fences ( like ```) outside of the formatted report.
        """,
        agent=summary_generator,
        markdown=True,
        output_file='outputs/platform-upgrade.md',
    )


    return Crew(
        agents=[summary_generator],
        tasks=[generate_executive_summary_task],
        process=Process.sequential,
        verbose=True,
    )