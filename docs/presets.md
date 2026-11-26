# KnoxMap presets
Schema derived from a real KnoxMap 1.8.7.1 exported v1 preset.
The template preserves the supplied pilot settings except street alignment,
building squaring, basement share (set to zero) and generation seed (1993).
Their exact effects require UI and generation verification. Rectilinear building
alignment and spread_buildings remain enabled from the original preset and may
alter footprints; investigate before asserting 1:1 fidelity. The maximum building
size also needs investigation. Fixed seeds do not by themselves guarantee
identical results across versions or adjacent exports.

Run:
```powershell
py src/build_index.py
py src/export_presets.py
```
Import output/presets/CentralValley_Turlock_Pilot.knoxmap.json in the UI.
The committed template also preserves the manually entered pilot bounds.
The generated preset uses the computed geographic index envelope instead;
slight differences are expected. For an experimental sector, supply
--sector S_i_j using a real ID from output/sectors.csv.
Do not stitch sectors merely because their bounding boxes are adjacent:
projection, padding, origin, rotation and quantization must be verified.
No UI import or compiler execution tested yet.
