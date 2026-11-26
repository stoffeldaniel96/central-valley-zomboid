# 3DEP elevation and point-cloud evidence
2023 California Gaps, work unit 300618, includes portions of Stanislaus/Merced. NOAA metadata: https://www.fisheries.noaa.gov/inport/item/77693 (CC0; nominal 0.35 m pulse spacing, 0.5 m DEM, UTM NAD83(2011), NAVD88 Geoid18 meters). Exact pilot coverage and point-cloud product identity remain unverified. USGS catalog API: https://apps.nationalmap.gov/tnmaccess/. Do not infer local coverage from regional bounding box.

## Discover first
```cmd
py src/fetch_elevation.py
```
Saved data/elevation/catalog.json. Lists OPR DEM, 1 m DEM, LAS/LAZ candidates with index, title, size and source metadata. Query names based on USGS dataset listing; endpoint response not tested remotely. If names return empty or fail, use NOAA Data Access Viewer https://coast.noaa.gov/dataviewer/ or USGS LidarExplorer https://apps.nationalmap.gov/lidar-explorer/ and download the original product tiles intersecting the pilot. Do not assume every candidate belongs to the same project/datum.

Select explicit indices from catalog using --download KIND:INDEX (repeatable), or a specific verified project substring with --kind opr --match PROJECT. Per-file size cap 500 MB by default; override --max-mb only deliberately. Download hashes and metadata cached separately. No auto-download on catalog query.

## Build the ground grid
```cmd
py -m pip install -r requirements-elevation.txt
py src/build_elevation.py --vertical-datum "NAVD88 Geoid18"
```
Default inputs: downloaded OPR TIFF files; alternatively --dem PATH PATH for explicit compatible tiles. Before running verify all DEM vertical units meters and same vertical datum; argument records operator verification, not an automated transformation. Use --resolution 1 for lower memory. Default 0.5 m; resampling does not establish native detail. Preserve NaN for unknown cells. Fixed local metric grid (north-up); output/elevation/ground.npy, ground.json. Display preview registered under Additional imagery. Color range clipped to 2nd–98th percentile for visibility; gray = no coverage. Numeric values separate from display. Overlaps first-valid priority, count differences >0.25 m for review; never silently assume agreement. Avoid combining different project vintages without review.

## Analyze classified cloud
After downloading verified matching LAS/LAZ products:
```cmd
py src/analyze_lidar.py --vertical-datum "NAVD88 Geoid18"
```
Or --las PATH PATH. Requires same verified vertical units/datum as DEM, no datum conversion. Streams half-million return chunks, excludes withheld points, calculates sparse class-specific maximum heights relative to ground. Separate layers for selected surface returns, classified buildings (6), vegetation (3–5), bridge decks (17). Classification may be incomplete; no interpolation or geometry inference. Heights may be negative due to uncertainty or source differences. No floor/roof reconstruction; no bridge clearance claims from bare earth. Local results and display previews available after restarting workbench. Large grids and raw downloads can require substantial disk/RAM; choose 1m first if needed. No original data or derivatives automatically sent to third parties.

Next: verify actual catalog coverage and class inventory, compare aerial/OSM registration, derive per-building roof planes and robust height statistics, route profiles and independently modeled deck surfaces. Do not use DEM as a walkable surface at grade-separated crossings. New scripts and optional dependencies not yet exercised against user's Windows/Python 3.14 environment.
