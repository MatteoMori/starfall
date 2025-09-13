# 🛠️ In Progress / Next Up
- 🔎 Expand K8s scanner to Statefulsets 🧱, Prometheus Kinds 📈, Daemonsets 🛡️
  - Use the chance to review the k8s JSON object
- 📊 Improve the Final summary report
  - 🎯 Risk score has to be more meaningfull
  - 🎯 Better naming for Tools
  - 🎯 K8s has to be the first Tool in the report
- 🗺️ Update Starfall flow diagram

# 📈 Planned / Future
- 🧯 Compatibility Guardrails (next)
  - Validate Kubernetes version skew policy and min/max supported versions per tool
  - Leverage tool compatibility matrices when available (e.g., Cilium, Ingress-NGINX, Kubernetes skew)
  - Check Helm chart `kubeVersion` constraints, CRD and API deprecations, and known breaking compat notes
  - Add report badges: ✅ Compatible, ⚠️ Needs k8s bump, ⛔ Blocked — with a short rationale and source links
  - Influence Priority by increasing Risk when incompatibilities or blockers are detected
- 📤 Run as kube Cronjob
- 📤 “Uploader” step
  - Store final Markdown (and optional HTML/PDF) in a central location (GitHub Pages, S3, or similar)
  - Return a stable link and surface upload errors with retries/backoff
- 🔔 Slack notification
  - Short summary (tool + version + # highlights)
  - Link to full hosted report
  - Support dry-run mode
- 📄 Export options
  - Markdown → PDF/HTML export support
- 🗂️ Report versioning (history)
  - Keep past reports and provide a simple index
- 🎛️ Configurable Slack formatting
  - Short vs extended summaries
- 📣 Additional notification channels
  - GitHub Issue and Email (optional, per-run configurable)


# 🧪 Postponed
- Unit testing for release-notes extraction (focus on core functionality first)
- Automatic diffing of all intermediate versions (currently only latest vs current is considered)


# ✅ Done
- Phase 4
  - 🧹 Minor refining
    - [x] Report naming conventions (stable, human-friendly filenames)
    - [x] Cleanup unused env variables and flags
    - [x] Normalize file/folder paths and output locations
    - [x] Dockerfile + improve Install docs

- ✅ Phase 3
  - 🧭 Define JSON traversal logic
  - 🔁 Implement Sequential mode baseline
    - Loop over JSON results, pass individual objects to Agents, assemble unified Markdown report
  - 🔎 Agent: find latest release notes for tool
  - 🧠 Agent: extract and categorize highlights
    - New features for platform engineers, developers/consumers, and breaking changes
  - 🧩 Assemble results into unified JSON structure
  - 📝 Define modern Markdown template for final report
    - Sections: Overview, Platform Engineer Features, Developer Features, Breaking Changes, Version Metadata
- ✅ Phase 1 — First Agent
  - Scans a k8s cluster and returns structured JSON of discovered tooling
- ✅ Phase 2 — Second crew
  - Manager delegates tasks; coworker retrieves latest releases of identified tooling