# Code map

Updated: 2026-11-01 (America/Denver).
Current inventory inspected at commit `e6910c177ed7a1c8f9b29a06c0ca3627bec932fa`.
Product requirements: [SPEC.md](SPEC.md). Delivery sequence: [ROADMAP.md](ROADMAP.md).

## 1. Existing code in this repository

| Existing path | Responsibility | Planned integration |
| --- | --- | --- |
| [toolboxes/](toolboxes/) `Dockerfile.*` | Backend-specific image builds and runtime dependencies. | Recipes bind exact image/engine identity; preserve lean builds and backend-specific behavior. |
| [toolboxes/gguf-vram-estimator.py](toolboxes/gguf-vram-estimator.py) | Local GGUF metadata, multipart file sizes, FP16 KV approximation and configurable fixed overhead; prints context-size estimates. | [#4](https://github.com/iannitram/amd-strix-halo-toolboxes/issues/4) extracts structured planning without breaking the CLI; adds architecture/cache/concurrency/host reserves, pre-download metadata and disk planning. |
| [refresh-toolboxes.sh](refresh-toolboxes.sh) | Manual image pull and toolbox recreation. Current ordering removes an existing toolbox before pulling its replacement; cleanup removes dangling images. | [#2](https://github.com/iannitram/amd-strix-halo-toolboxes/issues/2) adds candidate staging, preservation, promotion/rollback and retention policy. Do not remove protected prior artifacts. |
| [scripts/run_distributed_llama.py](scripts/run_distributed_llama.py) | Dialog TUI, saved host/settings selection, SSH RPC startup, port readiness checks, benchmark depths and cleanup. | [#11](https://github.com/iannitram/amd-strix-halo-toolboxes/issues/11), [#12](https://github.com/iannitram/amd-strix-halo-toolboxes/issues/12), [#13](https://github.com/iannitram/amd-strix-halo-toolboxes/issues/13) add inventory, measured placement and session ownership. Existing cleanup includes broad process matching; managed sessions must track only their own processes. |
| [benchmark/run_benchmarks.sh](benchmark/run_benchmarks.sh), [benchmark/run_rpc_benchmarks.sh](benchmark/run_rpc_benchmarks.sh) | Single/distributed throughput campaigns. | [#9](https://github.com/iannitram/amd-strix-halo-toolboxes/issues/9) evaluates reusable methodology, records exact recipe/host identities and adds budgets/task outcomes. |
| [benchmark/mtp-bench.py](benchmark/mtp-bench.py), [benchmark/run_mtp_bench.py](benchmark/run_mtp_bench.py) | Speculative-decoding benchmark helpers. | Backend-specific comparison adapters; do not assume MTP support across all recipes. |
| [benchmark/toolbox_performance/run_calibrated_campaign.py](benchmark/toolbox_performance/run_calibrated_campaign.py) | Campaigns using saved Cockpit ubatch calibration. Imports older `src.benchmark_runner`, `src.model_manager`, `src.toolbox_manager`, `src.ubatch_calibration` and `src.ubatch_profiles`. | [#6](https://github.com/iannitram/amd-strix-halo-toolboxes/issues/6)/[#9](https://github.com/iannitram/amd-strix-halo-toolboxes/issues/9) must pin/verify compatibility; these imports are external integration dependencies, not local modules. |
| [benchmark/toolbox_performance/merge_curve_summary.py](benchmark/toolbox_performance/merge_curve_summary.py), [benchmark/toolbox_performance/validate_campaign.py](benchmark/toolbox_performance/validate_campaign.py) | Curve summary merging and campaign validation. | Review for [#9](https://github.com/iannitram/amd-strix-halo-toolboxes/issues/9)/[#10](https://github.com/iannitram/amd-strix-halo-toolboxes/issues/10) result provenance and comparability reuse. |
| [benchmark/generate_results_json.py](benchmark/generate_results_json.py), [benchmark/ryzen_ai_halo/generate_results_json.py](benchmark/ryzen_ai_halo/generate_results_json.py), [benchmark/toolbox_performance/generate_results_json.py](benchmark/toolbox_performance/generate_results_json.py) | Convert benchmark artifacts into viewer data. | Preserve historical output; introduce versioned new results rather than rewriting archival evidence. |
| [docs/index.html](docs/index.html), [docs/toolbox-performance.html](docs/toolbox-performance.html), [docs/mtp.html](docs/mtp.html), [docs/ryzen-ai-halo.html](docs/ryzen-ai-halo.html), [docs/assets/](docs/assets/) | Existing static benchmark views and assets, presented as legacy archive in README. | Keep archive links/provenance; new local UI is a separate proposed surface, not a claim that these pages manage live servers. |
| [docs/models.ini.example](docs/models.ini.example) | Example llama.cpp multi-model routing configuration. | [#8](https://github.com/iannitram/amd-strix-halo-toolboxes/issues/8) evaluates compatible routing; a sample file is not a universal endpoint adapter. |
| [systemd/gpu-workload-watch/](systemd/gpu-workload-watch/) | GPU process watcher and Framework cooling/TuneD switching service. | Optional host-readiness/telemetry integration; do not assume supported fan control on other hardware. |
| [.github/workflows/build_and_publish.yml](.github/workflows/build_and_publish.yml), `poll-*.yaml` | Image build/publication and upstream revision polling. | Recipe provenance consumes immutable build identities; compilation does not equal hardware qualification. |
| [.github/workflows/prune-old-toolboxes.yml](.github/workflows/prune-old-toolboxes.yml) | Registry retention policy. | [#2](https://github.com/iannitram/amd-strix-halo-toolboxes/issues/2) must account for retention: a digest reference alone cannot restore a registry-deleted image. |
| [COCKPIT_UPDATE_WORKFLOW.md](COCKPIT_UPDATE_WORKFLOW.md) | Cross-repository catalog synchronization instructions. | Continue catalog/README synchronization when backend identities change. |
| [docs/building.md](docs/building.md), [docs/vram-estimator.md](docs/vram-estimator.md), [docs/troubleshooting-firmware.md](docs/troubleshooting-firmware.md) | Build, memory-planning and troubleshooting references. | Keep operational docs aligned with implemented behavior and current backend-specific guidance. |

The estimator currently reads local files and assumes two bytes per KV element, with special sliding-window handling and a fixed adjustable overhead. It is a useful starting point, not yet the complete unified-memory planner.

## 2. Existing external Cockpit ownership

External repository: [kyuz0/ai-toolbox-cockpit](https://github.com/kyuz0/ai-toolbox-cockpit). The paths below belong there, not in this fork:

| External path | Existing responsibility |
| --- | --- |
| `ai_toolbox_cockpit/app.py` | Terminal shell, platform state, themes and update notice. |
| `ai_toolbox_cockpit/assets/toolboxes.json`, `models.json` | Curated images, capabilities, model/sidecar profiles. |
| `ai_toolbox_cockpit/catalog/` | Typed catalog loading and cross-reference validation. |
| `ai_toolbox_cockpit/runtime/` | Engines, interactive containers, registry and process lifecycle. |
| `ai_toolbox_cockpit/views/` | Toolboxes, Models and Server Mode surfaces. |
| `ai_toolbox_cockpit/backends/` | Backend-owned model semantics, validation and command generation. |

M1 owns the versioned integration design. No public stable runtime API is assumed. New Cockpit patches require a reviewed contribution or an explicitly adopted companion strategy. Avoid coupling new code to the older `src.*` campaign imports.

## 3. Proposed module boundaries — NOT IMPLEMENTED

These names are architectural responsibilities, not existing directories or guaranteed final filenames. M1 decides packaging and repository placement. Build PRs must replace proposed entries with actual paths as code lands.

| Proposed module | Responsibility and dependencies | Build ownership |
| --- | --- | --- |
| `recipes` | Versioned recipes, identities, migrations, validation, redacted import/export. | [#1](https://github.com/iannitram/amd-strix-halo-toolboxes/issues/1) |
| `updates` | Candidate/current/previous transaction, artifact retention, promotion and restoration. Uses recipes and runtime adapter. | [#2](https://github.com/iannitram/amd-strix-halo-toolboxes/issues/2) |
| `qualification` | Recorded readiness/inference/regression gates and reproduction export. Uses recipes/updates. | [#3](https://github.com/iannitram/amd-strix-halo-toolboxes/issues/3) |
| `planning` | Structured metadata/resource estimates, reserves, storage and alternatives. Adapts existing GGUF estimator. | [#4](https://github.com/iannitram/amd-strix-halo-toolboxes/issues/4) |
| `ui/planner` | Interactive pre-download memory/disk workbench. Consumes planning results. | [#5](https://github.com/iannitram/amd-strix-halo-toolboxes/issues/5) |
| `runtime_adapter`, `local_service` | Versioned Cockpit/backend boundary, operation/event API, auth/origin validation, cancellation. | [#6](https://github.com/iannitram/amd-strix-halo-toolboxes/issues/6) |
| `ui/mission_control` | Outcome journeys, status, advanced inspector and local test conversation. | [#7](https://github.com/iannitram/amd-strix-halo-toolboxes/issues/7) |
| `connections` | Client settings, bounded connection checks and optional stable endpoint. | [#8](https://github.com/iannitram/amd-strix-halo-toolboxes/issues/8) |
| `tournaments` | Budgeted isolated workloads, sampling, cleanup and versioned results. | [#9](https://github.com/iannitram/amd-strix-halo-toolboxes/issues/9) |
| `ui/comparisons` | Explained tradeoffs, curves/tables, recommendation/save/export. | [#10](https://github.com/iannitram/amd-strix-halo-toolboxes/issues/10) |
| `cluster/inventory` | Explicit node enrollment, trust, compatibility and measured links. | [#11](https://github.com/iannitram/amd-strix-halo-toolboxes/issues/11) |
| `cluster/placement` | Capacity/latency/concurrency alternatives constrained by backend support. | [#12](https://github.com/iannitram/amd-strix-halo-toolboxes/issues/12) |
| `cluster/sessions`, `ui/topology` | Session-owned RPC lifecycle, partial-failure cleanup and canvas/table. | [#13](https://github.com/iannitram/amd-strix-halo-toolboxes/issues/13) |

## 4. Intended data flow

```text
Cockpit TUI or proposed browser workspace
  -> versioned local service/runtime adapter
     -> catalog + backend-owned validation/command generation
     -> recipes -> resource planning -> explicit launch
     -> staged update -> qualification -> promotion / restoration
     -> bounded tournament -> evidence -> explained recipe choice
     -> enrolled nodes -> placement -> owned RPC session
  <- structured events, typed results, redacted diagnostics
```

The UI never constructs arbitrary shell commands. Recipes are typed data, not executable templates. Credentials stay in runtime secret handling outside recipe/result exports. Proposed services must not silently change boot parameters, fan profiles or networking.

## 5. Verification ownership

| Area | Default local evidence | Separate target-hardware evidence |
| --- | --- | --- |
| Recipes/update | Schema/migration/redaction tests; failure injection and mocked artifact retention. | Candidate inference qualification, rollback and model preservation. |
| Planner | Metadata/architecture fixtures, incomplete shards, unknown data and shared-memory accounting. | Estimate versus recorded allocations/host pressure. |
| Mission Control | Fake-runtime API contracts and browser state/accessibility journeys. | Real model readiness, conversation and client connection. |
| Tournament | Budget/comparability/sandbox/cancellation fixtures. | Repeated measured trials at recorded depths and exact build identities. |
| Cluster | Fake SSH nodes, identity/timeouts, placement and owned-process cleanup. | Two-node transport, capacity/latency and partial-failure validation. |

Default checks must not launch containers/GPUs, download weights or mutate the host. Record hardware evidence on the build issue; a command preview or successful build is not sufficient.
