# Central Valley
A standalone Project Zomboid Build 42 map of the Modesto–Turlock–Merced region at 1 meter per tile. Contemporary geography, 1993 material culture. Long-term goal: reusable generation pipeline for California.

## Windows quick start
1. Install Python 3.11+ and Project Zomboid Build 42.
2. `py -m pip install -r requirements.txt`
3. `py src/build_index.py` generates the regional grid and downtown pilot query.
4. `py src/fetch_pilot.py` obtains an OSM snapshot (internet required).
5. Install [KnoxMap](https://github.com/spytheeuclidean-a11y/knoxmap/releases), select the pilot bounding box in output/stats.json and test a standalone 1 m/tile export. The OSM snapshot is independent reference data, not a verified KnoxMap input.
6. Test a fresh save, recording game and generator versions. Do not stitch exports until alignment is verified.

## Coordinate contract
Fixed local azimuthal equidistant projection centered on downtown Turlock, signed global cells, x east/y south. Engine placement offset is provisional and must be frozen before production. Statewide distortion and negative game coordinates require investigation.

## Status
Geographic preparation only; no playable mod compiled. See ROADMAP.md. Generated files and raw datasets are excluded from Git.

OSM data © OpenStreetMap contributors, ODbL: https://www.openstreetmap.org/copyright.
