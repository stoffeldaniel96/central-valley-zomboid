# Architecture — target, not implemented
Immutable source snapshots → multi-source reconciliation → authoritative observed geography → constrained sanitization → continuous-coordinate semantic graybox → functional validation → backend-specific rendering/compilation → graphical polish and final validation.

## Geography
Keep fixed local azimuthal equidistant projection anchored at downtown Turlock; x east, y south, signed global cells and half-open bounds. Existing 16-cell sector IDs and regional envelope remain intact for expansion. Engine translation provisional; freeze before production. Statewide projection distortion and engine coordinate ranges require evaluation. Do not silently rescale or reproject existing content.

OSM is evidence, not truth. Combine appropriately licensed aerial imagery (e.g. NAIP), LiDAR/3DEP, municipal GIS, independently collected reference material and OSM. Track per-property source, timestamp, license, confidence, observation/inference and discrepancies. Dated Geofabrik PBF preferred for regional acquisition. Preserve original observations and derived corrections separately; manual overrides survive regeneration. No extraction of restricted third-party meshes or imagery.

## Geometry
Continuous meters are authoritative. Native simulation grid nominally 1 m; 256-tile B42 cells are a target assumption pending backend verification. Octilinear structural geometry (45° increments) is the initial target, not an assertion of supported engine collision. Arbitrary-angle structural geometry is not baseline scope. Terrain, markings, curves and low-physics-impact details may retain arbitrary angles. Adaptive subtiles at 25 cm initially, 12.5 cm or finer where warranted; no globally dense subgrid. Preserve exact vector boundaries until backend sampling. Distinguish rendering and physical geometry; do not conceal collision mismatches.

Sanitize only when meaningful topology and geographic fidelity survive. Fit connected road/property/building groups with shared vertices and fixed anchors; compare every change to original geometry, not prior snapped results. Trial displacement budgets 1–2 m buildings/local roads, 3 m rural roads; not approved thresholds. Reject topology violations and excessive drift; flag unresolved areas. Heatmaps must report angle, displacement, source disagreement/completeness, semantic uncertainty, asset/engine complexity and generated-output fidelity.

## Semantic world model
Stable feature IDs; spatial geometry, dimensions, elevation, materials, construction, function, openings, collision, visibility, interaction states, room membership, source provenance and uncertainty. Graybox is authoritative; appearance is separate. Schema and persistence format TBD. Deterministic generation with pinned versions, seeds and source hashes. Asset registry: primitives (walls, planes, columns), assemblies (storefronts, ramps), archetypes (housing, shops, barns); parameterized and reusable. AI may interpret references, propose compositions, identify missing capability and generate code; validate deterministically. Use original or properly licensed assets; inventory local vanilla art without redistribution.

## Backends
Prefer native map formats and custom tiles/model-to-sprite rendering. Investigate reusable transitions, geometric masks, atlas deduplication and procedural 3D, with actual performance/storage limits. Optional runtime 3D or core module only if justified. Engine tests cover movement, zombie navigation, visibility, room detection, lighting, combat, doors/windows, construction/destruction and multiplayer compatibility as applicable. Compile through replaceable adapter; never let a backend dictate the semantic world model. KnoxMap optional, see ADR-001.

## Engineering boundaries
No claim of playable production generator, diagonal collision, arbitrary-angle rendering or seamless sector compilation yet. Existing geographic scripts remain experimental. Start with small verified benchmark locations, not city-scale mass generation.
