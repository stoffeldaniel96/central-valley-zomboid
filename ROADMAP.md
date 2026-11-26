# Roadmap — fidelity first
Supersedes coverage-first plan. First product is Turlock, not Modesto–Merced. No geographic expansion until the Turlock pipeline meets acceptance gates.

## Current baseline
- [x] Regional coordinate index and 2 km downtown pilot.
- [x] KnoxMap preset generator and compiler wrapper (external, unverified execution).
- [x] User generated terrain and building previews; geographic and architectural discrepancies observed.
- [ ] Archive Baseline 001: version, preset, source dates, output hashes, preview, compilation/game results if available.
- [ ] Establish Turlock release boundary with surrounding rural transition.
- [ ] Georeference benchmark intersection from screenshots; exact extent TBD.

## R&D work packages
| ID | Work | First deliverable / exit test |
|---|---|---|
| 01 | Geographic sanitization | Constrained octilinear snapping with shared topology and original-reference displacement tests |
| 02 | Eight-direction structures | One enclosed diagonal room; collision, visibility, pathfinding and openings tested in game |
| 03 | Complexity analysis | Real orientation histograms and spatial heatmaps; raw vs sanitized results |
| 04 | Asset inventory | Local vanilla catalog of families, orientations, states and properties; measured missing variants; AI/procedural production trial |
| 05 | Arbitrary-angle surfaces | Parking lot, markings and curves with continuous visual boundaries |
| 06 | Model-first / 3D | Shared model-first asset sources; native sprite/depth plus required Viewpoint compatibility |
| 07 | Source reconciliation | Georeferenced OSM + independent licensed imagery/elevation; provenance, disagreement and completeness metrics |
| 08 | Adaptive resolution | Subtile rasterizer, deduplication and atlas/memory benchmarks; physical implications tested separately |
| 09 | Architectural vocabulary | Graybox primitive/assembly/archetype registry, coverage audit, reusable gap-filling workflow |

## Delivery gates
G0: independently inspect source data and inventory native assets. G1: reproduce a small intersection with accurate continuous terrain; document reference uncertainty. G2: diagonal room and native compiler compatibility experiments. G3: benchmark residential, commercial, institutional, industrial and rural environments with functional grayboxes. G4: complete Turlock physical/functional graybox with no unresolved critical gameplay failures. G5: graphical/material/1993 finish and fidelity validation; first public product. G6: expand using proven tools and assets.

Parallel research is encouraged; gates are evidence-based, not deadlines. No fabricated coverage percentages or engine capability claims. See docs/benchmarks.md.

## Additional R&D
| ID | Work | First deliverable / exit test |
|---|---|---|
| 10 | Vertical geometry | DEM and independently elevated route model; embankment and bridge benchmark with physical traversal |
| 11 | Chronology reconciliation | 2026 geography / pre-2008 institutional reference / 1993 material culture discrepancy register |
| 12 | Ecosystem interoperability | Versioned native and Viewpoint compatibility acceptance tests; investigate shared interfaces and upstream plans |

G0 implementation begins with read-only local asset and OSM geometry diagnostics. Their output is evidence, not a completed semantic reconstruction. See docs/first-deliverable.md.

## G0 pilot follow-up
- [x] User verified acquisition and orientation analysis (29,322 raw segments, no missing node references, nine omitted relations).
- [x] Implement default clipping to pilot extent; local/CI regression run pending.
- [ ] Acquire independently dated aerial reference and inspect co-registration.
- [ ] Identify actual benchmark intersection and compare OSM against independent evidence.
- [ ] Record reviewed source corrections before attempting sanitization or ground sprite generation.
- [ ] Render continuous corrected terrain with sampled native physical properties; test exceptions.

- [x] Implement Overture building evidence overlay and heuristic overlap/coverage candidate classification (local acquisition and testing pending).
- [ ] Review candidate footprints against dated NAIP and independent sources; implement explicit acceptance/addition workflow and source-specific lineage checks.

- [x] Add editable subtype legend, transport reference acquisition and preliminary vector/image discrepancy diagnostics (implementation; live verification pending).
- [ ] Calibrate image flags at known intersection; verify registration and semantic source differences.
- [ ] Implement image semantic masks and road graph connectivity audit; validate true/false positives before applying corrections.

- [x] Implement independent imagery registry, display tile pyramid, local import and NAIP Plus catalog probe (verification pending).
- [ ] Verify local high-resolution coverage and reuse terms; calibrate alignment and semantic segmentation using actual benchmark evidence.

- [x] Implement 3DEP catalog discovery, explicit cached downloads, metric bare-earth grid and sparse classified point-cloud height diagnostics (live verification pending).
- [ ] Verify California Gaps pilot tiles, vertical metadata, classified returns and elevation preview; derive road/rail profiles and building height evidence.

- [x] User reports all 49 DWR pilot cache patches downloaded; local image quality improved on first test. Coverage/seam and actual audit validation pending.
- [x] Adopt model-first dual-renderer asset contract and ten-placement non-singular sprite review rule.
- [ ] Validate DWR mosaic transport audit, quantify coverage and align B01; build shared native/Viewpoint asset fixtures.
