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
| 06 | Model-first / 3D | Compare native sprites, model-to-sprite and optional runtime rendering; Viewpoint compatibility/licensing investigation |
| 07 | Source reconciliation | Georeferenced OSM + independent licensed imagery/elevation; provenance, disagreement and completeness metrics |
| 08 | Adaptive resolution | Subtile rasterizer, deduplication and atlas/memory benchmarks; physical implications tested separately |
| 09 | Architectural vocabulary | Graybox primitive/assembly/archetype registry, coverage audit, reusable gap-filling workflow |

## Delivery gates
G0: independently inspect source data and inventory native assets. G1: reproduce a small intersection with accurate continuous terrain; document reference uncertainty. G2: diagonal room and native compiler compatibility experiments. G3: benchmark residential, commercial, institutional, industrial and rural environments with functional grayboxes. G4: complete Turlock physical/functional graybox with no unresolved critical gameplay failures. G5: graphical/material/1993 finish and fidelity validation; first public product. G6: expand using proven tools and assets.

Parallel research is encouraged; gates are evidence-based, not deadlines. No fabricated coverage percentages or engine capability claims. See docs/benchmarks.md.
