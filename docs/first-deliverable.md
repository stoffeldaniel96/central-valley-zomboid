# G0 diagnostics — initial implementation
Run from repository root on Windows:
```cmd
git pull
py -m pip install -r requirements.txt
py -m unittest discover -s tests
py src/build_index.py
py src/fetch_pilot.py
py src/analyze_geometry.py
py src/inventory_assets.py --game "C:\Program Files (x86)\Steam\steamapps\common\ProjectZomboid"
```
Adjust game root to actual Steam library. If pilot acquisition fails, use a complete OSM XML snapshot with --osm. Outputs under ignored output/geometry and output/assets. Share summary.json and CSVs as needed, not game packs or extracted art.

Geometry: segment length, nearest cardinal/octilinear deviation, fixed-start lateral displacement estimate, 5° exploratory compatibility fractions, length-weighted 256m spatial bins and 5° axial histograms by road/building/parking/rail. No snapping or topology modifications. XML pilot only; relations omitted and reported; source completeness and exact Turlock boundary unresolved. Heatmap CSV is numerical data, not yet a rendered map. Asset inventory is file-level only; next step inspect actual local .tiles/.pack formats and decode metadata to identify families, facings and states. No actual sprite count yet.

Elevation follow-on: choose licensed bare-earth DEM with recorded vertical datum and resolution, sample route profiles, distinguish bridge decks from ground and validate clearance. Chronology follow-on: feature-level date evidence and conflicts, no invented dates. Interop follow-on: version-pinned experiments with native and community backends.

Tests added; local and CI execution not verified at commit time.
