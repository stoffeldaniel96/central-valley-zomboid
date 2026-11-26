# Geographic reconciliation workbench v0.1
This is a local development prototype, not a production geography editor. Uses Python, Shapely and dependency-free SVG/JavaScript instead of a MapLibre/TypeScript build for the first pilot; avoids an additional Node installation and CDN dependencies. Migrate when scale requires it.

## Run
```cmd
git pull
py -m pip install -r requirements.txt
py src/build_index.py
py -m unittest discover -s tests
py src/fetch_aerial.py
py src/workbench.py
```
Open http://127.0.0.1:8765. Existing data/pilot.osm is used; fetch_pilot.py if absent. If aerial acquisition fails, the workbench still runs without aerial. --year YYYY is optional on fetch_aerial.py; default is service mosaic, not a verified dated snapshot. --refresh requests a replacement. Inspect data/aerial/manifest.json for candidate dates, rights, actual extent and hash. Do not mistake catalog candidates for actual image provenance or exported pixel spacing for source accuracy.

Click features to inspect source tags. Toggle layers, zoom and pan. Redraw a simple line or hole-free polygon using clicks, finish, add evidence and rationale, save. Complex polygons and boundary-crossing features remain inspect-only. Orange overlays are proposals, not authoritative corrections. Export proposed geometry as WGS84 GeoJSON; history stored locally in data/corrections.json. No automatic approval, application, topology preservation or reconciliation yet. Avoid editing connected roads until shared-node constraints are implemented.

Viewer uses EPSG:3857 for image alignment (not meter-accurate ground measurement); the core fixed local projection remains authoritative for geometry analysis. Source files remain immutable. Multipolygon way members are assembled, inner rings assigned to containing shells; invalid or unsupported relations reported rather than guessed. Viewer retains full features and clips display. Current OSM acquisition is limited to selected feature kinds, not comprehensive terrain. No actual independent aerial co-registration verified yet.

Next: confirm imagery dates/coverage; compare landmarks, identify benchmark intersection, add measured discrepancies and source-specific evidence IDs, implement topology-aware edits and reviewed correction application. No native tile export yet.

## Supplementary building coverage (v0.2)
```cmd
py -m pip install overturemaps
py src/fetch_buildings.py
py src/workbench.py
```
Restart the server and refresh the browser. Overture is an optional download dependency, not a runtime requirement. If the client is unavailable for your Python version, download a building GeoJSON for the pilot bbox with the official Overture client in a supported environment, then run py src/fetch_buildings.py --from-geojson PATH. Cache and manifest are stored under data/buildings/ (ignored). The CLI resolves latest; a release hint is recorded but is not proof of an exact pinned release. Preserve the snapshot hash and source attribution.

Cyan = OSM buildings; green = Overture coverage candidates with no OSM footprint within 2 m; orange = nearby/overlap review; gray = high-IoU matches (hidden by default). Spatial comparisons use the fixed metric projection, not Web Mercator units. 0.70 IoU and 2 m proximity are exploratory thresholds; overlapping split/merged buildings require review. Overture incorporates OSM, so matching OSM-derived geometry is not independent evidence. Inspect per-feature sources; verify against NAIP, date and other observations. Roof outlines may differ from wall footprints. No automatic merge or candidate acceptance. Supplementary features are inspect-only. No count should be interpreted as an actual completeness percentage without independent reference.

Source and license: https://docs.overturemaps.org/guides/buildings/ and https://docs.overturemaps.org/attribution/ (ODbL).
