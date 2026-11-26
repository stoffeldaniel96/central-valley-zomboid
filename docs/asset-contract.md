# Dual-renderer asset contract (design requirement)
Central Valley is model-first for volumetric objects. Full Viewpoint compatibility is required; Viewpoint installation is not mandatory for native isometric play. A backend-specific limitation cannot silently change authoritative geometry. Exact runtime integration remains unverified.

## Asset identity
Stable family/variant/state IDs shared across both backends. Source primitive or assembly, meter dimensions, local origin and axes, orientations, material slots, attachment sockets, interaction/collision/visibility semantics, state transitions, and provenance. Explicit distinction between visually represented geometry and native mechanical proxy. No duplicate independent authoring of equivalent sprites and models.

## Compilation
- Flat material surfaces and truly planar decals: common material and planar geometry; native sprites/overlays and Viewpoint texture/decal representation. No unnecessary volumetric object model.
- Volumetric objects, including raised curbs and rails where relevant: original reusable 3D source; native color sprite, baked depth, and tile definitions; Viewpoint-compatible mesh, textures and tile binding. Model/UV conventions validated against installed renderer. No assumptions that an OBJ supplies collision.
- Stateful doors, windows, damage and other variants: matching state IDs, geometry/texture outputs and behavior; optional LODs must not change physical identity.
- Buildings are composed of reusable assemblies. Singular landmarks may use specialized geometry but still need both outputs where applicable.
- Native square grid remains 1 m; arbitrary visual orientations and exact continuous geometry retained until backend compilation.

## Reuse gate
Every non-singular generated sprite with fewer than 10 intended or actual placements is flagged for review. Record family, state, orientation, placement counts, potential regional reuse, geometric error, mechanical equivalence and rationale for exceptions. Review rare required states separately from accidental one-off geometry; do not erase necessary functionality to meet threshold. Do not collapse geometries with different mechanical semantics. No map-coordinate-keyed bespoke assets as normal practice. Unique landmarks explicitly classified. Favor finite reusable vocabulary and quantization within measured tolerances; regional demand analysis before expanding the catalog. No arbitrary threshold override disguised as landmark.

## Acceptance tests
For every relevant new family: reproducible shared source; native sprite/depth renders and corresponding Viewpoint model; consistent origin, dimensions and orientation; state parity; native collision and interaction tests; Viewpoint visual verification; placement report. Track unverified capability and exceptions, do not mark release-ready until tested. T01/T02/T05 fixtures should be generated from same source; flat-surface test need not invent 3D geometry.
