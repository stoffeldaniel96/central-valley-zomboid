# Build 42 tileset and renderer investigation (2026-11-26)

## Scope and evidence status
Research, not an engine test. Target exact local build must be recorded; community engine notes compare 42.21.0 and 42.22.2. Keep fixed 1 m project tiles, original continuous geometry, and independently compiled visual and physical outputs. No mandatory Java extension selected. The source links below are references, not copied implementation or permission to incorporate third-party code.

## Native surfaces
- Standard 2x authoring canvas is 128x256; floor art occupies a diamond within it. Packed textures may be trimmed, with original canvas/offset data retained. This is a visual sampling constraint, not the geographic grid resolution.
- Community notes report separate floor pass for solidfloor or RenderLayer=Floor; the latter is a candidate for non-solid overlays. diamondFloor is used for full-diamond road art, not arbitrary trimmed decals. Verify actual flags, material behavior, floor shaper and lighting in installed build.
- Compile an original planar surface/material map into one visual diamond per native square, plus native gameplay material/floor properties. Curves and diagonal markings need not become diagonal physical wall elements. Do not mistake a subpixel image for a new collision square.
- Candidate representations: reusable base material plus clipped marking overlays; quantized boundary masks; exact baked composite for exceptional tiles; optional chunk mesh backend. Deduplicate on visual AND mechanical/state signature; record visual error independently. Avoid huge unique per-square atlases. Do not set water, blocked, or slope behavior solely from visible artwork.
- Illustrative 2048^2 pilot contains 4,194,304 squares. A unique full 128x256 RGBA canvas for every square would be 512 GiB uncompressed (before trimming/compression); not an actual runtime memory prediction. Measure trimmed packing, unique signatures, atlas count, loading, FPS and VRAM, not just PNG disk size.

## Depth and structure
- Community reverse-engineering indicates baked per-tile depth PNGs and assignment mappings drive depth rendering; geometry primitives are authoring input, not automatic collision meshes. Minimal tileGeometry.txt reportedly gates loading custom depth maps. Verify depth encoding against vanilla fixtures and in-game test occlusion with player, dropped item, cutaway and light.
- Render the same parameterized model into native sprites and depth textures, with optional separate OBJ assets. Do not assume arbitrary diagonal wall collision from a correct-looking sprite. Native wall edge and room/door mechanics need their own tests.
- Native API exposes sloped surfaces, apparent Z, min/max and direction. Community notes identify vanilla ramps with 5% storey increment per square. Test whether mod-defined min/max are honored, arbitrary slope ranges, direction, continuity, vehicles, zombies, projectiles and stacked surfaces. Native ramps are not proven general DEM support.
- 42.21 changed certain edge API signatures; inspect installed APIs before writing Lua. Exact diagonal wall collision, room flood fill, cutaway, opening interaction and multiplayer remain unknown.

## Existing tools / optional backends
- Unjammer PZTools: native 256 and legacy 300 cells, TileZed/WorldEd/BuildingEd. Z3R0-BYT3Z branch also documents depth-map authoring. Evaluate exact version/license and output in a disposable mod.
- guspuffygit project-zomboid-tile-cli: standalone Go atlas and tile-definition pack/unpack, floor splitting, depth output. Small public repo, no visible license in root listing; evaluate as external tool only until rights and behavior checked. A codec round-trip does not prove runtime semantics. Do not adopt full-coverage depth output as physically correct.
- Viewpoint resource packs bind OBJ assets to named tiles, and support higher-resolution flat floor textures with optional PBR maps. This is a plausible second backend, not native isometric support or new collision.
- Viewpoint documented draw callbacks support custom world-space meshes with depth; no callback when an Iris/Minecraft shaderpack owns frame. Test mesh integration, lighting, streaming and compatibility before depending on it. Viewpoint Better Terrain reports physical relief but standard map only, multiplayer unvalidated. Ask maintainers about custom elevation/mesh data interface and compatibility before extending.
- Indie Stone Oct 2026 explicitly supports Lua modding, not Java mods/loaders; Java internals can break on updates. Keep native path baseline, optional narrowly scoped bridge only if required.

## Experiment sequence (no geographic data dependency)
T01 floor calibration: 16x16 or 32x32 native squares; original synthetic asphalt/grass/concrete at 0, 15, 30, 45, 60 and 75 degrees, arc, painted lines, parking bays, rail overlay. Test seam positions, zoom, lighting, snow/rain, erosion, footstep/surface behavior, walking/zombie/vehicle traversal. Full-floor art vs overlay; confirm sprite anchor from vanilla. Record unique art/semantic signatures and atlas/VRAM.
T02 depth fixture: one raised curb, one slanted visual wall, one rectangular object. Compare default depth, measured depth and incorrect depth; player foreground/background and drop items. No collision claim.
T03 structural room: cardinal control vs 45-degree visual walls with native staircase-like collision proxy; quantify blocked/free area, corner leakage, doors/windows, LOS, room assignment, cutaway, pathfinding, construction/destruction. If mismatch material, investigate minimal extension or upstream capability.
T04 native slope: flat control, 20-square vanilla ramp, custom shallow ramp and elevated deck above traversable route. Verify apparent Z with actors and cars, AI, visibility, MP/save. Compare actual meters/storey calibration rather than assume physical scale.
T05 Viewpoint parity: same original models and flat material textures; compare isometric native and first/third-person, then mesh extension only if necessary. No dependency decision before evidence.
T06 scale: repeat 256x256 synthetic terrain at several densities/quantization tolerances, measure serialized sizes, unique sprites, page counts, RAM/VRAM, loading, frame time. Native 256-cell compiler/export, save/reload, version metadata. Only then scale to real B01.

## Sources
- Official B42 technology: https://projectzomboid.com/blog/news/2024/01/hmm-upgradez/
- Official B42.20 overview: https://projectzomboid.com/blog/features-overview-build-42-20/
- Official Java support position: https://projectzomboid.com/blog/news/2026/10/a-note-on-java-mods-and-modding/
- Official Java API reference (not promise of stable interfaces): https://projectzomboid.com/modding/zombie/iso/IsoGridSquare.html ; https://projectzomboid.com/modding/zombie/iso/sprite/IsoSprite.html ; https://www.projectzomboid.com/modding/zombie/core/properties/TilePropertyKey.html
- Community 42.21/42.22.2 notes: https://hydecogames.com/tools/mapformats/
- Mapping tools: https://github.com/Unjammer/PZ_Mapping_Tools ; https://github.com/Z3R0-BYT3Z/PZ_Mapping_Tools
- Candidate external codec: https://github.com/guspuffygit/project-zomboid-tile-cli
- Viewpoint: https://docs.projectviewpoint.org/resource-packs/tiles/ ; https://docs.projectviewpoint.org/resource-packs/format/ ; https://docs.projectviewpoint.org/api/draw-callbacks/ ; https://steamcommunity.com/sharedfiles/filedetails/?id=3815223174
