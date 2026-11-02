# ADR 0001: Cockpit boundary

**Status: Proposed, needs the owner's decision**

## Context

Mission Control is planned to run through the workstation's local service and `RuntimePort` on the Linux Strix Halo host. `RuntimePort` exists as a protocol; the local service, the Podman adapter and the Mission Control page are not built yet (CODE_MAP lists them as stubs). The spec also assigns the toolbox catalog, backend validation and command generation to Cockpit, but the repository records no public stable runtime API and says Cockpit has no licence. The workstation runtime and its recipes must remain testable without a Cockpit process.

## Options

1. **Drive Cockpit.** Automate its interface or depend on its internal modules. This couples host operations to an interface or implementation that this repository does not identify as a stable contract.
2. **Call Podman through `RuntimePort`.** Let the workstation service own lifecycle operations through its runtime port. Define and version the catalog, validation and command-building boundary needed by the workstation, without importing Cockpit code.
3. **Wait for an agreed Cockpit integration.** Do not implement the real runtime until Cockpit offers a supported contract or the owner approves a companion integration strategy.

## Decision

Recommend option 2 for container and server lifecycle: the service calls Podman via `RuntimePort`, and Mission Control does not drive Cockpit's UI or private internals. Cockpit's launch-and-monitor workflow and curated toolbox selection are ideas only; this ADR copies no Cockpit code or text.

This also means workstation-owned catalog and backend command semantics would replace responsibilities the spec currently assigns to Cockpit. That changes the documented integration boundary. Therefore this ADR is **proposed**, not accepted, and #34 must wait for the owner to decide whether that standalone boundary is acceptable or whether implementation must wait for an agreed Cockpit/companion contract.

## Toolbox name compatibility

Keep toolbox identities and image references compatible with the names already recorded for Cockpit: retain the `strix-halo-llama-<backend>-<version>` ID form (for example, `strix-halo-llama-rocm-10-0`) and the corresponding image tag (for example, `rocm-10.0`). Treat the stable ID, full image reference and resolved digest as separate recipe data; a display-name or tag change must not silently create a new identity or rewrite an existing recipe. When toolbox entries change, follow `COCKPIT_UPDATE_WORKFLOW.md`'s inventory and synchronization guidance. This is a compatibility convention, not a Cockpit API dependency.

## Consequences

- Runtime lifecycle remains behind the `RuntimePort`; default checks can use its fake implementation, while the real adapter is Linux-only.
- A versioned workstation-owned catalog/command contract and backend-specific validation would need to be specified before implementation. Cockpit does not become a dependency or source of executable code.
- Cockpit catalog changes are not automatic. If coordinated updates are later authorized, the existing toolbox update workflow describes the names and surfaces to keep aligned.

## Revisit when

Revisit if Cockpit publishes a licensed, stable, documented runtime/catalog contract; the owner approves a companion integration with an explicit version and ownership model; or the workstation cannot preserve required backend behavior and toolbox identity through its own adapter. Any change to the accepted spec requires the owner's approval.
