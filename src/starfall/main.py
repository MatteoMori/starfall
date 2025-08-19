#!/usr/bin/env python
import sys
import warnings
import json

# Import the functions that create the crews
from starfall.crew import create_k8s_scan_crew, create_version_discovery_crew

# This is a good practice to handle a common warning related to a specific library.
warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

def run():
    """
    Runs the two-stage crew process:
    1. The K8sScan crew to generate the initial cluster report.
    2. The VersionDiscovery crew to enrich the report with latest version data.
    """
    
    # --- Stage 1: K8sScan Crew ---
    print("--- Running K8sScan crew (Stage 1) ---")
    try:
        # Call the function to create the K8sScan crew
        k8s_scan_crew = create_k8s_scan_crew()
        k8s_scan_result = k8s_scan_crew.kickoff(inputs={})
        
        # Access the raw string output from the CrewOutput object
        k8s_json_output = k8s_scan_result.raw
        
        # We need to ensure the output is not empty before proceeding.
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
        
        # This is the key step: passing the output of the first crew as a named input
        # to the second crew's kickoff method. The manager agent's task is
        # designed to handle this 'k8s_data' input.
        final_report = version_discovery_crew.kickoff(inputs={'k8s_data': k8s_json_output})
        
        print("\n\n########################")
        print("## Final Combined Report ##")
        print("########################\n")
        print(final_report)

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
