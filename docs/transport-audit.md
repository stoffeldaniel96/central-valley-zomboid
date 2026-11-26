# Workbench v0.3 — transport evidence and image audit
Run from repo root:
```cmd
py -m pip install -r requirements.txt
py src/fetch_transport.py
py src/transport_audit.py
py src/workbench.py
```
Stop the existing server first. Refresh browser. Each source cached separately; partial success retained if one endpoint fails. --source caltrans or --source fra selects one; --refresh replaces cache. --skip-image runs vectors only. Output output/transport/audit.json includes source hashes, image hash, candidates, counts and issues. Stale results are rejected by viewer.

## Editable legend
Feature family and available tagged subtypes, color picker, per-bucket opacity and visibility, count, persisted in localStorage, reset button. Unknown building function remains other. Overture evidence status retains separate base palette. Reference, reverse discrepancy and image shift layers start hidden; enable in legend.

## Sources and lineage
Caltrans All Roads LRS: https://caltrans-gis.dot.ca.gov/arcgis/rest/services/chhighway/All_Roads/MapServer/0 — derived in part from TIGER, not independent of it. Verify licensing, dates and exact feature semantics.
FRA NTAD NARN: https://services.arcgis.com/xOi1kZaI0eWDREZv/ArcGIS/rest/services/NTAD_North_American_Rail_Network_Lines_NS/FeatureServer/0 — public domain per layer metadata; 1:24,000 or better, not necessarily track-level.
County GIS and local survey sources remain research candidates. No Google imagery extraction or derived production geometry.

## Detection
Vector: compare each reference line with union of nearby OSM buffered lines in fixed local metric CRS; reverse comparison also recorded. Thresholds 5 m roads, 3 m rail, minimum 12 m uncovered stretch, 10 m interior margin. These detect geometry disagreement, NOT graph connectivity, true missing connections or direction restrictions. Public network may omit private roads, crossings or parallel tracks. Road/rail references remain separate. No auto edits.
Image: use immutable NAIP JPEG and manifest extent, sample paired cross-track luminance edge contrast on approximately straight 20–30 m windows at shifts -12 to +12 m, across multiple corridor widths. Flag a stronger off-center signal using exploratory thresholds; display shifted diagnostic segment only. No semantic recognition, no verified track detection, no prediction of missing roads absent from all vectors. Occlusion, ballast, curb, painted stripes, shadows and adjacent parallel corridors can produce false positives. Do not treat result as proposed geometry. Image date and co-registration must be verified first.
Future: semantic segmentation (road surface, track/ballast, painted vs physical medians), independently georeferenced masks, skeleton/graph extraction, node degree/grade separation and turn connectivity comparison, source-specific control points and reviewer-labeled calibration set. Only after precision/recall testing promote evidence-backed corrections.

## Benchmark
Use the screenshot intersection as candidate B01; exact coordinates not yet known. Zoom and inspect the red reference gaps and optional magenta image-shift segments. Compare against aerial and additional survey sources, log true/false positive labels and cause. No live dataset or browser test at commit time.

## Intersection calibration export
Zoom to the candidate intersection and click Export current view evidence. The ZIP contains actual projected view bounds, full intersecting OSM/Overture/reference/audit geometries, source metadata, and an original-pixel-grid aerial crop with georeferenced extent. Includes a contextual margin of 40 Web Mercator units. No new source queries or geometry edits. Share the ZIP for local calibration; do not publish source material without rights review.

Classify flags into representation mismatch (single corridor vs separate carriageways), positional discrepancy, genuinely missing feature, topology discrepancy, stale observation, or unresolved. Screenshot red gaps alone cannot distinguish them. Compare road surfaces and railway track centerlines separately from road-network abstractions. Establish labeled examples before changing thresholds. Export implementation and tests not yet verified in browser.

## DWR image analysis
User authorizes proceeding under a working assumption of local DWR analysis permission; no independent rights finding or redistribution permission. Default audit source is now DWR (largest local collection by pixel count); --image-source naip restores the earlier baseline, or select exact DWR snapshot/group ID. --skip-image for vector only. Source hashes verified, four-patch grayscale cache, cross-patch sampling (half-pixel edge clamping), missing coverage windows skipped. DWR samples offsets every 0.25m, flags provisional shifts >=1.5m, uses 40 samples along each window and an optional approximate standard-gauge paired ridge contrast hypothesis. Parallel tracks and shadows can cause wrong matches. No geometry changed, no semantic discovery, no registration validation. Workbench lists source and tested window count. Existing benchmark export remains NAIP-only. Archive audit.json before comparing runs. Synthetic seam and rail tests added; live verification pending.

## DWR benchmark and physical observation authoring
Select DWR mosaic, zoom to the intersection (roughly 200–300m), click Export current view evidence. ZIP schema v2 includes independent DWR PNG crops at original exported sampling, per-crop extent/pixel windows/source hash, NAIP context, vector layers, audit and physical observations. 24M total DWR crop pixels cap; zoom closer if refused. No full mosaic assembled or resampled. Export intended for local analysis under project working assumption, not public distribution. Optional Physical observations panel allows independent polygons/lines from selected DWR coverage, stored in data/physical_observations.json with provenance; proposed only, no automatic geometry application, no edit/delete/review UI yet. Roof outline is not wall footprint. Manual annotations are optional calibration, not required citywide. Next analyze actual exported benchmark and develop automatic extraction. Synthetic tests added; live browser behavior not yet verified.
