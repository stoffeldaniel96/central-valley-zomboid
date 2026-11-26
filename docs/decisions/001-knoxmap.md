# ADR-001 — Remove KnoxMap from mandatory production path
Status: adopted, 2026-11-26.

## Context
User generated Turlock terrain and building previews with KnoxMap 1.8.7.1. Observed parking/road/geometry and architecture discrepancies; source vs generator contribution not yet measured. Upstream README explicitly describes road rotation/straightening, stepped or squared buildings, generic interiors, source limitations, optional enrichment layers and native map compiler. It documents CLI tools render_ground.py, audit_layouts.py, validate_tbx.py, compile_map.py and WorldEd fallback.
Reference: https://github.com/spytheeuclidean-a11y/knoxmap (current README reviewed; local version may differ).

## Decision
Central Valley owns geographic reconciliation, sanitization, semantic geometry, grayboxing, asset registry and quality checks. KnoxMap cannot be mandatory or authoritative. Keep existing presets and wrapper unchanged as optional experimental tools. Never ingest its invented geography or interiors as verified observations.

| Component | Disposition |
|---|---|
| End-to-end generator | Baseline/comparative analysis; quick disposable gameplay control |
| OSM acquisition, landcover, terrain and road layout | Replace; reference algorithms only |
| Building and interior generation | Reference for native room/loot conventions and comparative metrics, not production geometry |
| Population and spawn estimates | Benchmark only; no claims about real residents |
| Local tile extraction | Optional inventory aid; no redistribution of vanilla art |
| Ground rendering | Optional comparative diagnostic |
| Layout/TBX validation | Candidate optional native-output validation |
| Patched WorldEd compiler | Candidate external native export backend if it accepts independently generated inputs without loss |
| Packaging and installation | Candidate adapter utility if independently usable |

## Reuse gate
Pin installed release and document interface, input/output contract, version, licensing and reproducible tests. Test a hand-authored minimal native project with no KnoxMap generation. Compare output against our semantic graybox and in-game behavior; record dropped/quantized features, origin, padding, cell alignment, failures and packaging. If unacceptable or too coupled, use standard mapping tools or build our own adapter/core. Successful exit code alone is insufficient. No component promoted yet.

## Licensing
Upstream describes MIT additions, GPL compiler patch/binary and inherited Knoxify files without published license. Review per-file terms before copying or distributing; prefer external invocation while evaluating. Preserve OSM attribution/ODbL and third-party notices. Do not redistribute game art. Review Viewpoint separately; no dependency decision.

## Consequences
Old compiler and preset commands remain available for experiments, not the main workflow. No ongoing mass generation with KnoxMap. Preserve Baseline 001 and compare against independent verified references. Existing scripts need not move until imports/tests can be migrated safely.
