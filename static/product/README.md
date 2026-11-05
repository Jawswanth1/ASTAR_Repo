# ASTAR interactive engineering explorer

Open `/product/` from the ASTAR local server, or double-click `start-product.bat` in the project root. Three.js 0.180.0 and its MIT licence are bundled in `vendor/`; the visualization needs no external network requests or build step.

## Render-only presentation

The current default follows the supplied exploded product reference: a light studio background, dark enclosure, vertically separated layers, restrained component callouts and no surrounding application interface. Callouts are omitted at narrow mobile widths so the model remains unobstructed. This supersedes the earlier dark workbench interface.

The solar assembly is lifted above the device and turned outward in the inspection layout so its cells can be seen. Assembling returns it to its rear-facing position. The exploded sequence explains the parts; it is not a literal removal-order animation.

## Explore

- Drag to orbit, scroll/pinch to zoom, right-drag/two-finger drag to pan.
- Press **Space** to switch between assembled and exploded views. **A** assembles; **E** explodes.
- Click geometry to select a component. **Left/Right arrows** cycle through all 37 parts for keyboard access.
- The selected component is highlighted while surrounding parts become translucent.
- Double-click a component, or press **I / Enter** after selecting it, to isolate it and fit the camera.
- Double-click empty space to switch assembly state without a keyboard.
- **R** resets the camera. **Escape** restores all components and clears selection.
- Clicking empty space clears selection.
- **S** exports an assembled GLB with metre units, part names and concept metadata, regardless of the current exploded or isolated state.

The 33 requested component categories are represented as 37 independently selectable groups because the three navigation switches and their three caps are individually modelled. Repeated screws, posts, wires, solder joints and related hardware are selectable as named sets.

## Engineering basis

This model follows the latest 4.2-inch display / three-button / solar brief. Older V0 seven-button and 2.13-inch build documents remain historical references; they were not silently rewritten.

| Item | Reference or assumption |
| --- | --- |
| Display module | Waveshare 4.2-inch e-Paper Module, SKU 13353. Reference driver outline 103 × 78.5 mm; active area 84.8 × 63.6 mm; 400 × 300 pixels. Revision-specific details must be checked before procurement. |
| Controller | Waveshare ESP32-S3 development-board reference; modelled board envelope approximately 25 × 55 mm. Shield, antenna, headers and bridge are representative. |
| Body | 124 × 90 mm nominal outline, 6.03-inch diagonal, approximately 24 mm depth excluding small protrusions. Estimated concept. |
| Battery | 3.7 V, approximately 480 mAh requirement; estimated 36 × 28 × 4.8 mm pouch. No exact cell selected. |
| Solar | 5 V / 1 W nominal target; 105 × 65 mm estimated rear laminate. Output and runtime have not been tested. |
| Power electronics | Separate conceptual protection, solar charging, power-path and 3.3 V regulator areas. Not a validated schematic or set of selected modules. |
| Wiring | Relationships and routing are illustrative. No pin assignments or safe charging claims are implied. |

Screen content is an illustrative mathematics lesson, not an extracted textbook page. Display rendering uses a supersampled texture for legibility; hardware resolution remains the referenced 400 × 300.

Sources checked for this model:

- https://www.waveshare.com/4.2inch-e-paper-module.htm
- https://www.waveshare.com/wiki/4.2inch_e-Paper_Module_Manual
- https://www.waveshare.com/product/esp32-s3-dev-kit-n8r8.htm
- https://threejs.org/docs/

## Files and validation

`parts.js` contains the component descriptions, relationships and accuracy notes. `model.js` creates separate, named geometry in millimetres. `explorer.js` handles raycasting, state, controls, camera transitions and GLB export. `product.css` and `index.html` provide the responsive interface. The existing Python server serves these assets without changing textbook APIs.

The current browser regression is `tests/product-render-browser.cjs` in the project root. Its saved results and screenshots are in `test-results/product/`. It exercises all parts through keyboard navigation and actual raycast clicks while isolated, the absence of persistent interface panels, assembly states, viewport fit, camera controls, clearing selection, mobile width, network independence, and GLB structure.

This is an engineering visualization, not validated manufacturing CAD. Exact mechanical fit, electrical compatibility, battery safety, tolerances, sealing, tooling and runtime require hardware engineering and physical validation.
