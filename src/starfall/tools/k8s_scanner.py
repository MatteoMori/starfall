#import os
from crewai.tools import BaseTool
from typing import List, Dict, Any
# from pydantic import BaseModel, Field
# from kubernetes import client, config

class ScanK8sCluster(BaseTool):
    name: str = "Scan a Kubernetes Cluster"
    description: str = (
        "Scan a Kubernetes cluster, namespaces and deployments that share the same label key and value. "
        "The label is starfall.enabled = true"
        "Returns a list of deployments with name, namespace, and version."
    )

    #def _run(self, label_value: str) -> List[Dict[str, Any]]:
    def _run(self) -> List[Dict[str, Any]]:
        # Mock output for testing
        return [
            {"namespace": "default", "deployment_name": "frontend", "version": "1.2.3"},
            {"namespace": "default", "deployment_name": "backend", "version": "4.5.6"},
        ]

# class ScanClusterInput(BaseModel):
#     """Input schema for the ScanClusterTool."""
#     label_value: str = Field(
#         default="true",
#         description="The label value to match for namespaces and deployments."
#     )


# class ScanClusterLabeledTool(BaseTool):
#     name: str = "scan_cluster_labeled"
#     description: str = (
#         "Scans Kubernetes namespaces and deployments that share the same label key and value. "
#         "The label key is read from the STARFALL_LABEL_KEY environment variable "
#         "(default: 'starfall.enabled'). Returns a list of deployments with name, namespace, and version."
#     )
#     args_schema: Type[BaseModel] = ScanClusterInput

#     def _run(self, label_value: str) -> List[Dict[str, Any]]:
#         label_key = os.getenv("STARFALL_LABEL_KEY", "starfall.enabled")
#         label_selector = f"{label_key}={label_value}"

#         print(f"[DEBUG] Using label selector: {label_selector}")

#         try:
#             # Load Kubernetes config (in-cluster first, fallback to local kubeconfig)
#             try:
#                 config.load_incluster_config()
#                 print("[DEBUG] Loaded in-cluster Kubernetes config")
#             except:
#                 config.load_kube_config()
#                 print("[DEBUG] Loaded local kubeconfig")

#             v1 = client.CoreV1Api()
#             apps_v1 = client.AppsV1Api()

#             # Get namespaces matching the label
#             namespaces = v1.list_namespace(label_selector=label_selector)
#             ns_names = [ns.metadata.name for ns in namespaces.items]
#             print(f"[DEBUG] Matching namespaces: {ns_names}")

#             results = []
#             for ns in ns_names:
#                 deployments = apps_v1.list_namespaced_deployment(
#                     ns, label_selector=label_selector
#                 )
#                 print(f"[DEBUG] Found {len(deployments.items)} deployments in namespace '{ns}'")

#                 for dep in deployments.items:
#                     # Try label first
#                     version = dep.metadata.labels.get("app.kubernetes.io/version")
#                     if not version:
#                         # Fallback to image tag
#                         try:
#                             image = dep.spec.template.spec.containers[0].image
#                             version = image.split(":")[1] if ":" in image else "unknown"
#                         except Exception:
#                             version = "unknown"

#                     dep_info = {
#                         "name": dep.metadata.name,
#                         "namespace": ns,
#                         "version": version
#                     }
#                     print(f"[DEBUG] Deployment found: {dep_info}")
#                     results.append(dep_info)

#             print(f"[DEBUG] Total deployments found: {len(results)}")
#             return results

#         except Exception as e:
#             print(f"[ERROR] Exception during cluster scan: {e}")
#             return [{"error": str(e)}]
