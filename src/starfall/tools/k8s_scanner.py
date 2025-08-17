from crewai.tools import BaseTool
from typing import List, Dict, Any
from kubernetes import client, config
from datetime import datetime

from starfall.pydantic_models import K8sClusterScanResult, ClusterInfo, AppInfo, ContainerInfo


# class ScanK8sCluster(BaseTool):
#     name: str = "Scan a Kubernetes Cluster looking for the kubernetes version and Applications to upgrade"
#     description: str = (
#         "Scan a Kubernetes cluster, namespaces and deployments that share the same label key and value. "
#         "The label is starfall.io/enabled = true. "
#         "Returns a structured dictionary with cluster version, name, scan time, and a list of apps with deployment, namespace, container images, versions, and labels."
#     )
class ScanK8sCluster(BaseTool):
    name: str = "Kubernetes Control Plane and Application Inventory Scanner"
    description: str = (
        "Performs a comprehensive scan of a Kubernetes cluster and its workloads to inventory upgrade candidates."
        "Identifies all namespaces and deployments explicitly labeled with 'starfall.io/enabled=true', and gathers detailed metadata for each: "
        "deployment name, namespace, containers (including image and version), and all deployment labels. "
        "Also retrieves the current Kubernetes control plane version, cluster name or identifier, and a precise scan timestamp. "
        "Produces a structured dictionary suitable for downstream upgrade planning, compliance checks, and automation. "
        "Excludes any resources not matching the label criteria. Does not modify cluster state."
    )

    def _run(self) -> K8sClusterScanResult:
        label_key = "starfall.io/enabled"
        label_value = "true"
        label_selector = f"{label_key}={label_value}"

        try:
            # Load Kubernetes config (in-cluster first, fallback to local kubeconfig)
            try:
                config.load_incluster_config()
            except Exception:
                config.load_kube_config()

            v1 = client.CoreV1Api()
            apps_v1 = client.AppsV1Api()

            # Get cluster version
            version_info = client.VersionApi().get_code()
            cluster_version = getattr(version_info, "git_version", "unknown")

            scanned_at = datetime.utcnow().isoformat() + "Z"

            # Get namespaces matching the label
            namespaces = v1.list_namespace(label_selector=label_selector)
            ns_names = [ns.metadata.name for ns in namespaces.items]

            apps = []
            for ns in ns_names:
                deployments = apps_v1.list_namespaced_deployment(
                    ns, label_selector=label_selector
                )
                for dep in deployments.items:
                    dep_labels = dep.metadata.labels or {}
                    containers_info = []
                    for container in dep.spec.template.spec.containers:
                        image = container.image
                        image_tag = image.split(":")[1] if ":" in image else "unknown"
                        containers_info.append(
                            ContainerInfo(
                                name=container.name,
                                image=image,
                                current_version=image_tag,
                                latest_version=None,               
                                latest_version_info_url=None
                            )
                        )
                    app_info = AppInfo(
                        name=dep.metadata.name,
                        namespace=ns,
                        deployment=dep.metadata.name,
                        containers=containers_info,
                        labels=dep_labels
                    )
                    apps.append(app_info)

            cluster_info = ClusterInfo(
                current_version=cluster_version,
                name="Kubernetes",
                scanned_at=scanned_at,
                latest_version=None,
                latest_version_info_url=None
            )

            result = K8sClusterScanResult(
                kubernetes_control_plane=cluster_info,
                apps=apps
            )
            return result

        except Exception as e:
            # Optionally: You can return a K8sClusterScanResult with an error app entry or raise
            raise RuntimeError(f"Exception during cluster scan: {e}")