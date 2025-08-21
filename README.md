# Starfall

<img src="./imgs/logo/20250814_112206603_iOS.jpg" width="140" alt="Starfall Logo">

> AI-powered upgrade helper for Kubernetes clusters and the software you run on them.

---

## Overview

Starfall is an "Upgrade Helper": it automates the repetitive and error‑prone work of researching upgrade paths for your Kubernetes control plane and in-cluster applications.

Instead of manually answering:
* What version is currently running?
* What is the latest stable version?
* Are there breaking changes or relevant release notes?
* What is the safest upgrade path?

Starfall:
1. Scans the cluster (control plane + selected workloads)
2. Collects version + metadata
3. Looks up latest stable releases
4. Summarizes meaningful upgrade notes (planned capability)
5. Prepares actionable insights (e.g. Slack / GitHub Issue / Email)

## Architecture Diagram

![Starfall flow](./imgs/references/starfall%20-%20flow.png)

## Key Features (current & planned)

| Area | Status | Notes |
|------|--------|-------|
| Kubernetes control plane version detection | ✅ | Captures current + latest version
| Workload container image version extraction | ✅ | Parses Deployments (selectively via labels)
| Latest release lookup | ✅ (basic) | Uses external release sources (currently GitHub)
| Structured task delegation to AI agents | ✅ | CrewAI powered
| Release notes summarization | ⏳ | Planned enhancement
| Delivery integrations (Slack / GitHub issues) | ⏳ | Planned
| Safety / diff heuristics | ⏳ | Planned

## Tech Stack

* Python (uv + virtualenv)
* CrewAI for multi‑agent orchestration
* Ollama (Qwen3) as the local LLM provider
* Kubernetes (scan target)

## Repository Layout (selected)

| Path | Purpose |
|------|---------|
| `src/starfall/crew.py` | Crew & agent orchestration entry points |
| `src/starfall/main.py` | CLI / execution entry |
| `src/starfall/tools/k8s_scanner.py` | Cluster + workload scanning tool |
| `src/starfall/pydantic_models.py` | Data models (versions, apps, etc.) |
| `knowledge/` | User / domain guidance for agents |
| `outputs/` | Generated scan reports (JSON) |
| `docs/` | Roadmap, tools overview, performance notes |

## Getting Started

### 1. Prerequisites
* Python 3.11+ (align with your local environment)
* Access to a Kubernetes cluster (or kind/minikube)
* Ollama installed locally (for Qwen3 model)
* Git + curl

### 2. Environment Setup
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip setuptools wheel
pip install ipython
```

If using `uv` (alternative toolchain):
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
uv tool install crewai
```

### 3. Configure LLM Provider
Ensure Ollama is running and Qwen3 (or your chosen model) is pulled:
```bash
ollama pull qwen:latest   # or the specific variant you prefer
```
Update `.env` with any required provider configuration.

### 4. (Optional) Regenerate Crew Scaffolding
```bash
crewai create crew starfall
```
Creation output (for reference) is preserved below.

<details>
  <summary>Scaffolding output</summary>

  ```bash
  Creating folder starfall...
  Cache expired or not found. Fetching provider data from the web...
  ... (provider/model selection prompts) ...
  Crew starfall created successfully!
  ```
</details>

## Running a Scan (Conceptual Flow)

```bash
crewai run
```

1. Invoke the scanner tool (code in `k8s_scanner.py`) to produce an initial JSON snapshot (e.g. `initial_k8s_scanner_report.json`).
2. Agents receive structured tasks derived from that snapshot.
3. Release intelligence specialist agents look up the latest stable versions.
4. A manager agent aggregates findings into `final_k8s_scanner_report.json`.
5. (Planned) Formatter / publisher pushes insights to external destinations.

## Task Delegation Contract

Manager-to-coworker task objects must strictly follow this JSON shape:
```json
{
  "task": "Find the latest stable version for the container 'redis' in the app 'redis-test-app'",
  "context": "The app object is {\"name\": \"redis-test-app\", \"namespace\": \"starfall-test\", \"deployment\": \"redis-test-app\", \"containers\": [{\"name\": \"redis\", \"image\": \"redis:7.2.0\", \"current_version\": \"7.2.0\"}], \"labels\": {\"app\": \"redis-test-app\", \"starfall.io/enabled\": \"true\"}}",
  "coworker": "Software Release Intelligence Specialist"
}
```
Consistency here ensures reliable downstream parsing & agent behavior.

## Data Outputs

Example (prettified) structure of a final report:
```json
{
  "kubernetes_control_plane": {
    "current_version": "v1.x.y",
    "latest_version": "v1.x.y",
    "name": "Kubernetes",
    "scanned_at": "<ISO8601>",
    "latest_version_info_url": "https://..."
  },
  "apps": [
    {
      "name": "example-app",
      "namespace": "example-ns",
      "deployment": "example-app",
      "containers": [
        {
          "name": "app",
          "image": "repo/app:1.2.3",
          "current_version": "1.2.3",
          "latest_version": "1.3.0",
          "latest_version_info_url": "https://..."
        }
      ],
      "labels": { "app": "example-app" }
    }
  ]
}
```

## Development Notes

* Use labels (e.g. `starfall.io/enabled=true`) to scope which workloads are scanned.
* Extend scanning logic by adding new collectors under `tools/`.
* Pydantic models enforce structure—update them if you add fields.

## Roadmap & Docs

See:
* `docs/ROADMAP.md`
* `docs/TOOLS.md`
* `docs/PERFORMANCE-TRACKING.md`

## Contributing (Lightweight Process)

1. Open an issue / jot intent
2. Create a feature branch
3. Keep changes focused
4. Include/adjust sample output if data model changes

## FAQ (Early Stage)

| Question | Answer |
|----------|--------|
| Why Qwen3 via Ollama? | Local control + good reasoning/price profile |
| Does it mutate the cluster? | No, read-only scanning (current scope) |
| How are latest versions resolved? | GitHub releases (initial); pluggable sources planned |

---

_Starfall is in an iterative build phase. Expect rapid changes._