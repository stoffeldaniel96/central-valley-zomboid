# Project charter
Status: adopted architectural direction, 2026-11-26.

Central Valley is the overarching map family and reusable world-generation technology. Turlock is the first finished product and development laboratory. Deliver fidelity before coverage, automation before repetitive hand authoring. Preserve modern geography at nominal 1 meter per native ground tile, with 1993 material culture. The final visual minimum is comparable to Google Earth 3D; aim to exceed it through clean architecture, functional interiors, accurate infrastructure and gameplay. This is a target, not a demonstrated capability.

## Physical-first production
AI operates like a level designer: interpret evidence, compose dimensionally accurate grayboxes, assign semantic construction/material/interaction properties, flag missing primitives and uncertainty. Gameplay-relevant geometry, access, collision, rooms, elevation and period-sensitive objects belong in the functional graybox. Graphical finish can follow without replacing the authoritative physical representation. Unknown interiors are plausible inference, not claims about actual private buildings or occupants.

Observe recurring architectural forms in appropriately licensed references; identify missing expressive capabilities; author reusable primitives, assemblies and archetypes. Prefer parameter changes and compositions over bespoke assets; unique landmarks may warrant dedicated assets. This is vocabulary expansion, not extraction of Google meshes/textures or automated reconstruction from restricted Google data. Google Earth is a quality benchmark; verify permissions for any actual use of third-party imagery and derived content.

## Compatibility
Prefer native engine and custom assets first, then external generators and supported mod interfaces. If fidelity/functional requirements cannot be met, evaluate a separate geometry/rendering/simulation core or narrowly scoped engine modifications. Record evidence, compatibility/version cost and fallback for each escalation. No requirement to use KnoxMap, Viewpoint, native sprites or an unchanged engine. Preserve native gameplay wherever practical.

## Fidelity
Measure geographic, physical, functional, architectural, environmental, infrastructural, period and graphical fidelity separately. A visually accurate but physically broken feature fails functional acceptance. Do not silently reduce fidelity to accommodate a compiler. Use reference uncertainty, source rights and explicit review status; do not claim exactness where evidence is missing.

## Chronology and vertical fidelity
Use modern 2026 geography, a provisional pre-2008 institutional/commercial reference cutoff, and 1993 material culture. These are independent layers, not a historically exact single year or a fixed outbreak date. Track anachronisms in institutions, population, infrastructure, economic functions and materials; retain modern geometry unless explicitly overridden. Terrain elevation, grades, embankments, bridges and vertically overlapping routes are physical fidelity requirements. Prefer interoperable shared extensions over a private engine fork.

## Least mechanical intervention and source corroboration
Maximize fidelity where it has minimal mechanical impact. Prefer continuous visual ground geometry with native point/coverage-sampled physical classifications where safe. Raised curbs, water barriers, steep slopes and other physical exceptions require actual gameplay tests. Reconcile evidence per property before sanitizing geometry; no source is globally authoritative. Maintain immutable snapshots and record corrections separately from representational compromises. Rendering detail is not evidence of measurement accuracy.
