from pydantic import BaseModel
from typing import List, Dict

class ContainerInfo(BaseModel):
    name: str
    image: str
    current_version: str

class AppInfo(BaseModel):
    name: str
    namespace: str
    deployment: str
    containers: List[ContainerInfo]
    labels: Dict[str, str]

class ClusterInfo(BaseModel):
    version: str
    name: str
    scanned_at: str  # ISO formatted datetime string

class K8sClusterScanResult(BaseModel):
    cluster: ClusterInfo
    apps: List[AppInfo]