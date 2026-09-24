# Visual refinement direction

Author's direction, 23 September 2026: move from the spatial sketch toward photographic realism and capture the bleak industrial environment, with chemical works and sewage in the river. Bounded movement on the bridge is now implemented; this requires true 3D parallax rather than a single fixed panoramic image.

The first atmosphere pass is implemented: muted overcast sky, diffuse lighting, distance haze, uneven procedural brick weathering, exposed mud and dull grey-brown water. These are interpretations, not recovered photographic colours or measured pollution. Keep the horizon and factory details readable instead of making the whole scene underexposed.

## Earlier surface pass, 24 September 2026

- Replaced the repeated factory roof treatment with stepped pitched ranges, selected roof ventilators, loading doors, eaves gutters and rainwater pipes. Curved parapets are confined to the northern site-253 studies. Existing mapped envelopes remain; roof divisions and facade assignments are still interpretations, not identified photo matches.
- Added original deterministic brick, slate, timber, stone and mud colour/bump textures with consistent metre-based coordinates, including roof lofts and cylindrical chimneys. Material shaders add broad weathering and damp bases. No reference photo is published or used as a texture.
- Added directional shadow mapping, overcast environment lighting and a soft contact-shading atlas derived from the existing building envelopes. These shading marks are not historical evidence. The static shadow map is calculated once.
- Subdivided the existing bed relief, smoothed shared normals and replaced periodic ridges with irregular noise. Channel outlines are unchanged. Low mud is darker and less rough; dry mud remains matte.
- Replaced the striped water texture with a camera-dependent planar reflection of the actual scene, restrained ripple distortion and fine surface variation. The 512 × 384 reflection target is rendered on view changes and movement, with no continuous water animation.
- Preserved three before-pass desktop images in `review/before-realism/`. Current review images include `south-scene.png` and `north-scene.png`. Full interaction checks passed; a subsequent focused review checks final surface refinements, both bridge sides, desktop/mobile layouts and shader errors.

That earlier pass used 17 draw calls and about 1.09 million triangles; reflections add 16 calls and about 1.09 million triangles. Low draw-call counts do not establish phone performance. The sky, lighting and buildings remain schematic; the result is not photorealistic.

## Latest terrain and context pass

The [terrain record](TERRAIN.md) supersedes the earlier flat-bed method and rendering counts: both river directions now use a continuous terrain mesh, inferred channels, shelves, rills and wet margins. Original generated sediment texture replaces the procedural mud colour tile; archive images remain reference-only. The south bank protects lower Mill Mead ground, with 19 plank sheds and irregular allotment rows. Coal loads have dense angular surfaces. Abbey Mill follows the author’s c1800-to-c1900 continuity hypothesis without a windmill. The southwest distance now has 15 approximate terrace groups and 20 industrial ranges; eight supplied maps are catalogued, with the 1905 map retained as a separately dated comparison.

Latest focused desktop review: 20 main-pass draw calls, about 4.2 million triangles, plus 19 reflection calls. Phone and website development are deferred by the author. The following longer-term priorities remain subject to that direction.

## Remaining priorities

Further work should proceed in this order:

1. Replace generic factory and mill masses with individual structures matched between the OS and the correctly identified photographs. Fix roof forms, bay spacing, chimneys and quays before adding small decoration. Use the northern 1902 view for the West Ham direction and the wide 1900 view for Bromley.
2. Build original or verified reusable materials at real-world scale: soot and rain staining, brick variation, roof slates, timber and damp retaining walls. Roughness and normal maps should carry fine detail. Archive photographs remain references unless publication rights are established.
3. Improve overcast lighting with soft contact shadows and ambient occlusion. Bake static lighting where useful for phone performance. Keep the bank and building bases grounded rather than relying on heavy fog to disguise simplified geometry.
4. Refine the channels, tidal mud and retaining edges against the photographs. Add subtle wet/dry variation and restrained water reflections; no bright blue water, exaggerated green pollution or invented floating waste. Garden divisions remain interpretive until a plan or closer photograph establishes them.
5. Review matching compositions from both bridge sides on desktop and a physical phone. Record which features are documented and which remain inferred. Optimise meshes and texture sizes before adding animation.

The current scene is still a study model, not photorealistic. High-resolution textures alone will not correct inaccurate silhouettes, scale, camera placement or lighting.

The subsequent [lighting and infrastructure pass](LIGHTING_AND_INFRASTRUCTURE.md) supersedes the earlier lighting setup and flat railway levels. It adds 50 map-traced road/lane studies with provisional grey/brown period surfaces, raised railway embankments and crossings, and separate Three Mills landmarks. The sediment mask now protects dry ground from wet-mud shading. Latest desktop exports and error checks are `review/lighting-*.png` and `review/lighting-checks.json`; earlier rendering counts describe earlier passes.
