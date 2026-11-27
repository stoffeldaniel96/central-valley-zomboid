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
G0: independently inspect source data and inventory native assets. G1: ground-first gate: signed Z, slopes, independent surface geometry, native-grid distortion and real engine/Viewpoint traversal; buildings not required. Reproduce B01 ground and actual Turlock below-zero/grade-separated benchmark sites; document reference uncertainty. G2: diagonal room and native compiler compatibility experiments. G3: benchmark residential, commercial, institutional, industrial and rural environments with functional grayboxes. G4: complete Turlock physical/functional graybox with no unresolved critical gameplay failures. G5: graphical/material/1993 finish and fidelity validation; first public product. G6: expand using proven tools and assets.

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

- [x] Implement high-resolution DWR benchmark export and independent physical observation proposals (local validation pending).
- [ ] Analyze actual B01 benchmark package, derive first surface/structure candidates and quantify error before scaling.

- [x] Implement signed metric ground laboratory, quantized slope and material sampling distortion reports, continuous terrain mesh output (local tests pending).
- [ ] Verify native below-zero and slope mechanics at actual Turlock benchmark sites; derive a continuous shared regional baseline and protect local relief after checking DEM metadata.
- [ ] Run real B01 ground reconstruction before building additions; preserve unknowns and separate stacked surfaces.

- [x] Measure B01 provisional surface candidates at 1m, 25cm and 12.5cm; add horizontal-only ground audit before DEM availability.
- [ ] Identify and validate real canal/depression, CA-99 and railway overpass ground benchmarks; no synthetic showcase map required.

- [x] Verify uploaded pilot DEM checksum, full coverage and vertical metadata; analyze observed local relief and broad trend.
- [x] Adopt Central Valley selective vertical sanitization policy; add reproducible diagnostic (local CLI pending).
- [ ] Review local relief against actual features; constrain regional flattening, protect drainage/decks and test shared boundaries. No final thresholds approved.

- [x] Analyze actual pilot relief candidates and level-foundation groups; record conflicts and Better Terrain / Rolling Hills interoperability evidence.
- [ ] Use full-pilot reconciled footprints and protected route/water constraints; solve seam-safe planar pads and relief jointly; verify upstream custom terrain interface and physical/render parity.

- [x] Implement and execute shared regional candidate terrain fit with protected residual and planar foundation assertions on uploaded pilot (partial Overture only).
- [ ] Run full local Overture fit; resolve blocked pads, new sharp transitions, missing water and grade-separated routes, and buffered sector seams before compilation.
