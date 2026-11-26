# Legacy KnoxMap compiler experiment
This workflow is optional and superseded as production architecture by [ADR-001](decisions/001-knoxmap.md). No compiler candidate has passed the independent-input acceptance gate.

External dependency: https://github.com/spytheeuclidean-a11y/knoxmap. Use a version-recorded local installation; review mixed licensing before vendoring any code.

Generate a disposable terrain project in the KnoxMap UI using output/stats.json pilot_bbox. Disable street alignment and straightening, choose 1 m/tile, record actual bounds, rotation and padding. From Central Valley:
```powershell
py src/compile_pilot.py --knoxmap ../KnoxMap --project ../KnoxMap/output/turlock
```
Append --execute only for the intended external project; --reuse-buildings protects existing generated or manually edited buildings. Inspect logs and manifest, compile failures, lot coverage, install in a fresh save and verify gameplay. Paths are examples.

300-tile WorldEd working cells and 256-tile B42 exported cells differ. Independent exports cannot be stitched solely by bbox. Actual game/compiler versions, coordinate mapping, alignment, fidelity and native output properties need verification. Existing adapter unverified in live compilation. New production backend must consume our independent world representation without silently losing necessary details.
