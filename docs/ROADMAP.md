# 🛠️ In Progress / Next Up
- Phase 3 foundation  
  - Define ENV variable to toggle operational model  
    - **Name proposal:** `STARFALL_HIERARCHICAL_MODE` (boolean: `true` for hierarchical crews, `false` for sequential loop)  
  - Start implementing **Sequential mode** as baseline  
    - Loop over JSON results  
    - Pass individual objects to Agents  
    - Collect results and assemble into unified Markdown report  
<br>


# 📈 Planned / Future
- **Phase 3 – Sequential Mode**
  - Define JSON traversal logic  
  - Implement Agent flow:  
    - Agent finds latest release notes for tool  
    - Agent extracts highlights:  
      - New features for **platform engineers**  
      - New features for **developers/consumers**  
      - **Breaking changes**  
    - Assemble results into unified JSON structure  
  - Define modern Markdown template for final report  
    - Sections: Overview, Platform Engineer Features, Developer Features, Breaking Changes, Version Metadata  
  - Implement “Uploader” step:  
    - Store final Markdown report in central location (GitHub Pages, S3, or similar)  
  - Slack notification step:  
    - Short summary (tool + version + # highlights)  
    - Link to full Markdown report  
<br>

- **Phase 3 – Hierarchical Mode**
  - Implement Manager → Sub-crew orchestration  
    - Manager delegates release-notes discovery  
    - Sub-crew extracts highlights (platform engineer vs developer vs breaking changes)  
    - Manager assembles into Markdown + passes to uploader/Slack  
  - Define Hierarchical Crew roles more formally:  
    - Manager  
    - Research Agent (fetches release notes)  
    - Analyzer Agent (extracts + categorizes changes)  
    - Reporter Agent (generates Markdown + summary)  
  - Validate results vs Sequential mode (consistency check)  
<br>

- **General Improvements**
  - Markdown → PDF/HTML export support  
  - Report versioning (keep history of past reports)  
  - Configurable Slack formatting (short or extended summary)  
  - Add support for multiple notification channels (Slack + GitHub issue + email)  
<br>


# 🧪 Postponed
- Unit testing for release-notes extraction (focus on core functionality first)  
- Automatic diffing of *all intermediate versions* (currently only latest vs current is considered)  
<br>


# ✅ Done
- **Phase 1** – Starfall first Agent  
  - Scans a k8s cluster  
  - Returns structured JSON of discovered tooling  
- **Phase 2** – Starfall second crew  
  - Manager delegates tasks  
  - Coworker retrieves latest release of identified tooling  
