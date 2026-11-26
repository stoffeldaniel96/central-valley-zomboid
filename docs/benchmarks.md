# Benchmark protocol
B01 complex intersection shown in user screenshots (exact coordinates/extent TBD; approximately 300 m square initial candidate). B02 downtown commercial block. B03 residential block. B04 shopping center. B05 industrial facility. B06 university campus. B07 agricultural property. B08 highway interchange. Select actual locations and licensed reference snapshots before testing.

For every benchmark record: bounds and fixed global transform; source dates/hashes/rights; observed vs inferred geometry; raw and sanitized geometry; missing primitive families; backend and game versions; screenshots and logs; elapsed time, storage, RAM and runtime performance; manual review and failures.

Measure position/edge displacement, area overlap, road graph connectivity, curb/marking placement, height/roof accuracy, uncertainty and gaps. Compare against original verified source, not just KnoxMap. Test actual play: collision vs appearance, doors/windows, room detection, stairs, vehicles, zombie navigation, combat and lighting as applicable. Keep visual and physical results separate; record unsupported features instead of silently approximating. Set numeric thresholds after reference accuracy and backend precision are measured. Use Google Earth 3D only as quality benchmark subject to terms; no restricted data extraction.

Native backend spike: independently author a tiny cardinal room, diagonal room experiment and subtile parking lot. Try standard/native and optional KnoxMap compiler path; compare losses, compatibility and performance. Do not conclude diagonal collision is supported from sprites alone.

Baseline 001: archive original user-generated KnoxMap terrain/building previews and preset locally; compilation/play status unverified. No real heatmaps or sprite inventory completed yet.
