# Workstation roadmap

Updated: 2026-11-01 (America/Denver). Product direction accepted by me; implementation has not started.

## Product direction

Evolve the Strix Halo toolbox collection into a complete local AI workstation that helps people choose, run, measure and trust their setup. Preserve the existing container/CLI workflows and build on AI Toolbox Cockpit instead of duplicating its backend command builders.

This is the planning source for `iannitram/amd-strix-halo-toolboxes`. The fork had no roadmap, spec or code map when this plan was adopted. These documents initialize that baseline; they do not describe already shipped features.

- [Product and technical requirements](SPEC.md)
- [Current code inventory and proposed ownership](CODE_MAP.md)
- [Build issue tracker](https://github.com/iannitram/amd-strix-halo-toolboxes/issues)

## Delivery sequence and release gates

| Phase | Initiative | Build issues | Release gate |
| --- | --- | --- | --- |
| 1 | Time Machine: reproducible recipes and reversible updates | [#1](https://github.com/iannitram/amd-strix-halo-toolboxes/issues/1), [#2](https://github.com/iannitram/amd-strix-halo-toolboxes/issues/2), [#3](https://github.com/iannitram/amd-strix-halo-toolboxes/issues/3) | Candidate failures preserve the current setup; qualified promotion and rollback demonstrated on target hardware. |
| 2 | Will it fit?: memory and storage workbench | [#4](https://github.com/iannitram/amd-strix-halo-toolboxes/issues/4), [#5](https://github.com/iannitram/amd-strix-halo-toolboxes/issues/5) | Explain fit, uncertainty and alternatives before downloading; compare estimates with recorded target-host observations. |
| 3 | Mission Control: outcome-first local workspace | [#6](https://github.com/iannitram/amd-strix-halo-toolboxes/issues/6), [#7](https://github.com/iannitram/amd-strix-halo-toolboxes/issues/7), [#8](https://github.com/iannitram/amd-strix-halo-toolboxes/issues/8) | A supported first-run journey reaches a verified conversation and client connection; browser control API passes boundary tests. |
| 4 | Find my best setup: personal workload tournament | [#9](https://github.com/iannitram/amd-strix-halo-toolboxes/issues/9), [#10](https://github.com/iannitram/amd-strix-halo-toolboxes/issues/10) | Bounded, repeatable comparisons explain useful-work, latency and resource tradeoffs and restore the starting setup. |
| 5 | Combine my machines: visual cluster composer | [#11](https://github.com/iannitram/amd-strix-halo-toolboxes/issues/11), [#12](https://github.com/iannitram/amd-strix-halo-toolboxes/issues/12), [#13](https://github.com/iannitram/amd-strix-halo-toolboxes/issues/13) | Two-node llama.cpp RPC qualification demonstrates placement, actual transport and session-scoped cleanup. |

The phase order expresses release priority, not artificial blocking. Build contracts can overlap once their issue dependencies are satisfied. No dates or performance promises are committed.

## Build register

| ID | Issue | Depends on | Status |
| --- | --- | --- | --- |
| R1 | [#1](https://github.com/iannitram/amd-strix-halo-toolboxes/issues/1) Define versioned, reproducible workstation recipes | None | Planned |
| R2 | [#2](https://github.com/iannitram/amd-strix-halo-toolboxes/issues/2) Stage toolbox updates and restore the last working recipe | [#1](https://github.com/iannitram/amd-strix-halo-toolboxes/issues/1) | Planned |
| R3 | [#3](https://github.com/iannitram/amd-strix-halo-toolboxes/issues/3) Qualify candidate recipes and export reproduction evidence | [#1](https://github.com/iannitram/amd-strix-halo-toolboxes/issues/1), [#2](https://github.com/iannitram/amd-strix-halo-toolboxes/issues/2) | Planned |
| P1 | [#4](https://github.com/iannitram/amd-strix-halo-toolboxes/issues/4) Implement unified-memory and storage planning contracts | [#1](https://github.com/iannitram/amd-strix-halo-toolboxes/issues/1) | Planned |
| P2 | [#5](https://github.com/iannitram/amd-strix-halo-toolboxes/issues/5) Add an interactive model-fit and download planning workbench | [#4](https://github.com/iannitram/amd-strix-halo-toolboxes/issues/4) | Planned |
| M1 | [#6](https://github.com/iannitram/amd-strix-halo-toolboxes/issues/6) Add a local workstation service and Cockpit integration boundary | [#1](https://github.com/iannitram/amd-strix-halo-toolboxes/issues/1), [#4](https://github.com/iannitram/amd-strix-halo-toolboxes/issues/4) | Planned |
| M2 | [#7](https://github.com/iannitram/amd-strix-halo-toolboxes/issues/7) Build an outcome-first Mission Control workspace | [#6](https://github.com/iannitram/amd-strix-halo-toolboxes/issues/6), [#5](https://github.com/iannitram/amd-strix-halo-toolboxes/issues/5), [#3](https://github.com/iannitram/amd-strix-halo-toolboxes/issues/3) | Planned |
| M3 | [#8](https://github.com/iannitram/amd-strix-halo-toolboxes/issues/8) Connect coding clients and expose a verified local API endpoint | [#6](https://github.com/iannitram/amd-strix-halo-toolboxes/issues/6), [#7](https://github.com/iannitram/amd-strix-halo-toolboxes/issues/7) | Planned |
| T1 | [#9](https://github.com/iannitram/amd-strix-halo-toolboxes/issues/9) Run bounded, private workload comparison tournaments | [#3](https://github.com/iannitram/amd-strix-halo-toolboxes/issues/3), [#4](https://github.com/iannitram/amd-strix-halo-toolboxes/issues/4), [#6](https://github.com/iannitram/amd-strix-halo-toolboxes/issues/6) | Planned |
| T2 | [#10](https://github.com/iannitram/amd-strix-halo-toolboxes/issues/10) Explain workload tradeoffs and save the winning setup | [#9](https://github.com/iannitram/amd-strix-halo-toolboxes/issues/9), [#7](https://github.com/iannitram/amd-strix-halo-toolboxes/issues/7) | Planned |
| C1 | [#11](https://github.com/iannitram/amd-strix-halo-toolboxes/issues/11) Enroll cluster nodes and measure transport readiness | [#1](https://github.com/iannitram/amd-strix-halo-toolboxes/issues/1), [#6](https://github.com/iannitram/amd-strix-halo-toolboxes/issues/6) | Planned |
| C2 | [#12](https://github.com/iannitram/amd-strix-halo-toolboxes/issues/12) Plan model placement across machines with latency tradeoffs | [#11](https://github.com/iannitram/amd-strix-halo-toolboxes/issues/11), [#4](https://github.com/iannitram/amd-strix-halo-toolboxes/issues/4), [#9](https://github.com/iannitram/amd-strix-halo-toolboxes/issues/9) | Planned |
| C3 | [#13](https://github.com/iannitram/amd-strix-halo-toolboxes/issues/13) Build a cluster topology canvas and session-scoped lifecycle | [#12](https://github.com/iannitram/amd-strix-halo-toolboxes/issues/12), [#7](https://github.com/iannitram/amd-strix-halo-toolboxes/issues/7) | Planned |

Each issue contains build scope, acceptance criteria and verification expectations. Close an issue only when its criteria are met and evidence is linked; passing mocked tests does not establish GPU compatibility.

## Ownership and boundaries

- This fork owns its recipes, lifecycle integration, planner, benchmark adapters and llama.cpp RPC integration.
- Cockpit is a separate project at [kyuz0/ai-toolbox-cockpit](https://github.com/kyuz0/ai-toolbox-cockpit). Its current model management, profiles and server launching are existing foundations, not new milestones here.
- M1 must select and document a versioned adapter/contribution strategy before relying on Cockpit internals. Work requiring upstream changes remains a cross-repository dependency until a reviewed contribution or explicit companion strategy exists.
- Start with llama.cpp on Strix Halo; expose other engines only through backend-owned capabilities and qualification evidence.
- No container builds, registry publication, host tuning or inference execution are part of this planning update.

## Risks to retire

1. A moving image tag is not a reproducible recipe; registry retention can still make an old digest unavailable.
2. Unified-memory fit depends on architecture, context, concurrent use and host pressure.
3. Benchmark ranking depends on workload, cache state and repetitions; no universal model score is promised.
4. Distributed capacity may improve while single-request latency worsens.
5. Existing campaign tooling imports older Cockpit `src.*` modules; verify the integration version before reuse.
