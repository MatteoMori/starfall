 # Performance Tracking 📈

Tracking qualitative + lightweight quantitative observations for local LLM performance in Starfall upgrade workflows.

> ℹ️ No frontier (large proprietary) models yet due to cost & local-first preference. Starfall currently targets locally hosted models.

**Hardware (baseline test rig)**
* 🧠 CPU: Ryzen 7 (8 core)
* 💾 Memory: 32 GB

## 🏆 Current Best Model

For BOTH Kubernetes resource scanning and latest version discovery tasks the best overall balance of speed, accuracy, and token efficiency is:

➡️ **`qwen3:4b-instruct-2507-q4_K_M`**

Reasons:
* Fastest first-token + completion among tested variants
* Consistent extraction of required fields (including latest version labels)
* Lower memory footprint vs 8B while maintaining precision

---

## Test Run 1 (Context = 10,000)

**Generation Parameters:**
```dockerfile
PARAMETER num_ctx 10000
PARAMETER temperature 0.1
PARAMETER top_p 0.1
PARAMETER top_k 40
```

| Model | Perf Summary | Accuracy (qualitative) | Memory Footprint (approx) | Notes |
|-------|--------------|------------------------|----------------------------|-------|
| `qwen3:8b` | 🐢 Slow (CPU saturated quickly) | N/A | High | Not ideal for rapid iterative tasks |
| `qwen3:4b-instruct` | Moderate | ✅ Perfect answer | Medium | Slight lag but reliable |
| `qwen3:4b-q8_0` | Moderate-slow | ⚠️ Missed LATEST label | Medium-High (~12GB) | Retest after code improvements |
| `qwen3:4b-instruct-2507-q4_K_M` | 🚀 Fast | ✅ Perfect answer | Low/Lean | Chosen baseline going forward |

Legend: 🚀 = noticeably faster, 🐢 = slow, ✅ = meets all extraction goals, ⚠️ = partial/missing field

---

## 🎯 Next Experiments

Objective: Evaluate impact of reducing context window to 4096 on latency & output completeness.

| Model | Planned num_ctx | Hypothesis | Priority |
|-------|-----------------|-----------|----------|
| `qwen3:4b-instruct` | 4096 | Should speed up slightly; accuracy intact | High |
| `qwen3:4b-q8_0` | 4096 | May still miss labels—validate after parser improvements | Medium |
| `qwen3:4b-instruct-2507-q4_K_M` | 4096 | Expect same accuracy, even faster → candidate default | High |
| `qwen3:8b` | 4096 | Still too slow; baseline comparative data | Low |
| `qwen3:8b-q8_0` | 4096 | Check if quantization narrows gap vs 4B variants | Medium |


---

## 📌 Notes & Actions
* Re-run `qwen3:4b-q8_0` after improving label extraction logic.

