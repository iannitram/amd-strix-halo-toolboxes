# Spec: the local AI workstation

**1.0 means:** On a Strix Halo host running Linux, I open Mission Control in a browser (on the host, or on my Mac, Windows or Linux computer once I switch on LAN access), see whether a model fits before I download it, start a saved recipe and hold a real test conversation with it, connect a coding client to it, and update its toolbox in one step that I can undo when the new one is worse.

**Approved by me:** 2026-11-02, in the Project Manager session's question tool: "Adopt it, to Dev Loop (Recommended)" (the 2026-11-01 workstation plan is the spec), "First three are 1.0 (Recommended)" (1.0 is Time Machine, Will it fit? and Mission Control), "Linux host, any browser (Recommended)" and, for the prior art below, "Approve all 15 (Recommended)". Recorded in [CHANGELOG.fork.md](CHANGELOG.fork.md), 2026-11-02.

A project is Spec'd only when the line above has a date and a link. Change a Must or a Won't after approval and the approval line goes back to "not yet" until I approve again.

**Platforms (R04), in every part below:** the toolboxes, the local service and every host check run on a Strix Halo host running Linux (the containers need `/dev/kfd` and `/dev/dri`). The Mission Control page must work in current Chrome, Firefox, Safari and Edge on Mac, Windows and Linux. The pure Python modules (recipes, planning, qualification, redaction) are tested on all three in CI.

Updated: 2026-11-02 (America/Denver), from the 2026-11-01 plan.
Scope: my AMD Strix Halo toolbox fork and its explicitly defined Cockpit integration.

## Musts

Each Must is something a person can do and see. The `#` is the roadmap ID; each one has its own issue (see Build traceability), and each issue names the check that proves it.

| # | Must | Done looks like | Check |
|---|---|---|---|
| R1 | WHEN I save a working setup as a named recipe, THE APP SHALL store its exact image digest, engine revision, model files and launch settings, and export it without secrets, private prompts or home paths. | A recipe file I can export, import on another host and get back byte for byte; tags shown with their digest. | `tests/workstation/recipes/`; export, import, export again and compare. |
| R2 | WHEN I update a toolbox, THE APP SHALL stage the new one beside the working one, switch only after its checks pass, and let me restore the previous recipe in one step. | The old setup keeps running through a failed pull, create or check; Restore brings back the previous engine and settings with model files untouched. | Failure-injection tests in `tests/workstation/updates/`; one recorded rollback on the host. |
| R3 | WHEN a candidate recipe is checked, THE APP SHALL record passed, failed or unknown for device access, model completeness, readiness, a short inference test and a comparison with the current recipe. | A qualification record per recipe and host, and a redacted reproduction export. | `tests/workstation/qualification/`; one recorded host run. |
| P1 | WHEN I pick a model, context, cache type and number of users, THE APP SHALL estimate memory and disk before any download and say what it is unsure of. | A plan with weights, KV cache, runtime and desktop reserves, download and temporary space, each labelled estimated, measured, stale or unknown. | `tests/workstation/planning/` fixtures; estimates compared with recorded host use. |
| P2 | WHEN I change a setting on the Will it fit? page, THE APP SHALL show the new explained plan at once and offer only alternatives the backend supports. | The page updates on each change, keeps my input after an error, and never shows green when metadata is missing. | Browser tests on the planner page at 390 px and desktop widths. |
| M1 | WHEN the page asks the host to do something, THE APP SHALL go through one local service that binds to loopback, checks host, origin and CSRF token, and reports each operation as events I can cancel. | Requests from another site or host name are refused; long operations show progress and can be cancelled. | `tests/workstation/service/` against the fake runtime. |
| M2 | WHEN I open Mission Control, THE APP SHALL take me from choosing Code, Chat, Analyze images or Serve an API to a running recipe and a test conversation, with status always visible. | Active model, readiness, memory headroom and request activity on screen; an inspector with the real settings; every error has a recovery step. | Mocked browser journeys (first run, recovery, keyboard, light and dark); one recorded host run reaching a real conversation. |
| M3 | WHEN I connect a coding client, THE APP SHALL give me its settings and check that listing models and a short completion work. | Copyable snippets with no secrets in them; a check that passes or says what failed. | `tests/workstation/connections/`; one recorded client connection on the host. |

