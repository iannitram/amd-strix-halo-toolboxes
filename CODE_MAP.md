# Code map

Updated: 2026-11-02 (America/Denver).
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

## 3. Module map

The `workstation/` package (Python 3.10+, standard library only at run time) and its tests. Every stub raises `NotImplementedError("TODO #N")` with its issue number; the skeleton test imports them all, so `python -m pytest -q` runs green from day one. Status is `present` (done), `partial`, `stub` (signature only) or `planned` (no file yet). Build PRs update this table as code lands.

| Path | Responsibility | ID | Issue | Status | Platforms |
| --- | --- | --- | --- | --- | --- |
| `workstation/__init__.py` | Package marker and `__version__`. | - | - | present | Mac, Windows, Linux |
| `workstation/errors.py` | `WorkstationError`, `RecipeError(errors)`, `InvalidTransition`, `Refused`. | - | - | present | Mac, Windows, Linux |
| `workstation/runtime/port.py` | `RuntimePort` protocol: devices, pull, create, remove, start_server, stop_server, health, active_requests, list_models, complete. | M1 | #22, #34 | present | Mac, Windows, Linux |
| `workstation/__main__.py` | `python -m workstation`: `--help` works; `serve` (#6) and `update`/`restore` (#24) to come. | M1, R2 | #6, #24 | partial | Mac, Windows, Linux (update: Linux) |
| `workstation/recipes/migrate.py` | Schema migration steps up to `SCHEMA_VERSION`. | R1 | #1 | stub | Mac, Windows, Linux |
| `workstation/recipes/store.py` | Recipe files under a data folder: save, load, load_by_name, list. | R1 | #1 | stub | Mac, Windows, Linux |
| `workstation/updates/transaction.py` | Stage, promote and restore. | R2 | #2 | stub | Mac, Windows, Linux |
| `workstation/qualification/runner.py` | Run the checks and decide. | R3 | #3 | stub | Mac, Windows, Linux |
| `workstation/qualification/manifest.py` | Redacted reproduction manifest. | R3 | #3 | stub | Mac, Windows, Linux |
| `workstation/planning/planner.py` | One explained plan and supported alternatives. | P1 | #4 | stub | Mac, Windows, Linux |
| `workstation/service/app.py` | Local HTTP service, page and JSON API. | M1 | #6, #37, #42 | stub | Mac, Windows, Linux |
| `workstation/web/` | Mission Control page: `index.html`, `styles.css`, `app.js`, no build step. | M2, P2, M3, R2 | #38, #5, #7, #8, #40, #41, #42, #46 | stub | browsers on Mac, Windows, Linux |
| `tests/workstation/test_skeleton.py` | Imports every module, checks the page files and the estimator CLI. | - | - | present | Mac, Windows, Linux |
| `workstation/redact.py` | A pure function that returns a copy of any JSON-like data with credentials, private prompts and personal home paths taken out. Recipe export, manifests and copied diagnostics all use it. | R1 | #15 | stub | Mac, Windows, Linux |
| `workstation/recipes/identity.py` | A stable recipe ID worked out from what the recipe runs, so the same setup always gets the same ID on any host. | R1 | #16 | stub | Mac, Windows, Linux |
| `workstation/recipes/schema.py` | Check a recipe against schema version 1 and list every problem in a fixed order. | R1 | #17 | stub | Mac, Windows, Linux |
| `workstation/recipes/io.py` | Export a recipe as fixed, redacted JSON text and import it back with every check, so a recipe can move between hosts byte for byte. | R1 | #18 | stub | Mac, Windows, Linux |
| `workstation/recipes/digests.py` | Turn an image tag into its exact digest by asking the registry, so a recipe never stores a moving tag alone. | R1 | #19 | present | Mac, Windows, Linux |
| `workstation/updates/states.py` | The table of update states and the moves allowed between them, used by the update transaction. | R2 | #20 | stub | Mac, Windows, Linux |
| `workstation/updates/retention.py` | Decide which old images may be removed, never the active, previous or pinned ones. | R2 | #21 | stub | Mac, Windows, Linux |
| `workstation/runtime/fake.py` | An in-memory `RuntimePort` that every default test uses instead of podman, with failures you can switch on per step. | R2 | #22 | present | Mac, Windows, Linux |
| `workstation/updates/drain.py` | Wait until a server has no requests in flight, with a timeout, before the update switches it off. | R2 | #23 | stub | Mac, Windows, Linux |
| `workstation/qualification/gates.py` | Turn the list of check results into one decision: passed, failed or unqualified. | R3 | #25 | stub | Mac, Windows, Linux |
| `workstation/qualification/compare.py` | Compare the candidate's load time, time to first token and speeds with the current recipe's, against a threshold per metric. | R3 | #26 | stub | Mac, Windows, Linux |
| `workstation/planning/memory.py` | Work out the KV cache size for a model and context, and add it to weights and reserves against the one shared memory total. | P1 | #27 | stub | Mac, Windows, Linux |
| `workstation/planning/disk.py` | Spot missing pieces of a split model and work out the download, temporary and cache space against free disk. | P1 | #28 | stub | Mac, Windows, Linux |
| `workstation/planning/labels.py` | Label each number the planner shows, so the page can say how sure it is. | P1 | #29 | stub | Mac, Windows, Linux |
| `workstation/planning/gguf_meta.py` | Read a local GGUF file's architecture, layer, head and size metadata as a dict, reusing `toolboxes/gguf-vram-estimator.py` without changing its command line. | P1 | #30 | present | Mac, Windows, Linux |
| `workstation/planning/remote_meta.py` | Read a remote GGUF file's header with HTTP range requests, so Will it fit? can answer before anything is downloaded. | P1 | #31 | stub | Mac, Windows, Linux |
| `workstation/host/snapshot.py` | Record the host facts that matter for a recipe: kernel, firmware, GPU device nodes, memory total and free, disk free, and toolbox and podman versions. | R3 | #32 | present | Linux |
| `workstation/runtime/podman.py` | The real `RuntimePort`: pull images, create and remove toolbox containers, start and stop llama-server, and read its health, with `/dev/kfd` and `/dev/dri` passed through. | M1 | #34 | stub | Linux |
| `workstation/service/security.py` | Check each request's Host, Origin, Sec-Fetch-Site and CSRF token, so another web site or host name cannot drive the service. | M1 | #35 | stub | Mac, Windows, Linux |
| `workstation/service/operations.py` | Keep each long job's id, state, progress and events, and let the page cancel it. | M1 | #36 | stub | Mac, Windows, Linux |
| `workstation/web/index.html` | The page shell every view sits in: navigation, colour and spacing tokens for light and dark, and shared loading, empty, error and success states. No build step. | M2 | #38 | stub | Mac, Windows, Linux |
| `workstation/connections/snippets.py` | Copyable env, curl and Python settings for a coding client, with the key's variable name and never its value. | M3 | #43 | stub | Mac, Windows, Linux |
| `workstation/connections/check.py` | Check that a client can list models and get a short completion from the endpoint, and say which step failed. | M3 | #44 | present | Mac, Windows, Linux |
| `workstation/connections/endpoint.py` | One fixed local port that always forwards to whichever recipe is active, so a client keeps its settings across updates. | M3 | #45 | stub | Mac, Windows, Linux |
| `docs/adr/0001-cockpit-boundary.md` | Cockpit boundary decision. | M1 | #33 | planned | - |
| `tests/browser/` | Playwright journeys in Chromium, Firefox and WebKit. | M2 | #39 | planned | Mac, Windows, Linux |
| `docs/workstation/host-runs/` | Dated records of host runs. | 1.0 | #47 | planned | Linux |

Tests mirror the package: `tests/workstation/<area>/test_<module>.py`. Prove it with `python -m pytest -q` and `python -m ruff check workstation tests`; CI runs both on ubuntu, windows and macos.

After 1.0, not mapped yet: tournaments (#9, #10) and cluster (#11 to #13).

## 4. Intended data flow

```text
Cockpit TUI or the Mission Control page (workstation/web)
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
