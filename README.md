# Central Valley
Standalone Project Zomboid Build 42 world: modern Modesto–Turlock–Merced geography, 1993 material culture, 1 meter per tile. Long-term ambition: California.

## Windows quick start
```powershell
py -m pip install -r requirements.txt
py src/build_index.py
py -m unittest discover -s tests
py src/fetch_pilot.py
```
Install [KnoxMap](https://github.com/spytheeuclidean-a11y/knoxmap/releases) separately. Select the pilot bbox in output/stats.json, 1 m/tile, and test a standalone export. The downloaded OSM is reference data, not a verified KnoxMap input. Record compiler and game versions. Do not stitch exports until alignment is verified.

See ROADMAP.md and docs/architecture.md. No playable mod compiled yet. OSM data © OpenStreetMap contributors, ODbL: https://www.openstreetmap.org/copyright.