## Won'ts

Things 1.0 will not do, so nobody builds them by accident.

- **Find my best setup** (roadmap phase 4, T1/T2, issues #9 and #10): after 1.0, by my ruling of 2026-11-02 ("First three are 1.0 (Recommended)"). Labelled `after-1.0`.
- **Combine my machines** (roadmap phase 5, C1/C2/C3, issues #11 to #13): after 1.0, by the same ruling. Labelled `after-1.0`.
- No toolbox host other than Linux on Strix Halo: no Mac or Windows host, no other GPU.
- No automatic host tuning: no boot parameters, fan profiles, TuneD or network changes.
- No NPU support, no closed-source engines, no promise that every OpenAI client works.
- No new images, registry publication or upstream offers while upstream has no licence (Further notes).
- No change to upstream Cockpit; no copy of its code while it has no licence.
- No automatic model downloads or image pulls; each needs my click.

## Prior art

Projects doing the same thing, approved by me at Spec on 2026-11-02 ("Approve all 15 (Recommended)") and reviewed weekly. Their code comes in only when their license allows it, with credit; otherwise only their ideas. The ones with no licence file give ideas only: no code copied.

peer: kyuz0/ai-toolbox-cockpit | no licence file | the upstream we build on; its launch and monitoring UI is the base Mission Control grows from (ideas only until it has a licence)
peer: kyuz0/amd-strix-halo-toolboxes | no licence file | our fork's parent; track its gfx1151 Vulkan/ROCm image tags so Time Machine recipes can pin them
peer: mostlygeek/llama-swap | MIT | YAML model registry with hot-swap behind one OpenAI endpoint; closest model for recipes plus a launch/watch page
peer: gpustack/gguf-parser-go | MIT | estimates VRAM/RAM from GGUF headers without downloading the file: the core technique for Will it fit?
peer: gpustack/gpustack | Apache-2.0 | GPU cluster manager with resource-fit scheduling and a web dashboard
peer: lemonade-sdk/lemonade | Apache-2.0 | AMD's local LLM server for Ryzen AI with Vulkan/ROCm llama.cpp and a model manager UI: the nearest Strix Halo rival
peer: containers/ramalama | MIT | models as OCI artifacts in pinned GPU containers: prior art for recipes and rollback
peer: exo-explore/exo | Apache-2.0 | splits a model across machines with peer discovery; reference for post-1.0 clustering
peer: ggml-org/llama.cpp | MIT | the engine; rpc-server and llama-bench underlie clustering and tournaments
peer: b4rtaz/distributed-llama | MIT | tensor-parallel inference over Ethernet; network limits and setup UX of home clusters
peer: kyuz0/amd-strix-halo-vllm-toolboxes | no licence file | kyuz0's vLLM toolboxes for gfx1151: a second backend (ideas only)
peer: ollama/ollama | MIT | Modelfile and digest-pinned model store: reproducible recipes and simple pull-and-run
peer: janhq/jan | NOASSERTION | open LM Studio alternative with fit hints in its model hub: pick-and-launch UX
peer: cjpais/LocalScore | Apache-2.0 | standard local-LLM benchmark with a results board: template for tournaments
peer: kyuz0/pi-bench | no licence file | kyuz0's benchmark harness; likely start for tournaments (ideas only)

## Fork delta (R18)

Upstream ([kyuz0/amd-strix-halo-toolboxes](https://github.com/kyuz0/amd-strix-halo-toolboxes)) publishes no roadmap file; its plan is its image list in its README and its build workflows, which we take as they come. Our delta is everything in this spec:

| Delta | Where it goes |
| --- | --- |
| Time Machine (R1-R3) | keep on our fork |
| Will it fit? (P1-P2), including the structured API over `toolboxes/gguf-vram-estimator.py` | keep on our fork (the estimator's CLI stays as upstream has it) |
| Mission Control (M1-M3) | keep on our fork |
| Find my best setup, Combine my machines (after 1.0) | keep on our fork |

Nothing is marked "send upstream" while upstream has no licence; each later offer needs my yes.

## Problem

I can already install accelerated containers and launch models with AI Toolbox Cockpit. I still have to work out which models and settings suit the machine, whether the host is ready, how a setup really performs, and how to get back when an update makes things worse.

## Solution

One local workstation that ties those decisions together. Its five accepted capabilities are Mission Control, Will it fit?, Find my best setup, Time Machine and Combine my machines; the first three are 1.0. [ROADMAP.md](ROADMAP.md) gives the delivery order; [CODE_MAP.md](CODE_MAP.md) separates existing source from planned modules.

## User stories

1. As the owner of a Strix Halo host, I want to save a setup that works as a recipe, so that an update can never leave me without one.
2. As the owner, I want to try a new toolbox image beside the current one, so that I switch only when it is at least as good.
3. As the owner, I want to know whether a model fits before I download 100 GB of it, so that I do not waste the download.
4. As the owner, I want to open one page from whatever computer I am at and get from "I want to code" to a working model, so that I do not have to remember container commands.
5. As the owner, I want my coding client's settings handed to me and checked, so that connecting it is one copy and paste.

## Implementation decisions

### Existing foundations and integration contract

Existing in this repository: backend Dockerfiles and build/poll workflows; manual refresh; local GGUF estimator; benchmark campaigns/results; an SSH/dialog llama.cpp RPC launcher; and the GPU workload watcher.

Existing externally: Cockpit terminal UI, backend-owned model catalogs, validation, runtime and command builders. The browser companion must use a narrow versioned adapter to those responsibilities. Do not copy launcher logic into a second source of truth or assume a general stable Cockpit API already exists.

M1 must record the adapter version, supported Cockpit version, dependency packaging and contribution/companion ownership before implementation depends on it. Backend differences remain explicit: GGUF, HF, sidecars, context, vision and distributed modes are not interchangeable.

Packaging (Roadmap stage, 2026-11-02): the new code is the Python package `workstation/` (standard library only at runtime, Python 3.10+), served to the browser by its own local service as plain HTML, CSS and JavaScript with no build step. M1 still decides how it talks to Cockpit.

### Shared data contracts

All new persisted records require a schema version, stable ID, timestamps, provenance and explicit migration/error behavior.

| Contract | Required information |
| --- | --- |
| Recipe | OCI digest and optional display tag; engine/source revision; backend/platform; model revision and file identities; sidecars; typed launch settings; capability constraints; qualification reference. |
| Host snapshot | Host identity, hardware, OS/kernel, device visibility, memory/storage availability, sampling time and collection failures. |
| Resource plan | Model/shard completeness; weights/cache/runtime/desktop allocation; concurrency assumptions; disk/preparation/cache requirements; uncertainty and compatible alternatives. |
| Qualification | Exact recipe/host identities, checks and thresholds, measured results, passed/failed/unknown status, redacted diagnostics. |
| Benchmark run (after 1.0) | Recipe/host IDs, workload version, depths, concurrency, cache/warmup state, repetitions, time budget, results, failures and optional energy provenance. |
| Cluster plan/session (after 1.0) | Explicit enrolled nodes, identity verification, measured links, per-node placement/reserves, actual transport, owned process/container IDs, lifecycle and cleanup results. |

Credentials never belong in these records. Reproduction exports omit private prompts and personal paths by default; show a redacted preview before sharing. Missing historical artifacts must yield an actionable unavailable state.

### Time Machine (R1/R2/R3)

Platforms: host Linux (image pulls, toolbox creation and checks); recipe files and exports are plain JSON, read the same on Mac, Windows and Linux.

- Save named reproducible recipes, resolve tags to immutable image digests and bind model/sidecar identities.
- Stage candidate acquisition and creation while preserving the current working setup.
- Represent update states explicitly: resolving, pulling, staging, checking, candidate-ready, promoting, active, failed, restoring.
- Qualification records device access, complete model artifacts, readiness, a bounded inference smoke check and configurable regression comparisons.
- Promote only after required gates pass. Do not silently interrupt active requests; drain or defer the switch.
- Restore the prior recipe and retained image/configuration without modifying model files. If unavailable, explain the exact missing artifact.
- Retain active, previous and pinned artifacts; garbage collection follows an explicit policy.
- Support deterministic redacted export/import and migrations.

Acceptance: failed pull/create/check/promotion and interruption scenarios preserve or restore the working setup in failure-injection tests. Record target-host qualification separately. Rollback restores configuration/runtime selection, not conversation state or a historical host kernel.

### Will it fit? (P1/P2)

Platforms: the planner is pure Python and runs on Mac, Windows and Linux; host measurements (free memory, free disk, devices) come from the Linux host; the page works in any browser on all three.

- Extend `toolboxes/gguf-vram-estimator.py` behind a structured API while preserving its CLI.
- Plan from model metadata before complete downloads where metadata is available.
- Account for weights, architecture-specific KV behavior, cache precision, runtime buffers, desktop reserve, context and server concurrency; avoid counting shared CPU/GPU memory twice.
- Include shard completeness, sidecars, download size, temporary preparation space, caches and existing reusable artifacts.
- The user can change context, quantization, slots and supported offload/streaming choices and immediately see an explained new plan.
- Label estimates, measured observations, stale data and unknown values distinctly.
- Suggest only backend-compatible alternatives when over budget; never turn absent metadata into a green fit result.
- Do not automatically tune the host, fetch large models or change engine settings.

Acceptance: architecture fixtures and real-host comparisons document estimation limits; incomplete shards and unsupported models are actionable states. Preserve input after errors. A plan is an estimate, not an allocation guarantee.

### Mission Control (M1/M2/M3)

Platforms: the local service runs on the Linux host; the page must work in current Chrome, Firefox, Safari and Edge on Mac, Windows and Linux, at 390 px and desktop widths. Reaching it from another computer is LAN serving, which is off by default and switched on explicitly.

Primary journey:
1. Choose Code, Chat, Analyze images or Serve an API.
2. Inspect detected host readiness and compatible model/engine suggestions.
3. Review the resource/download plan and explicitly accept required operations.
4. Start a named recipe and observe real loading/readiness progress.
5. Complete a local test conversation or verified client connection.

Workspace requirements:
- Persistent active-model, server-readiness, memory-headroom and request-activity summaries.
- Advanced inspector exposes actual backend settings and redacted command details.
- A built-in bounded test conversation verifies useful connectivity.
- Connection panel provides endpoint/model settings and redacted client snippets, checks model listing and completion, and offers an opt-in stable endpoint adapter.
- Unsupported vision/tool-use/API behavior is visible instead of implied compatibility.
- Local control service uses structured operations/events, cancellation, operation IDs and recoverable stale/disconnected states.
- Bind to loopback by default; authenticated lifecycle operations validate origin/host and protect against CSRF and DNS rebinding. LAN serving is explicit and separately configured.

Visual direction: functional developer-tool density with a calm primary workspace and an advanced inspector. Use system UI fonts, monospace for identifiers, a 4px spacing scale, 14–16px readable body text, 24px primary headings, 6px control radii and a restrained blue action accent. Light/dark tokens must meet 4.5:1 body-text and 3:1 UI/large-text contrast; status always has a text label. Provide visible focus, keyboard navigation, reduced motion and at least 44px primary touch targets. Browser layouts must work at 390px and desktop widths. The design pass before 1.0 (ROADMAP.md stage 6) aligns these tokens with the design system shared by all my apps.

State coverage: loading, empty, populated, error, partial data, missing device, unknown telemetry and disconnected service. Errors preserve inputs and give a recovery action; long operations show actual progress and cancellation rather than an indefinite spinner.

Acceptance: mocked browser journeys verify first-run, recovery and accessible narrow/desktop layouts; a separate supported-host run reaches a real conversation and client connection.

### After 1.0: Find my best setup (T1/T2)

Kept for when 1.0 ships; not built now (Won'ts).

- User chooses workload, compatible candidate recipes and explicit time/resource budgets.
- Include coding, long-document and concurrent-serving presets, with warmup and repeated trials.
- Record time to first response, prefill/decode at relevant context depths, peak memory, errors and useful task completion. Energy is optional and unavailable when no reliable measurement exists.
- Executable coding evaluations use disposable restricted environments, never the user's live working tree. Network access and private-workload use are explicit.
- Respect cancellation/budgets, clean up owned jobs and restore the starting active recipe.
- Explain workload-specific tradeoffs using a frontier, curves and equivalent accessible tables; show variance, provenance and non-comparable conditions.
- Accepting a recommendation saves its exact recipe. Uploading results is opt-in with a preview; prompts remain local by default.

Acceptance: deterministic fixtures verify comparability, budgets and cleanup; recorded hardware runs reproduce the same identities and report uncertainty. No universal quality score or guaranteed speedup.

### After 1.0: Combine my machines (C1/C2/C3)

Kept for when 1.0 ships; not built now (Won'ts).

- Begin with existing llama.cpp RPC semantics. Enroll explicit SSH hosts with host-key verification; no automatic network scanning or trust.
- Inventory builds/devices, per-node memory/artifacts and measured links before launch.
- Compare a single host, supported RPC partitions and independent replicas for concurrency. Explain capacity gain and latency cost.
- Show placement and actual negotiated TCP/RDMA transport in a topology canvas plus accessible table.
- Validate all selected nodes before launch; represent node-specific loading, communication failure and cleanup state.
- Own remote processes/containers by session ID. Remove the legacy broad `pkill` cleanup behavior from the managed path; stop only owned resources.
- Handle partial startup, disconnect and cancellation with explicit cleanup/recovery.

Acceptance: fake-node tests cover mismatches, slow links, insufficient memory, timeouts and partial failure; record a two-node hardware run including a case where distribution is slower than local. Transparent failover and cross-engine memory pooling are outside the initial release.

## Testing decisions

- Unit/contract tests: recipes, migrations/redaction, memory/metadata fixtures, backend capabilities and placement. They live in `tests/workstation/`, run with pytest, and go through each module's public functions.
- Failure injection: update transactions, cancellation, restoration and session cleanup, against the fake runtime.
- Browser tests: outcome journeys, recovery, keyboard flow, narrow/desktop and light/dark states, in Chromium, Firefox and WebKit.
- Default local checks must not pull images, download weights, mutate host settings or start GPU/SSH workloads.
- Hardware qualification is an explicit separate run with recorded host/image/model identity and checks. Build success and command generation are insufficient.
- Preserve existing CLI workflows; document any migrations. Record evidence on the corresponding build issue before closing it.

## Further notes

This plan ships no interface yet, runs no benchmarks, changes no host settings, publishes no images and modifies no upstream Cockpit. Do not declare that proposed service/modules already exist. Boot tuning, closed-source engine qualification, NPU support and universal client compatibility are outside 1.0.

### Licence status (owner ruling, 2026-11-01)

The upstream project, kyuz0/amd-strix-halo-toolboxes, has no licence file. I have asked upstream to add one: https://github.com/kyuz0/amd-strix-halo-toolboxes/issues/141. Until upstream answers, nothing from this repository is offered upstream or redistributed, including images, packages and release artefacts.

## Build traceability

| Capability | Issues |
| --- | --- |
| Time Machine | [#1](https://github.com/iannitram/amd-strix-halo-toolboxes/issues/1), [#2](https://github.com/iannitram/amd-strix-halo-toolboxes/issues/2), [#3](https://github.com/iannitram/amd-strix-halo-toolboxes/issues/3) |
| Will it fit? | [#4](https://github.com/iannitram/amd-strix-halo-toolboxes/issues/4), [#5](https://github.com/iannitram/amd-strix-halo-toolboxes/issues/5) |
| Mission Control | [#6](https://github.com/iannitram/amd-strix-halo-toolboxes/issues/6), [#7](https://github.com/iannitram/amd-strix-halo-toolboxes/issues/7), [#8](https://github.com/iannitram/amd-strix-halo-toolboxes/issues/8) |
| Find my best setup (after 1.0) | [#9](https://github.com/iannitram/amd-strix-halo-toolboxes/issues/9), [#10](https://github.com/iannitram/amd-strix-halo-toolboxes/issues/10) |
| Combine my machines (after 1.0) | [#11](https://github.com/iannitram/amd-strix-halo-toolboxes/issues/11), [#12](https://github.com/iannitram/amd-strix-halo-toolboxes/issues/12), [#13](https://github.com/iannitram/amd-strix-halo-toolboxes/issues/13) |

The smaller pieces each Must is split into are listed per roadmap ID in ROADMAP.md, Build register.
