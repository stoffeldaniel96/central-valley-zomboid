# ADR-003: Standalone map and optional terrain integrations
Status: accepted product requirement; implementation pending (user clarification 2026-11-26).

The mapping toolchain and base playable map must build and operate without Viewpoint or Better Terrain, directly or transitively (including ZombieBuddy solely for those integrations). Full Viewpoint compatibility remains an acceptance requirement, not a player installation requirement. Research into Better Terrain does not approve a mandatory dependency, a fork, or copying its implementation.

Canonical signed elevations, planar foundations, surfaces, independent decks/subsurface spaces, material/mechanical semantics and stable assets remain renderer-independent. Third-party formats are adapter outputs, never authoritative inputs. Model-first volumetric asset generation continues per asset-contract.md.

## Runtime configurations
- Native base: no Viewpoint or Better Terrain. Use native slopes, levels and reusable assets first; a project-owned runtime extension is only justified by demonstrated gaps and must work without those third-party mods.
- Viewpoint alone: identical base geography with compatible model/texture/state bindings; Better Terrain not required.
- Viewpoint + Better Terrain: optional adapter if a supported, version-compatible provider or data format is available. One physical elevation authority, no double-applied relief, no modifying upstream installation or silent fallback to standard Kentucky terrain. Disable unsupported integration explicitly, preserving base behavior.

## Acceptance
Test actual Turlock benchmarks in native-only, Viewpoint-only and supported combined configurations, on pinned builds and fresh saves. Compare slopes, negative Z, foundations, access, deck clearance, collisions and traversal. Visual fidelity may differ; mechanically meaningful geography must remain functional. Document measurable backend differences; do not silently flatten important features. Flat control is a format-loading experiment, not terrain parity. Native arbitrary slope support, Better Terrain custom provider and multiplayer behavior are unverified. No new dependency approved.
