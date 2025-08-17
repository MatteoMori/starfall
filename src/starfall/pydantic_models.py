from typing import List, Optional, Dict
from pydantic import BaseModel

'''
K8sClusterScanResult ->Data structure for Kubernetes cluster scan results.

EXAMPLE:
{
  "kubernetes_control_plane": {
    "current_version": "v1.32.0",
    "latest_version": null,
    "name": "Kubernetes",
    "scanned_at": "2025-08-16T15:10:42.189015Z",
  },
  "apps": [
    {
      "name": "nginx-test-app",
      "namespace": "starfall-test",
      "deployment": "nginx-test-app",
      "containers": [
        {
          "name": "nginx",
          "image": "nginx:latest",
          "current_version": "latest"
        }
      ],
      "labels": {
        "app": "nginx-test-app",
        "starfall.io/enabled": "true"
      }
    }
  ]
}
'''

class ClusterInfo(BaseModel):
    current_version: str
    latest_version: Optional[str] = None
    latest_version_info_url: Optional[str] = None
    name: str
    scanned_at: str

class ContainerInfo(BaseModel):
    name: str
    image: str
    current_version: str
    latest_version: Optional[str] = None
    latest_version_info_url: Optional[str] = None

class AppInfo(BaseModel):
    name: str
    namespace: str
    deployment: str
    containers: List[ContainerInfo]
    labels: Dict[str, str]

class K8sClusterScanResult(BaseModel):
    kubernetes_control_plane: ClusterInfo
    apps: List[AppInfo]

