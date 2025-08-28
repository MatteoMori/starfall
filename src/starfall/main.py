#!/usr/bin/env python
import sys
import warnings
import json
import os
from pathlib import Path

# Import the functions that create the crews
from starfall.crew import create_k8s_scan_crew, create_version_discovery_crew, create_sequential_release_notes_discovery_crew
warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

def run():
    """
    Runs the two-stage crew process:
    1. The K8sScan crew to generate the initial cluster report.
    2. The VersionDiscovery crew to enrich the report with latest version data.
    """
    
    # # --- Stage 1: K8sScan Crew ---
    # print("--- Running K8sScan crew (Stage 1) ---")
    # try:
    #     # Call the function to create the K8sScan crew
    #     k8s_scan_crew = create_k8s_scan_crew()
    #     k8s_scan_result = k8s_scan_crew.kickoff(inputs={})
        
    #     # Access the raw string output from the CrewOutput object
    #     k8s_json_output = k8s_scan_result.raw
        
    #     # Ensure the output is not empty before proceeding.
    #     if not k8s_json_output:
    #         raise Exception("K8sScan crew returned no output. Aborting.")

    # except Exception as e:
    #     # Catch and re-raise a custom exception to make debugging easier.
    #     raise Exception(f"An error occurred in K8sScan crew: {e}")

    # # --- Stage 2: VersionDiscovery Crew ---
    # print("\n--- Running VersionDiscovery crew (Stage 2) ---")
    # try:
    #     # Call the function to create the VersionDiscovery crew
    #     version_discovery_crew = create_version_discovery_crew()
        
    #     # Pass the output of the first crew as a named input
    #     # to the second crew's kickoff method. The manager agent's task is
    #     # designed to handle this 'k8s_data' input.
    #     final_report = version_discovery_crew.kickoff(inputs={'k8s_data': k8s_json_output})
        
    # except Exception as e:
    #     raise Exception(f"An error occurred in VersionDiscovery crew: {e}")


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
            # Simplified: load template report relative to this file's directory.
            template_path = Path(__file__).resolve().parent / 'templates' / 'final_k8s_scanner_report.json'
            with template_path.open('r') as f:
                final_scanned_obj = json.load(f)
            print(f"Loaded report from: {template_path}")
            #print(final_scanned_obj)

            # TODO - Pass value from previous step
            #final_scanned_obj = version_discovery_crew.kickoff(inputs={'k8s_data': k8s_json_output})

            # Split the received scanned object and loop for each element. The Sequential crew will address one block at the time
            #   -> Focus on the k8s control plane
            if final_scanned_obj['kubernetes_control_plane']:
                print(final_scanned_obj['kubernetes_control_plane'])
                # Call the function to create the Crew
                sequential_release_notes_discovery_crew = create_sequential_release_notes_discovery_crew()

                # Start the crew
                k8s_report = sequential_release_notes_discovery_crew.kickoff(inputs={
                    'tool_name': "kubernetes",
                    'tool_info': final_scanned_obj['kubernetes_control_plane']
                })
                print(k8s_report)


            #   -> Focus on each identified application
            if final_scanned_obj['apps']:
                for app in final_scanned_obj['apps']:
                    print(app)
                    print("--")

            # Call the function to create the crew
            #version_discovery_crew = create_version_discovery_crew()
            
            # Pass the output of the first crew as a named input
            # to the second crew's kickoff method. The manager agent's task is
            # designed to handle this 'k8s_data' input.
            #final_report = version_discovery_crew.kickoff(inputs={'k8s_data': k8s_json_output})
            
        except Exception as e:
            raise Exception(f"An error occurred in VersionDiscovery crew: {e}")





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
