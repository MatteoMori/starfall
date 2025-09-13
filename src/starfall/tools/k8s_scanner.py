from crewai.tools import BaseTool
from typing import List, Dict, Any
from kubernetes import client, config
from datetime import datetime

from starfall.pydantic_models import K8sClusterScanResult, ClusterInfo, AppInfo, ContainerInfo


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

            v1 = client.CoreV1Api()      # Namespaces, Pods, Services, etc.
            apps_v1 = client.AppsV1Api() # Deployments, Daemonsets, Statefulsets, etc.

            # Get cluster version
            version_info = client.VersionApi().get_code()
            cluster_version = getattr(version_info, "git_version", "unknown")


            # Identify the namespaces matching the label
            namespaces = v1.list_namespace(label_selector=label_selector)
            ns_names = [ns.metadata.name for ns in namespaces.items]

            apps = []
            for ns in ns_names:
                deployments = apps_v1.list_namespaced_deployment(
                    ns, label_selector=label_selector
                )

                daemonsets = apps_v1.list_namespaced_daemon_set(
                    ns, label_selector=label_selector
                )

                # TODO: Optionally include Statefulsets, Jobs, CronJobs, etc.

                # Explore the Deployments and Daemonsets looking for information
                deployments_info = self.Inspector(apps, deployments, "deployment", ns)
                apps.extend(deployments_info)

                daemonsets_info = self.Inspector(apps, daemonsets, "daemonset", ns)
                apps.extend(daemonsets_info)


            cluster_info = ClusterInfo(
                current_version=cluster_version,
                name="Kubernetes",
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


    def Inspector(self, apps: List[AppInfo], resourceObj: List, resourceKind: str, resourceNamespace: str) -> List[AppInfo]:
        """
        Loop though a K8s object and extract relevant information
        """

        for i in resourceObj.items:
            labels = i.metadata.labels or {}
            containers_info = []
            for container in i.spec.template.spec.containers:
                image = container.image
                # Remove any digest suffix (everything after '@') so parsing the tag is reliable
                base_image = image.split("@", 1)[0] if "@" in image else image
                image_tag = base_image.split(":")[1] if ":" in base_image else "unknown"
                containers_info.append(
                    ContainerInfo(
                        name=container.name,
                        image=base_image,
                        current_version=image_tag,
                        latest_version=None,               
                        latest_version_info_url=None
                    )
                )
            app_info = AppInfo(
                name=i.metadata.name,
                namespace=resourceNamespace,
                kind=resourceKind,
                containers=containers_info,
                labels=labels
            )
            apps.append(app_info)


        return apps