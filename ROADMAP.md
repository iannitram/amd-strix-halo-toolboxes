# Workstation roadmap

Updated: 2026-11-02 (America/Denver). Stage: Dev Loop. Spec: [SPEC.md](SPEC.md). Code map: [CODE_MAP.md](CODE_MAP.md). Issues: [https://github.com/iannitram/amd-strix-halo-toolboxes/issues](https://github.com/iannitram/amd-strix-halo-toolboxes/issues).

Evolve the Strix Halo toolbox collection into a local AI workstation that helps people choose, run, measure and trust their setup. The existing container and CLI workflows stay as upstream has them; everything new lives in `workstation/` (CODE_MAP.md, section 3).

## Platforms (R04)

| Part | Mac | Windows | Linux |
| --- | --- | --- | --- |
| Toolboxes, podman runtime, host snapshot, update CLI, host run | no (needs a Strix Halo host) | no | yes, the only host |
| Pure modules: recipes, planning, qualification, redaction, service checks, snippets | tested in CI | tested in CI | tested in CI |
| Local service with the fake runtime | runs and is tested in CI | runs and is tested in CI | runs and is tested in CI |
| Mission Control page | Safari (WebKit), Chrome, Firefox, Edge | Chrome, Firefox, Edge | Chrome, Firefox |

The page reaches the host over loopback, or over the LAN once I switch LAN access on (#6). CI runs on GitHub-hosted runners: `.github/workflows/workstation-ci.yml`.

## Feature list (1.0)

| Feature | Musts | What I can do |
| --- | --- | --- |
| Time Machine | R1, R2, R3 | Save a setup as a recipe, export it without secrets, update a toolbox in one step and undo it. |
| Will it fit? | P1, P2 | See memory and disk needs, and how sure the numbers are, before any download. |
| Mission Control | M1, M2, M3 | Pick a journey, reach a running recipe and a test conversation, connect a coding client. |

After 1.0 (ruling of 2026-11-02, "First three are 1.0 (Recommended)"): Find my best setup (T1, T2: [#9](https://github.com/iannitram/amd-strix-halo-toolboxes/issues/9), [#10](https://github.com/iannitram/amd-strix-halo-toolboxes/issues/10)) and Combine my machines (C1 to C3: [#11](https://github.com/iannitram/amd-strix-halo-toolboxes/issues/11), [#12](https://github.com/iannitram/amd-strix-halo-toolboxes/issues/12), [#13](https://github.com/iannitram/amd-strix-halo-toolboxes/issues/13)).

## Dev stages

| Stage | What | Issues | Gate |
| --- | --- | --- | --- |
| 1 | Foundations: pure functions and the fake runtime | [#15](https://github.com/iannitram/amd-strix-halo-toolboxes/issues/15), [#16](https://github.com/iannitram/amd-strix-halo-toolboxes/issues/16), [#17](https://github.com/iannitram/amd-strix-halo-toolboxes/issues/17), [#18](https://github.com/iannitram/amd-strix-halo-toolboxes/issues/18), [#20](https://github.com/iannitram/amd-strix-halo-toolboxes/issues/20), [#21](https://github.com/iannitram/amd-strix-halo-toolboxes/issues/21), [#25](https://github.com/iannitram/amd-strix-halo-toolboxes/issues/25), [#26](https://github.com/iannitram/amd-strix-halo-toolboxes/issues/26), [#27](https://github.com/iannitram/amd-strix-halo-toolboxes/issues/27), [#28](https://github.com/iannitram/amd-strix-halo-toolboxes/issues/28), [#29](https://github.com/iannitram/amd-strix-halo-toolboxes/issues/29), [#35](https://github.com/iannitram/amd-strix-halo-toolboxes/issues/35), [#36](https://github.com/iannitram/amd-strix-halo-toolboxes/issues/36), [#43](https://github.com/iannitram/amd-strix-halo-toolboxes/issues/43), [#22](https://github.com/iannitram/amd-strix-halo-toolboxes/issues/22), [#33](https://github.com/iannitram/amd-strix-halo-toolboxes/issues/33) | All locked tests green on Mac, Windows and Linux CI; ADR #33 decided. |
| 2 | Time Machine core | [#19](https://github.com/iannitram/amd-strix-halo-toolboxes/issues/19), [#1](https://github.com/iannitram/amd-strix-halo-toolboxes/issues/1), [#23](https://github.com/iannitram/amd-strix-halo-toolboxes/issues/23), [#2](https://github.com/iannitram/amd-strix-halo-toolboxes/issues/2), [#32](https://github.com/iannitram/amd-strix-halo-toolboxes/issues/32), [#3](https://github.com/iannitram/amd-strix-halo-toolboxes/issues/3) | Failure injection shows a failed candidate never breaks the working recipe; restore works against the fake runtime. |
| 3 | Will it fit? core | [#30](https://github.com/iannitram/amd-strix-halo-toolboxes/issues/30), [#31](https://github.com/iannitram/amd-strix-halo-toolboxes/issues/31), [#4](https://github.com/iannitram/amd-strix-halo-toolboxes/issues/4) | Plans from fixtures match hand-worked numbers; missing data is always labelled unknown. |
| 4 | Mission Control: service and pages | [#6](https://github.com/iannitram/amd-strix-halo-toolboxes/issues/6), [#37](https://github.com/iannitram/amd-strix-halo-toolboxes/issues/37), [#38](https://github.com/iannitram/amd-strix-halo-toolboxes/issues/38), [#39](https://github.com/iannitram/amd-strix-halo-toolboxes/issues/39), [#40](https://github.com/iannitram/amd-strix-halo-toolboxes/issues/40), [#41](https://github.com/iannitram/amd-strix-halo-toolboxes/issues/41), [#42](https://github.com/iannitram/amd-strix-halo-toolboxes/issues/42), [#44](https://github.com/iannitram/amd-strix-halo-toolboxes/issues/44), [#45](https://github.com/iannitram/amd-strix-halo-toolboxes/issues/45), [#5](https://github.com/iannitram/amd-strix-halo-toolboxes/issues/5), [#46](https://github.com/iannitram/amd-strix-halo-toolboxes/issues/46), [#7](https://github.com/iannitram/amd-strix-halo-toolboxes/issues/7), [#8](https://github.com/iannitram/amd-strix-halo-toolboxes/issues/8) | Browser journeys pass in Chromium, Firefox and WebKit on Mac, Windows and Linux CI against the fake runtime. |
| 5 | On the host: real runtime and the 1.0 run | [#34](https://github.com/iannitram/amd-strix-halo-toolboxes/issues/34), [#24](https://github.com/iannitram/amd-strix-halo-toolboxes/issues/24), [#47](https://github.com/iannitram/amd-strix-halo-toolboxes/issues/47) | The recorded host run (#47) reaches a real conversation, a client connection, an update and a restore. |
| 6 | Design pass | none yet | Last stage, after everything above is built and merged: one design pass on every page with the shared design system (the pipeline repo's design-pass rule). No issue yet; it is filed when stage 5 closes. |

Within a stage, any issue whose `Blocked by` lines are closed can be built; stages are an order of release, not a lock.

## Build register

Parent issues ([#1](https://github.com/iannitram/amd-strix-halo-toolboxes/issues/1) to [#8](https://github.com/iannitram/amd-strix-halo-toolboxes/issues/8)) hold each Must; the smaller issues are the pieces it is split into. Each Easy issue carries a Qwen brief and its locked tests.

| ID | Issue | Size | Kind | Platforms | Blocked by | Status |
| --- | --- | --- | --- | --- | --- | --- |
| R1 | [#15](https://github.com/iannitram/amd-strix-halo-toolboxes/issues/15) redact secrets, private prompts and home paths | Easy | pure-fn | Mac, Windows, Linux | nothing | Planned |
| R1 | [#16](https://github.com/iannitram/amd-strix-halo-toolboxes/issues/16) deterministic recipe identity | Easy | pure-fn | Mac, Windows, Linux | nothing | Planned |
| R1 | [#17](https://github.com/iannitram/amd-strix-halo-toolboxes/issues/17) recipe schema validation | Easy | data-shape | Mac, Windows, Linux | nothing | Planned |
| R1 | [#18](https://github.com/iannitram/amd-strix-halo-toolboxes/issues/18) recipe export and import | Easy | data-shape | Mac, Windows, Linux | #15, #16, #17 | Planned |
| R2 | [#20](https://github.com/iannitram/amd-strix-halo-toolboxes/issues/20) update state machine | Easy | state | Mac, Windows, Linux | nothing | Planned |
| R2 | [#21](https://github.com/iannitram/amd-strix-halo-toolboxes/issues/21) artifact retention plan | Easy | pure-fn | Mac, Windows, Linux | nothing | Planned |
| R3 | [#25](https://github.com/iannitram/amd-strix-halo-toolboxes/issues/25) qualification decision | Easy | pure-fn | Mac, Windows, Linux | nothing | Planned |
| R3 | [#26](https://github.com/iannitram/amd-strix-halo-toolboxes/issues/26) compare a candidate with the current recipe | Easy | pure-fn | Mac, Windows, Linux | nothing | Planned |
| P1 | [#27](https://github.com/iannitram/amd-strix-halo-toolboxes/issues/27) KV cache size and unified-memory plan | Easy | pure-fn | Mac, Windows, Linux | nothing | Planned |
| P1 | [#28](https://github.com/iannitram/amd-strix-halo-toolboxes/issues/28) shard completeness and disk plan | Easy | pure-fn | Mac, Windows, Linux | nothing | Planned |
| P1 | [#29](https://github.com/iannitram/amd-strix-halo-toolboxes/issues/29) estimated, measured, stale or unknown labels | Easy | pure-fn | Mac, Windows, Linux | nothing | Planned |
| M1 | [#35](https://github.com/iannitram/amd-strix-halo-toolboxes/issues/35) host, origin and CSRF checks | Easy | pure-fn | Mac, Windows, Linux | nothing | Planned |
| M1 | [#36](https://github.com/iannitram/amd-strix-halo-toolboxes/issues/36) operation registry with progress and cancel | Easy | state | Mac, Windows, Linux | nothing | Planned |
| M3 | [#43](https://github.com/iannitram/amd-strix-halo-toolboxes/issues/43) client settings snippets | Easy | pure-fn | Mac, Windows, Linux | nothing | Planned |
| R2 | [#22](https://github.com/iannitram/amd-strix-halo-toolboxes/issues/22) fake runtime for tests | Medium | state | Mac, Windows, Linux | nothing | Planned |
| M1 | [#33](https://github.com/iannitram/amd-strix-halo-toolboxes/issues/33) decide how we talk to Cockpit (ADR) | Medium | docs | Mac, Windows, Linux | nothing | Planned |
| R1 | [#19](https://github.com/iannitram/amd-strix-halo-toolboxes/issues/19) resolve image tags to digests | Medium | wiring | Mac, Windows, Linux | nothing | Planned |
| R1 | [#1](https://github.com/iannitram/amd-strix-halo-toolboxes/issues/1) recipe store and schema migrations | Medium | state | Mac, Windows, Linux | #17, #18 | Planned |
| R2 | [#23](https://github.com/iannitram/amd-strix-halo-toolboxes/issues/23) drain requests before a switch | Medium | state | Mac, Windows, Linux | #22 | Planned |
| R2 | [#2](https://github.com/iannitram/amd-strix-halo-toolboxes/issues/2) update transaction with one-step restore | Medium | state | Mac, Windows, Linux | #1, #20, #21, #22 | Planned |
| R3 | [#32](https://github.com/iannitram/amd-strix-halo-toolboxes/issues/32) host snapshot | Medium | data-shape | Linux | nothing | Planned |
| R3 | [#3](https://github.com/iannitram/amd-strix-halo-toolboxes/issues/3) qualification runner and reproduction manifest | Medium | wiring | Mac, Windows, Linux | #25, #26, #22, #32, #15 | Planned |
| P1 | [#30](https://github.com/iannitram/amd-strix-halo-toolboxes/issues/30) structured metadata from local GGUF files | Medium | data-shape | Mac, Windows, Linux | nothing | Planned |
| P1 | [#31](https://github.com/iannitram/amd-strix-halo-toolboxes/issues/31) metadata before download | Medium | data-shape | Mac, Windows, Linux | #30 | Planned |
| P1 | [#4](https://github.com/iannitram/amd-strix-halo-toolboxes/issues/4) planner and supported alternatives | Medium | pure-fn | Mac, Windows, Linux | #27, #28, #29, #30 | Implemented (fixture tests; host evidence: #47) |
| M1 | [#6](https://github.com/iannitram/amd-strix-halo-toolboxes/issues/6) local service | Medium | wiring | Mac, Windows, Linux | #35, #36, #22 | Built with fake-runtime tests; Mac/Windows CI pending |
| M1 | [#37](https://github.com/iannitram/amd-strix-halo-toolboxes/issues/37) service routes for recipes, plans and updates | Medium | wiring | Mac, Windows, Linux | #6, #1, #2, #4 | Planned |
| M2 | [#38](https://github.com/iannitram/amd-strix-halo-toolboxes/issues/38) page shell, tokens and state components | Medium | ui | Mac, Windows, Linux | #6 | Planned |
| M2 | [#39](https://github.com/iannitram/amd-strix-halo-toolboxes/issues/39) browser test harness | Medium | wiring | Mac, Windows, Linux | #38 | Planned |
| M2 | [#40](https://github.com/iannitram/amd-strix-halo-toolboxes/issues/40) status summaries | Medium | ui | Mac, Windows, Linux | #38, #37 | Planned |
| M2 | [#41](https://github.com/iannitram/amd-strix-halo-toolboxes/issues/41) settings inspector | Medium | ui | Mac, Windows, Linux | #38, #37 | Planned |
| M2 | [#42](https://github.com/iannitram/amd-strix-halo-toolboxes/issues/42) test conversation | Medium | ui | Mac, Windows, Linux | #38, #37 | Planned |
| M3 | [#44](https://github.com/iannitram/amd-strix-halo-toolboxes/issues/44) connection check | Medium | wiring | Mac, Windows, Linux | nothing | Planned |
| M3 | [#45](https://github.com/iannitram/amd-strix-halo-toolboxes/issues/45) stable local endpoint | Hard | wiring | Mac, Windows, Linux | #6 | Planned |
| P2 | [#5](https://github.com/iannitram/amd-strix-halo-toolboxes/issues/5) Will it fit? planner page | Medium | ui | Mac, Windows, Linux | #4, #38, #37 | Planned |
| R2 | [#46](https://github.com/iannitram/amd-strix-halo-toolboxes/issues/46) Time Machine page | Medium | ui | Mac, Windows, Linux | #38, #37 | Planned |
| M2 | [#7](https://github.com/iannitram/amd-strix-halo-toolboxes/issues/7) Mission Control journeys page | Medium | ui | Mac, Windows, Linux | #38, #37, #5, #40 | Planned |
| M3 | [#8](https://github.com/iannitram/amd-strix-halo-toolboxes/issues/8) connect panel | Medium | ui | Mac, Windows, Linux | #43, #44, #38, #37 | Planned |
| M1 | [#34](https://github.com/iannitram/amd-strix-halo-toolboxes/issues/34) podman runtime on the host | Hard | wiring | Linux | #33, #22 | Planned |
| R2 | [#24](https://github.com/iannitram/amd-strix-halo-toolboxes/issues/24) update command line | Medium | wiring | Linux | #2, #34 | Planned |
| 1.0 | [#47](https://github.com/iannitram/amd-strix-halo-toolboxes/issues/47) recorded run on the Strix Halo host | Medium | docs | Linux | #7, #8, #46, #34, #3 | Planned |
| T1 | [#9](https://github.com/iannitram/amd-strix-halo-toolboxes/issues/9) Run bounded, private workload comparison tournaments | Hard | pure-fn | Linux | 1.0 | After 1.0 |
| T2 | [#10](https://github.com/iannitram/amd-strix-halo-toolboxes/issues/10) Explain workload tradeoffs and save the winning setup | Hard | ui | Mac, Windows, Linux | 1.0 | After 1.0 |
| C1 | [#11](https://github.com/iannitram/amd-strix-halo-toolboxes/issues/11) Enroll cluster nodes and measure transport readiness | Hard | wiring | Linux | 1.0 | After 1.0 |
| C2 | [#12](https://github.com/iannitram/amd-strix-halo-toolboxes/issues/12) Plan model placement across machines with latency tradeoffs | Hard | pure-fn | Linux | 1.0 | After 1.0 |
| C3 | [#13](https://github.com/iannitram/amd-strix-halo-toolboxes/issues/13) Build a cluster topology canvas and session-scoped lifecycle | Hard | ui | Mac, Windows, Linux | 1.0 | After 1.0 |

## Interlinks

```text
redact (#15) ─┬─> recipes/io (#18) ─> recipes/store (#1) ─> updates/transaction (#2) ─> service routes (#37)
identity (#16)┤                                ^                      ^    ^
schema (#17) ─┘                  digests (#19) ┘   states (#20), retention (#21), drain (#23)
fake runtime (#22) ─> transaction (#2), drain (#23), qualification (#3), service (#6)
gates (#25) + compare (#26) + host snapshot (#32) ─> qualification (#3) ─> Time Machine page (#46)
memory (#27) + disk (#28) + labels (#29) + gguf_meta (#30) + remote_meta (#31) ─> planner (#4) ─> Will it fit? page (#5)
security (#35) + operations (#36) ─> service (#6) ─> routes (#37) ─> page shell (#38) ─> pages (#5, #7, #8, #40, #41, #42, #46)
snippets (#43) + check (#44) ─> connect panel (#8);  stable endpoint (#45) <─ service (#6)
ADR (#33) ─> podman runtime (#34) ─> update CLI (#24), host run (#47)
```

## Open-source candidates

Licensed peers from SPEC.md, Prior art, and what each may give. Code comes in only under its licence, with credit; the peers with no licence file give ideas only.

| Candidate | Licence | Use | Issues |
| --- | --- | --- | --- |
| gpustack/gguf-parser-go | MIT | Technique for reading GGUF headers by range request before download. | #30, #31 |
| mostlygeek/llama-swap | MIT | How one stable OpenAI endpoint forwards to a swapped backend. | #45 |
| containers/ramalama | MIT | Models and engines pinned by OCI digest. | #19, #2 |
| ollama/ollama | MIT | Digest-pinned model store and pull-and-run flow. | #1, #19 |
| ggml-org/llama.cpp | MIT | llama-server health, `/v1/models` and timings used by checks. | #3, #44 |
| lemonade-sdk/lemonade | Apache-2.0 | Model manager page patterns for Strix Halo. | #7 |
| gpustack/gpustack | Apache-2.0 | Resource-fit explanations on a dashboard. | #4, #5 |
| Playwright | Apache-2.0 | Browser tests in Chromium, Firefox and WebKit (dev only). | #39 |
| pytest, ruff | MIT | Tests and lint (dev only). | all |
| kyuz0/ai-toolbox-cockpit, kyuz0/pi-bench, kyuz0/amd-strix-halo-vllm-toolboxes | none | Ideas only, no code. | #33 |

The runtime itself uses Python's standard library only, so nothing above ships with it unless a later issue says so.

## Ownership and boundaries

- This fork owns `workstation/`, `tests/workstation/`, `pyproject.toml` and `.github/workflows/workstation-ci.yml`; upstream owns everything else (AGENTS.fork.md).
- Cockpit is a separate project with no licence: ideas only, and the boundary is decided in #33 before #34 starts.
- No container builds, registry publication, host tuning or upstream posts are part of this roadmap.
- Default tests never start containers, use the GPU, download weights or change the host; host evidence goes on #47.

## Risks to retire

1. A moving image tag is not a reproducible recipe; registry retention can still delete an old digest (#19, #21).
2. Unified-memory fit depends on architecture, context, concurrent use and host pressure (#27, #4).
3. Benchmark ranking depends on workload, cache state and repetitions; no universal model score is promised (after 1.0).
4. Distributed capacity may improve while single-request latency worsens (after 1.0).
5. Existing campaign tooling imports older Cockpit `src.*` modules; the new code does not (#33).
