# Ground coverage audit
Run from repo root:
```cmd
py src/ground_coverage_audit.py --benchmark PATH_TO_BENCHMARK_ZIP --candidates PATH_TO_PROJECTED_CANDIDATES_GEOJSON
```
Reports coverage of OSM vehicle-road centerlines by the union of proposed road/parking/driveway surfaces. Uses project metric CRS, clips to benchmark context, reports exact outside length and outside 0.5m tolerance; gaps >=3m exported as EPSG:3857 GeoJSON. Thresholds configurable. Non-service and service ways reported separately (not a public/private classification); bridges, tunnels, proposed/construction and pedestrian ways excluded from this at-grade check. Centerline sums count overlapping ways separately. Road geometry is only an omission detector, not a source of pavement boundaries or completeness truth. Cannot detect roads missing from OSM or measure width accuracy. No automatic edits.

B01 real local experiment: v1 non-service 59.18%, service 41.65%; v2 89.99%, 45.54%; v3 97.46%, 78.93%. V3 adds five visually digitized proposed pavement features; unclassified/occluded geometry remains unresolved. North Broadway residual 34m obscured by tree canopy. Total outside tolerance 34.04m non-service and 211.56m service. Local experiment ran successfully using equivalent standalone algorithm; repo wrapper not yet run in user's environment. Do not commit source imagery or unreviewed candidate polygons. Next: review remaining gaps, physical surface classes independent of OSM, boundary fidelity and reusable vocabulary; signed elevations require verified DEM. No synthetic map deliverable.
