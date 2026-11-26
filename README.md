# Central Valley

A geographically faithful, 1:1 Project Zomboid Build 42 world. **Central Valley: Turlock** is the first finished product; Modesto–Merced and eventually California are expansion ambitions, not initial release scope.

Modern geography, 1993 material culture. Minimum final visual target: comparable to Google Earth 3D, with functional, explorable environments. Physical and gameplay fidelity precede artistic polish. Native compatibility is strongly preferred, not mandatory.

## Start here
- [Project charter](docs/charter.md)
- [Architecture](docs/architecture.md)
- [Research and delivery roadmap](ROADMAP.md)
- [ADR-001: KnoxMap disposition](docs/decisions/001-knoxmap.md)
- [Benchmark protocol](docs/benchmarks.md)

## Existing experimental tools
```powershell
py -m pip install -r requirements.txt
py src/build_index.py
py -m unittest discover -s tests
py src/fetch_pilot.py
```
These index the **future regional envelope**, not the first release boundary, and acquire a small OSM pilot. KnoxMap is optional; see docs/compiler.md and docs/presets.md for legacy baseline experiments. No production world generator or verified playable release exists yet. The existing projected origin and sector IDs remain stable; first release boundary is TBD.

Keep source snapshots, licensed reference imagery and compiled artifacts out of Git. Map data © OpenStreetMap contributors, ODbL: https://www.openstreetmap.org/copyright.
