# ADR 0001: Cockpit boundary

**Status: Accepted (owner's decision, 2026-11-02): drive Cockpit through a narrow adapter**

## Context

Mission Control is planned to run through the workstation's local service on the Linux Strix Halo host. `RuntimePort` exists as a protocol; the local service, the runtime adapters and the Mission Control page are not built yet (CODE_MAP lists them as stubs). SPEC.md gives the toolbox catalog, backend validation, runtime and command building to Cockpit, and says the browser companion must reach those through a narrow versioned adapter, without copying launcher logic into a second source of truth. Cockpit has no licence file and no published stable API. The workstation and its recipes must stay testable without a Cockpit process.

## Options

1. **Drive Cockpit.** The workstation calls Cockpit's own catalog, validation and command builders, and lets it launch toolboxes.
2. **Call Podman through `RuntimePort`.** The workstation owns its own catalog and command building, and Cockpit is used for ideas only.
3. **Wait for an agreed Cockpit integration.** Build no real runtime until Cockpit offers a supported contract.

## Decision

Option 1. The owner chose to drive Cockpit. Cockpit stays the single source of truth for the toolbox catalog, backend validation and launch commands, as SPEC.md already says.

How it is done:

- **One adapter.** All Cockpit access goes through one workstation port (a `CockpitPort` beside `RuntimePort`). The real adapter is the only code that knows Cockpit's module names, catalog file or command-line surface. Everything else sees plain data: the catalog entries, a validation result, and a command to run.
- **No copied code.** Cockpit has no licence, so its code is never copied, vendored or redistributed here (SPEC.md: "no copy of its code while it has no licence"). The adapter calls a Cockpit the user has installed separately. It does not bundle one.
- **Ideas only.** The one thing we take from Cockpit is the idea of its launch-and-monitor UI, which SPEC.md names as the base Mission Control grows from. No Cockpit code, text, layout or assets are copied, and the page is written from scratch.
- **Pinned version.** The adapter records the adapter version and the Cockpit version it supports. On any other Cockpit version it reports "unsupported Cockpit version" and does not guess.
- **Testable without Cockpit.** Default tests use a fake `CockpitPort`. Tests of the real adapter are Linux-only and opt-in.
- **No upstream changes.** Cockpit is not modified. If the adapter needs something Cockpit does not offer, that becomes an issue for the owner to raise upstream, not a patch.

## Toolbox name compatibility

Keep the `strix-halo-llama-<backend>-<version>` ID form (for example, `strix-halo-llama-rocm-10-0`) and the matching image tag (for example, `rocm-10.0`). The stable ID, full image reference and resolved digest are separate recipe data. A display-name or tag change must not quietly create a new identity or rewrite an existing recipe. When toolbox entries change, follow `COCKPIT_UPDATE_WORKFLOW.md`.

## Consequences

- #34 can start. It builds the `CockpitPort` interface, a fake, and the real adapter for one pinned Cockpit version.
- Cockpit's internals are not a stable contract, so a Cockpit update can break the adapter. The version pin turns that into a clear "unsupported version" error, not wrong behaviour. Moving to a new Cockpit version is a deliberate adapter update.
- M1 must still record, before depending on it: the adapter version, the supported Cockpit version, how Cockpit is installed (separately, by the user), and who owns the companion (SPEC.md, M1).
- Backend differences stay explicit (GGUF, HF, sidecars, context, vision, distributed). The adapter passes them through and does not merge them.

## Revisit when

Revisit if Cockpit adds a licence (copying or deeper integration may then be allowed), publishes a stable API (switch the adapter to it), or changes often enough that keeping the adapter working costs more than option 2.
