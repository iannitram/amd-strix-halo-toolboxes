# Local AI workstation specification

Updated: 2026-11-01 (America/Denver).
Status: accepted product direction; proposed implementation.
Scope: my AMD Strix Halo toolbox fork and its explicitly defined Cockpit integration.

## 1. Problem and intended outcome

Users can already install accelerated containers and launch models with AI Toolbox Cockpit. They still need to determine suitable models/settings, establish that the host is ready, understand real workload performance, recover from regressions and operate multiple machines.

The product must connect those decisions into an understandable local workstation. Its five accepted capabilities are Mission Control, Will it fit?, Find my best setup, Time Machine and Combine my machines. [ROADMAP.md](ROADMAP.md) defines delivery priority; [CODE_MAP.md](CODE_MAP.md) separates existing source from planned modules.

## 2. Existing foundations and integration contract

Existing in this repository: backend Dockerfiles and build/poll workflows; manual refresh; local GGUF estimator; benchmark campaigns/results; an SSH/dialog llama.cpp RPC launcher; and the GPU workload watcher.

Existing externally: Cockpit terminal UI, backend-owned model catalogs, validation, runtime and command builders. The browser companion must use a narrow versioned adapter to those responsibilities. Do not copy launcher logic into a second source of truth or assume a general stable Cockpit API already exists.

M1 must record the adapter version, supported Cockpit version, dependency packaging and contribution/companion ownership before implementation depends on it. Backend differences remain explicit: GGUF, HF, sidecars, context, vision and distributed modes are not interchangeable.

## 3. Shared data contracts

All new persisted records require a schema version, stable ID, timestamps, provenance and explicit migration/error behavior.

| Contract | Required information |
| --- | --- |
| Recipe | OCI digest and optional display tag; engine/source revision; backend/platform; model revision and file identities; sidecars; typed launch settings; capability constraints; qualification reference. |
| Host snapshot | Host identity, hardware, OS/kernel, device visibility, memory/storage availability, sampling time and collection failures. |
| Resource plan | Model/shard completeness; weights/cache/runtime/desktop allocation; concurrency assumptions; disk/preparation/cache requirements; uncertainty and compatible alternatives. |
| Qualification | Exact recipe/host identities, checks and thresholds, measured results, passed/failed/unknown status, redacted diagnostics. |
| Benchmark run | Recipe/host IDs, workload version, depths, concurrency, cache/warmup state, repetitions, time budget, results, failures and optional energy provenance. |
| Cluster plan/session | Explicit enrolled nodes, identity verification, measured links, per-node placement/reserves, actual transport, owned process/container IDs, lifecycle and cleanup results. |

Credentials never belong in these records. Reproduction exports omit private prompts and personal paths by default; show a redacted preview before sharing. Missing historical artifacts must yield an actionable unavailable state.

## 4. Time Machine — R1/R2/R3

Requirements:
- Save named reproducible recipes, resolve tags to immutable image digests and bind model/sidecar identities.
- Stage candidate acquisition and creation while preserving the current working setup.
- Represent update states explicitly: resolving, pulling, staging, checking, candidate-ready, promoting, active, failed, restoring.
- Qualification records device access, complete model artifacts, readiness, a bounded inference smoke check and configurable regression comparisons.
- Promote only after required gates pass. Do not silently interrupt active requests; drain or defer the switch.
- Restore the prior recipe and retained image/configuration without modifying model files. If unavailable, explain the exact missing artifact.
- Retain active, previous and pinned artifacts; garbage collection follows an explicit policy.
- Support deterministic redacted export/import and migrations.

Acceptance: failed pull/create/check/promotion and interruption scenarios preserve or restore the working setup in failure-injection tests. Record target-host qualification separately. Rollback restores configuration/runtime selection, not conversation state or a historical host kernel.

## 5. Will it fit? — P1/P2

Requirements:
- Extend `toolboxes/gguf-vram-estimator.py` behind a structured API while preserving its CLI.
- Plan from model metadata before complete downloads where metadata is available.
- Account for weights, architecture-specific KV behavior, cache precision, runtime buffers, desktop reserve, context and server concurrency; avoid counting shared CPU/GPU memory twice.
- Include shard completeness, sidecars, download size, temporary preparation space, caches and existing reusable artifacts.
- The user can change context, quantization, slots and supported offload/streaming choices and immediately see an explained new plan.
- Label estimates, measured observations, stale data and unknown values distinctly.
- Suggest only backend-compatible alternatives when over budget; never turn absent metadata into a green fit result.
- Do not automatically tune the host, fetch large models or change engine settings.

Acceptance: architecture fixtures and real-host comparisons document estimation limits; incomplete shards and unsupported models are actionable states. Preserve input after errors. A plan is an estimate, not an allocation guarantee.

## 6. Mission Control — M1/M2/M3

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

Visual direction: functional developer-tool density with a calm primary workspace and an advanced inspector. Use system UI fonts, monospace for identifiers, a 4px spacing scale, 14–16px readable body text, 24px primary headings, 6px control radii and a restrained blue action accent. Light/dark tokens must meet 4.5:1 body-text and 3:1 UI/large-text contrast; status always has a text label. Provide visible focus, keyboard navigation, reduced motion and at least 44px primary touch targets. Browser layouts must work at 390px and desktop widths.

