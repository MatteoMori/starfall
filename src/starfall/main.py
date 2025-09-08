#!/usr/bin/env python
from datetime import datetime
import sys
import warnings
import json
import os
import random
from pathlib import Path
from jinja2 import Environment, FileSystemLoader

# Import the functions that create the crews
from starfall.crew import create_k8s_scan_crew, create_version_discovery_crew, create_sequential_report_generator_crew, final_report_summary_crew
from starfall.utils import assign_task_output_file_name

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

def run():
    """
    Runs the 4-stage crew process:
    1. The K8sScan crew to generate the initial cluster report.
    2. The VersionDiscovery crew to enrich the report with latest version data.
    3. The ReleaseNotesDiscovery crew to gather relevant release notes.
    4. The ReportGenerator crew to compile the final report.

    """
    # ===========================================
    # Global variables
    # ===========================================
    module_dir = Path(__file__).resolve().parent              # .../starfall/src/starfall
    # repo_root is the project root: .../starfall (one level above 'src')
    repo_root = module_dir.parents[1]                         # .../starfall
    template_dir = module_dir / "templates"                   # templates alongside main.py
    outputs_dir = repo_root / "outputs"
    tool_report_template = "final_report_tool.py.jinja"
    emoji_pool = [
        "🚀", "🌟", "🛠️", "⚙️", "📦", "🔧", "🧭", "🛰️", "🌐", "🧩",
        "🔒", "📊", "🧪", "🐳", "☁️", "🛡️", "🧰", "🧠", "🪐", "🌈",
        "📡", "🔭", "🧱", "🗂️", "🪄", "📝", "📌", "⚡", "🧵", "🔁"
    ]


    # --- Stage 1: K8sScan Crew ---
    print("--- Running K8sScan crew (Stage 1) ---")
    try:
        # Call the function to create the K8sScan crew
        k8s_scan_crew = create_k8s_scan_crew()
        k8s_scan_result = k8s_scan_crew.kickoff(inputs={})
        
        # Access the raw string output from the CrewOutput object
        k8s_json_output = k8s_scan_result.raw
        
        # Ensure the output is not empty before proceeding.
        if not k8s_json_output:
            raise Exception("K8sScan crew returned no output. Aborting.")

    except Exception as e:
        # Catch and re-raise a custom exception to make debugging easier.
        raise Exception(f"An error occurred in K8sScan crew: {e}")

    # --- Stage 2: VersionDiscovery Crew ---
    print("\n--- Running VersionDiscovery crew (Stage 2) ---")
    try:
        # Call the function to create the VersionDiscovery crew
        version_discovery_crew = create_version_discovery_crew()
        
        # Pass the output of the first crew as a named input
        # to the second crew's kickoff method. The manager agent's task is
        # designed to handle this 'k8s_data' input.
        final_report = version_discovery_crew.kickoff(inputs={'k8s_data': k8s_json_output})
        
    except Exception as e:
        raise Exception(f"An error occurred in VersionDiscovery crew: {e}")

    # --- Stage 3: Release info discovery Crew ---
    print("\n--- Running Release info discovery Crew (Stage 3) ---")

    # Check the value of the STARFALL_HIERARCHICAL_MODE environment variable. From its value we will drive the below path of execution
    hierarchical_mode = os.getenv("STARFALL_HIERARCHICAL_MODE", "false").lower() in ("true", "1", "yes")

    if hierarchical_mode:
        # If hierarchical mode is enabled, we will use a Hierarchical Process Crew for this step
        print("Using Hierarchical Process Crew for Release info discovery")

        # TODO - Implement logic for hierarchical process crew


    else:
        # If hierarchical mode is not enabled, we will use a Sequential Process Crew for this step
        print("Using Sequential Process Crew for Release info discovery")

        try:
            # LOAD Result of previous tasks
            final_scanned_obj_file = outputs_dir / "final_k8s_scanner_report.json"
            with final_scanned_obj_file.open('r') as f:
                final_scanned_obj = json.load(f)


            # Split the received object and loop through each element. The Sequential crew will address one block at the time
            # -> Generate partial report for Kubernetes itself
            if final_scanned_obj['kubernetes_control_plane']:
                #print(final_scanned_obj['kubernetes_control_plane'])

                # ===========================================
                # Create the crew, configure it and start it
                # ===========================================
                sequential_report_generator_crew = create_sequential_report_generator_crew()

    
                truncated_version = ".".join(final_scanned_obj['kubernetes_control_plane']['latest_version'].split(".")[:2])

                # Assign dynamic output_file for the task "release_notes_task"
                assign_task_output_file_name(
                    sequential_report_generator_crew,
                    scope="features",
                    task_name="release_notes_task",
                    tool_name="kubernetes",
                    tool_version=truncated_version,
                )

                assign_task_output_file_name(
                    sequential_report_generator_crew,
                    scope="risks",
                    task_name="upgrade_risks_task",
                    tool_name="kubernetes",
                    tool_version=truncated_version,
                )

                assign_task_output_file_name(
                    sequential_report_generator_crew,
                    scope="recommendations",
                    task_name="final_report_task",
                    tool_name="kubernetes",
                    tool_version=truncated_version,
                )
            
                # Start the crew
                k8s_report = sequential_report_generator_crew.kickoff(inputs={
                    'tool_name': "kubernetes",
                    'tool_latest_version': truncated_version,
                    'tool_current_version': final_scanned_obj['kubernetes_control_plane']['current_version']
                })

                # ===========================================================================
                # Generate the final report for the Kubernetes control plane
                # ===========================================================================
                features_md = outputs_dir / f"kubernetes-{truncated_version}-features-report.md"
                risks_md = outputs_dir / f"kubernetes-{truncated_version}-risks-report.md"
                recommendations_md = outputs_dir / f"kubernetes-{truncated_version}-recommendations-report.md"



                # Load raw markdown
                highlights_raw = features_md.read_text(encoding="utf-8")
                risks_raw = risks_md.read_text(encoding="utf-8")
                recommendations_raw = recommendations_md.read_text(encoding="utf-8")

                env = Environment(
                    loader=FileSystemLoader(str(template_dir)),
                    autoescape=False,
                    trim_blocks=True,
                    lstrip_blocks=True,
                )

                template = env.get_template(tool_report_template)

                rendered = template.render(
                    tool_name="kubernetes",
                    tool_icon="☸️",
                    current_version=final_scanned_obj['kubernetes_control_plane']['current_version'],
                    latest_version=final_scanned_obj['kubernetes_control_plane']['latest_version'],
                    highlights_table=highlights_raw,          # full file content dropped in
                    breaking_changes=risks_raw,               # full file content dropped in
                    final_recommendation=recommendations_raw, # full file content dropped in
                )

                with (repo_root / "outputs" / "kubernetes-upgrade-report.md").open("w", encoding="utf-8") as f:
                    f.write(rendered)

            # -> Generate partial report for each identified application
            if final_scanned_obj['apps']:
                for app in final_scanned_obj['apps']:
                    for container in app['containers']:
                        # ===========================================
                        # Create the crew, configure it and start it
                        # ===========================================
                        sequential_report_generator_crew = create_sequential_report_generator_crew()
                        truncated_version = ".".join(container['latest_version'].split(".")[:2])
                        
                        # Assign dynamic output_file for the task "release_notes_task"
                        assign_task_output_file_name(
                            sequential_report_generator_crew,
                            scope="features",
                            task_name="release_notes_task",
                            tool_name=app["name"]+"-"+container['name'],
                            tool_version=truncated_version,
                        )
                        assign_task_output_file_name(
                            sequential_report_generator_crew,
                            scope="risks",
                            task_name="upgrade_risks_task",
                            tool_name=app["name"]+"-"+container['name'],
                            tool_version=truncated_version,
                        )
                    
                        assign_task_output_file_name(
                            sequential_report_generator_crew,
                            scope="recommendations",
                            task_name="final_report_task",
                            tool_name=app["name"]+"-"+container['name'],
                            tool_version=truncated_version,
                        )

                        # Start the crew
                        app_report = sequential_report_generator_crew.kickoff(inputs={
                            'tool_name': container['name'],
                            'tool_latest_version': truncated_version,
                            'tool_current_version': container['current_version']
                        })

                        # ===========================================================================
                        # Generate the final report for each tool
                        # ===========================================================================
                        features_md = outputs_dir / f"{app["name"]+"-"+container['name']}-{truncated_version}-features-report.md"
                        risks_md = outputs_dir / f"{app["name"]+"-"+container['name']}-{truncated_version}-risks-report.md"
                        recommendations_md = outputs_dir / f"{app["name"]+"-"+container['name']}-{truncated_version}-recommendations-report.md"



                        # Load raw markdown
                        highlights_raw = features_md.read_text(encoding="utf-8")
                        risks_raw = risks_md.read_text(encoding="utf-8")
                        recommendations_raw = recommendations_md.read_text(encoding="utf-8")

                        env = Environment(
                            loader=FileSystemLoader(str(template_dir)),
                            autoescape=False,
                            trim_blocks=True,
                            lstrip_blocks=True,
                        )

                        template = env.get_template(tool_report_template)

                        rendered = template.render(
                            tool_name=app["name"]+"-"+container['name'],
                            tool_icon=random.choice(emoji_pool),
                            current_version=container['current_version'],
                            latest_version=container['latest_version'],
                            highlights_table=highlights_raw,          # full file content dropped in
                            breaking_changes=risks_raw,               # full file content dropped in
                            final_recommendation=recommendations_raw, # full file content dropped in
                        )

                        with (repo_root / "outputs" / f"{app["name"]+"-"+container['name']}-upgrade-report.md").open("w", encoding="utf-8") as f:
                            f.write(rendered)




            # Call the function to create the crew
            #version_discovery_crew = create_version_discovery_crew()
            
            # Pass the output of the first crew as a named input
            # to the second crew's kickoff method. The manager agent's task is
            # designed to handle this 'k8s_data' input.
            #final_report = version_discovery_crew.kickoff(inputs={'k8s_data': k8s_json_output})
            
        except Exception as e:
            raise Exception(f"An error occurred in Release info discovery crew: {e}")


    # --- Stage 4: Report Generation and summary ---
    # 1. Get all individual tools report into a single one
    # 2. Pass the report to LLM and ask for a short intro summary
    print("\n--- Running Report Generation and summary (Stage 4) ---")
    try:
        print("Join all reports into a single one")
        pattern = "*upgrade-report.md"
        # Build dated aggregate filename: dd-mm-yy-all-upgrades-aggregate.md
        date_prefix = datetime.now().strftime("%d-%m-%y")
        aggregate_file = outputs_dir / f"{date_prefix}-all-upgrades-aggregate.md"

        # Ensure output directory exists
        outputs_dir.mkdir(parents=True, exist_ok=True)

        parts = []
        for path in sorted(outputs_dir.glob(pattern)):
            # Skip the aggregate file itself if re-running
            if path.name == aggregate_file.name:
                continue
            if path.is_file():
                content = path.read_text(encoding="utf-8").rstrip()
                # Add the report content followed by two <br> tags
                parts.append(content + "\n<br><br>\n---")

        aggregate_file.write_text("\n".join(parts), encoding="utf-8")
        print(f"Wrote {aggregate_file}")


        # ===========================================
        # Create the crew, configure it and start it
        # ===========================================
        report_summary_crew = final_report_summary_crew()
    
        print(aggregate_file)
        # Start the crew
        report_summary_crew.kickoff(inputs={
            'file_path': str(aggregate_file),
        })

        # Post-summary: prepend platform-upgrade.md content to aggregate_file
        platform_file = outputs_dir / "platform-upgrade.md"
        if platform_file.exists():
            try:
                platform_content = platform_file.read_text(encoding="utf-8").rstrip()
                current_content = aggregate_file.read_text(encoding="utf-8")
                platform_file.write_text(platform_content + "\n<br><br>\n---\n# 🔍 Tool Details  \n---\n\n" + current_content, encoding="utf-8")
            except Exception as e:
                print(f"Warning: could not prepend platform-upgrade.md content: {e}")



    except Exception as e:
        raise Exception(f"An error occurred in Release info discovery crew: {e}")




if __name__ == "__main__":
    run()


# def train():
#     """
#     Train the crew for a given number of iterations.
#     """
#     inputs = {
#         "topic": "AI LLMs",
#         'current_year': str(datetime.now().year)
#     }
#     try:
#         Starfall().crew().train(n_iterations=int(sys.argv[1]), filename=sys.argv[2], inputs=inputs)

#     except Exception as e:
#         raise Exception(f"An error occurred while training the crew: {e}")

# def replay():
#     """
#     Replay the crew execution from a specific task.
#     """
#     try:
#         Starfall().crew().replay(task_id=sys.argv[1])

#     except Exception as e:
#         raise Exception(f"An error occurred while replaying the crew: {e}")

# def test():
#     """
#     Test the crew execution and returns the results.
#     """
#     inputs = {
#         "topic": "AI LLMs",
#         "current_year": str(datetime.now().year)
#     }
    
#     try:
#         Starfall().crew().test(n_iterations=int(sys.argv[1]), eval_llm=sys.argv[2], inputs=inputs)

#     except Exception as e:
#         raise Exception(f"An error occurred while testing the crew: {e}")
