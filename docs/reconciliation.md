# Evidence reconciliation and terrain-first fidelity
Use OSM as candidate topology and semantics, not a ground truth. Compare property-specific observations against independent evidence. A larger dataset is not necessarily more accurate, and two datasets copied from one source do not count as independent corroboration.

Stages:
1. Record source snapshots, date, CRS, spatial accuracy/resolution, rights, lineage and hash.
2. Co-register against fixed projected coordinates; check offsets at independent control points. Do not mistake imagery registration or roof displacement for road error.
3. Compare geometry and meaning: road centerlines vs pavement polygons, medians vs painted islands, building outlines vs roof overhangs, parking boundaries vs stall layout. Do not infer lane widths from centerline alone.
4. Log proposed corrections with before/after, evidence, uncertainty and reviewer. Distinguish observed, inferred and unknown. Reject conflicting, stale or unlicensed evidence for production corrections.
5. Only after reconciliation, evaluate sanitization for structural representation. Preserve both geometries and quantify displacement against the reconciled reference. Surface geometry stays continuous by default.
6. Rasterize visual surfaces independently from native physics samples. Test boundary cases (water, barriers, steep grades, crossings) where sampling changes mechanics.

## Initial sources
- OSM: existing data/pilot.osm with manifest; ODbL.
- USGS NAIP: https://imagery.nationalmap.gov/arcgis/rest/services/USGSNAIPImagery/ImageServer — public-domain NAIP mosaic, primarily 0.6 m. Exact local vintage, resolution, registration and accuracy need verification. Use https://index.nationalmap.gov/arcgis/rest/services/USGSNAIPImageryIndex/MapServer to identify dated source tiles; archive original imagery where feasible.
- Stanislaus County GIS: https://open-data-stancounty-gis.hub.arcgis.com/ — candidate local parcels/transportation; verify each layer's license, lineage and date.
- USGS 3DEP: https://www.usgs.gov/3d-elevation-program — vertical evidence; record acquisition date and vertical datum.
- Google Earth/Maps: visual quality benchmark subject to terms; no restricted mesh, texture or derived geometry extraction. Independently usable evidence for actual corrections.
- Independent field observations: useful for unclear medians, curb shapes, markings and dated features; log date, measurement method and permissions.

## Pilot
Run build_index.py then analyze_geometry.py. Default clips to projected pilot rectangle, not the padded fetch extent. --unclipped is available for historical comparison. Multipolygon assembly remains pending. Next acquire dated aerial imagery, identify intersection and record discrepancies using the example ledger format. No actual corrections are approved or applied by this commit.