State coverage: loading, empty, populated, error, partial data, missing device, unknown telemetry and disconnected service. Errors preserve inputs and give a recovery action; long operations show actual progress and cancellation rather than an indefinite spinner.

Acceptance: mocked browser journeys verify first-run, recovery and accessible narrow/desktop layouts; a separate supported-host run reaches a real conversation and client connection.

## 7. Find my best setup — T1/T2

Requirements:
- User chooses workload, compatible candidate recipes and explicit time/resource budgets.
- Include coding, long-document and concurrent-serving presets, with warmup and repeated trials.
- Record time to first response, prefill/decode at relevant context depths, peak memory, errors and useful task completion. Energy is optional and unavailable when no reliable measurement exists.
- Executable coding evaluations use disposable restricted environments, never the user's live working tree. Network access and private-workload use are explicit.
- Respect cancellation/budgets, clean up owned jobs and restore the starting active recipe.
- Explain workload-specific tradeoffs using a frontier, curves and equivalent accessible tables; show variance, provenance and non-comparable conditions.
- Accepting a recommendation saves its exact recipe. Uploading results is opt-in with a preview; prompts remain local by default.

Acceptance: deterministic fixtures verify comparability, budgets and cleanup; recorded hardware runs reproduce the same identities and report uncertainty. No universal quality score or guaranteed speedup.

## 8. Combine my machines — C1/C2/C3

Requirements:
- Begin with existing llama.cpp RPC semantics. Enroll explicit SSH hosts with host-key verification; no automatic network scanning or trust.
- Inventory builds/devices, per-node memory/artifacts and measured links before launch.
- Compare a single host, supported RPC partitions and independent replicas for concurrency. Explain capacity gain and latency cost.
- Show placement and actual negotiated TCP/RDMA transport in a topology canvas plus accessible table.
- Validate all selected nodes before launch; represent node-specific loading, communication failure and cleanup state.
- Own remote processes/containers by session ID. Remove the legacy broad `pkill` cleanup behavior from the managed path; stop only owned resources.
- Handle partial startup, disconnect and cancellation with explicit cleanup/recovery.

Acceptance: fake-node tests cover mismatches, slow links, insufficient memory, timeouts and partial failure; record a two-node hardware run including a case where distribution is slower than local. Transparent failover and cross-engine memory pooling are outside the initial release.

## 9. Validation and release evidence

- Unit/contract tests: recipes, migrations/redaction, memory/metadata fixtures, backend capabilities and placement.
- Failure injection: update transactions, cancellation, restoration and session cleanup.
- Browser tests: outcome journeys, recovery, keyboard flow, narrow/desktop and light/dark states.
- Default local checks must not pull images, download weights, mutate host settings or start GPU/SSH workloads.
- Hardware qualification is an explicit separate run with recorded host/image/model identity and checks. Build success and command generation are insufficient.
- Preserve existing CLI workflows; document any migrations. Record evidence on the corresponding build issue before closing it.

## 10. Non-goals and unresolved implementation decisions

This update does not ship a new interface, run benchmarks, change host settings, publish images or modify upstream Cockpit. Implementation must decide its browser/service packaging and versioned Cockpit adapter under M1. Do not declare that proposed service/modules already exist. Boot tuning, closed-source engine qualification, NPU support and universal client compatibility are outside this initial scope.

### Licence status (owner ruling, 2026-11-01)

The upstream project, kyuz0/amd-strix-halo-toolboxes, has no licence file. The owner has asked upstream to add one: https://github.com/kyuz0/amd-strix-halo-toolboxes/issues/141. Until upstream answers, nothing from this repository is offered upstream or redistributed, including images, packages and release artefacts.

## 11. Build traceability

| Capability | Issues |
| --- | --- |
| Time Machine | [#1](https://github.com/iannitram/amd-strix-halo-toolboxes/issues/1), [#2](https://github.com/iannitram/amd-strix-halo-toolboxes/issues/2), [#3](https://github.com/iannitram/amd-strix-halo-toolboxes/issues/3) |
| Will it fit? | [#4](https://github.com/iannitram/amd-strix-halo-toolboxes/issues/4), [#5](https://github.com/iannitram/amd-strix-halo-toolboxes/issues/5) |
| Mission Control | [#6](https://github.com/iannitram/amd-strix-halo-toolboxes/issues/6), [#7](https://github.com/iannitram/amd-strix-halo-toolboxes/issues/7), [#8](https://github.com/iannitram/amd-strix-halo-toolboxes/issues/8) |
| Personal tournament | [#9](https://github.com/iannitram/amd-strix-halo-toolboxes/issues/9), [#10](https://github.com/iannitram/amd-strix-halo-toolboxes/issues/10) |
| Cluster composer | [#11](https://github.com/iannitram/amd-strix-halo-toolboxes/issues/11), [#12](https://github.com/iannitram/amd-strix-halo-toolboxes/issues/12), [#13](https://github.com/iannitram/amd-strix-halo-toolboxes/issues/13) |
