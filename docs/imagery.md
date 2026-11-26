# Imagery registry and catalog probe
Existing NAIP baseline and audit remain unchanged. New local imagery layers use immutable content/metadata IDs, original bytes, display tile pyramids and independent metadata. Tiles are loaded only for the visible area and suitable zoom; 512 pixel tiles, full-resolution level 0. Each import is capped at 64M pixels; multiple bounded patches may be registered. Only one additional snapshot is shown at once. No automated Google/Vexcel acquisition, no bypass of access restrictions.

## Inspect coverage
```cmd
py src/probe_imagery.py --source naip
py src/probe_imagery.py --source plus
```
Catalog records saved to output/imagery. Compare vendor, date, resolution_value and resolution_units. Catalog candidates may be stale, overlapping or not contributing to a mosaic. Service-level resolution does not establish local coverage. NAIP Plus contains high-resolution orthoimagery; do not assume all content is public domain. Verify actual contributing source and rights.

To request a small test patch use --source plus --bbox WEST SOUTH EAST NORTH --export --pixel-m 0.2. Bbox is WGS84; request size capped at 4000 pixels per side. Optionally --raster-id ID selects a candidate; verify actual coverage. No arbitrary upsampling claim: requested pixel size does not indicate native resolution. Saved as reference_only. Existing NAIP not overwritten.

## Import a local image
```cmd
py src/import_imagery.py "C:\path\image.png" --provider "Authorized provider" --date 2026-03-13 --bounds XMIN YMIN XMAX YMAX
```
Bounds are EPSG:3857 outer pixel edges, NOT longitude/latitude. Alternatively --world-file PATH for a north-up EPSG:3857 world file. PNG/JPEG/TIFF supported if already projected to EPSG:3857. For GeoTIFF in other CRSs or rotated imagery, reproject/export using GIS software first; GeoTIFF metadata is NOT automatically read. No control-point registration yet. Use only images you are permitted to import/display. By default usage is reference_only. --usage analysis_reviewed requires a documented --rights-note and only use after independently verifying permissions; this is an operator assertion, not automated license verification. Native resolution optional --native-gsd meters. All registration initially unverified. Local imagery stays in ignored data/imagery.

Restart workbench after import. Select a snapshot under Additional imagery; overlay opacity controls comparison. Tile rendering is lazy and zoom-dependent. All additional snapshots are display-only in this release, even if marked analysis_reviewed. Existing image audit and benchmark export use the original NAIP snapshot only, and export warns when an additional snapshot is selected. No new imagery is automatically used for geographic corrections.

Next: local coverage results, source-specific registration controls and residuals, georeferenced GeoTIFF import/reprojection, approved-source audit selection, benchmark export respecting source rights, semantic segmentation. Verify browser, catalog and local tests before relying on new implementation.

## California DWR 2021 orthophotography
User's NAIP/Plus catalogs both returned the same June 2022 0.6m source tiles. New candidate: https://gis.water.ca.gov/arcgisimg/rest/services/Aerial_Photography/San_Joaquin_Valley_2021/ImageServer (0.25 US survey foot raster; 6.7 cm source imagery, spring 2021; see /info/iteminfo). Probe with py src/probe_imagery.py --source dwr. Catalog uses different fields; actual pilot coverage unverified. Use bounded export only if permitted, registered reference-only; service capability flags are not license grants. For a 7.62cm patch use --bbox WEST SOUTH EAST NORTH --export --pixel-m 0.08, within 4000px cap. Local query/export not yet verified.

## Pilot mosaic
User verified the raster 1 test patch imports and looks substantially better than NAIP. To plan a full pilot mosaic run py src/fetch_dwr_pilot.py. This is offline and reports pixel dimensions and patch count. If permitted under source terms and service limits, explicitly run py src/fetch_dwr_pilot.py --download --limit 2 to test two patches; then repeat without --limit to complete. Default 8cm approximate ground spacing and 4000px patches. Shared EPSG:3857 pixel grid extends less than a pixel beyond pilot on east/south; validate server extent and dimensions. Sequential 10s pauses per request, Retry-After/backoff, cached completed snapshots. Partial acquisition remains usable. No request concurrency. Local disk usage can be several GB because registry stores original JPEG plus lossless PNG tiles. Restart workbench; grouped patches appear as one selection. Original single test patch remains separate. Additional imagery still reference-only; benchmark export and automated audit still NAIP-only. Verify permission, imagery coverage and registration before analysis. Browser, live batch and tests not yet verified.
