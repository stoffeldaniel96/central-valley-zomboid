# Compiler integration
External dependency: https://github.com/spytheeuclidean-a11y/knoxmap
Use an installed, version-recorded KnoxMap distribution. Do not vendor upstream code: its components have mixed licensing, including original files without a published license.

## Pilot
Generate the terrain project with KnoxMap UI first, using output/stats.json pilot_bbox (west,south,east,north). Disable street straightening and choose 1 m/tile if available. Record actual scale, bounds, rotation and tool version; the UI may pad the region. A standalone test is not proof of exact global alignment.

From Central Valley, preview the command sequence:
```powershell
py src/compile_pilot.py --knoxmap C:/KnoxMap --project C:/KnoxMap/output/turlock
```
Append --execute to run building generation, TBX validation and compilation. If buildings already exist, use --reuse-buildings to preserve them. Check output/compile.log and output/compile-manifest.json. Successful process exits do not prove complete exports; inspect compile_failures.json wherever the compiler writes it, compare expected cell coverage, then install using the KnoxMap workflow and test a new save.

## Known boundary mismatch
KnoxMap documentation distinguishes 300-tile WorldEd work cells from 256-tile Build 42 exported cells. Do not identify them interchangeably. A 2048 m pilot may require padded work cells. Sector stitching requires global origin and exact transform control; this adapter does not claim to solve either.

## Acceptance
- Actual game version recorded; no compiler failures or missing lot files.
- North-up orientation and distances between three non-collinear landmarks checked to within 2 tiles after translation; record measured deviations.
- Roads passable, building doors and stairs reachable, collision and loot plausible.
- Adjacent separately generated pilot verified at seam before expanding.
- Capture game screenshots and logs, not just an editor preview.

No automated terrain API integration yet; no live compile verified. The compiler adapter invokes documented CLI commands only.
