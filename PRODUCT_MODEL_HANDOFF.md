# ASTAR reference-style interactive model

Open http://127.0.0.1:8783/product/ while the local server is running. On a later session, double-click `start-product.bat`.

The final presentation follows the supplied exploded-device image: a light studio backdrop, dark enclosure, separated component layers and fine callouts. Navigation panels, dashboard cards and persistent controls are hidden. Mobile shows the unobstructed model without callout text. All geometry remains interactive.

Drag to orbit, scroll/pinch to zoom, right-drag/two-finger drag to pan. Double-click a part to isolate it; Escape restores the assembly. Space or a double-click on empty space assembles/explodes. R resets the camera. Arrow keys cycle parts; Enter isolates. S downloads the assembled GLB.

## Verification completed

`tests/product-render-browser.cjs` passed. Its machine-readable result is `test-results/product/render-validation.json`.

- All 37 named component groups selected by keyboard and clicked through actual raycasting in isolated views.
- Assembled, exploded, isolation, restoration, orbit, zoom, pan and empty-space selection clearing passed.
- Mobile tested at 390 × 844; model fit, absence of horizontal overflow and double-click isolation passed.
- A fresh page loaded with all non-local requests blocked.
- GLB export passed: 19,941,904 bytes, glTF 2 binary, all 37 component identities retained. Export uses assembled positions, restored materials and metre scaling.
- No browser JavaScript errors in the final test. Python and JavaScript syntax checks passed.
- Final desktop and mobile screenshots were visually inspected.

The saved GLB is `test-results/product/ASTAR-engineering-concept.glb`. Current screenshots are `render-exploded-desktop.png`, `render-assembled-desktop.png`, and `render-mobile.png` in the same directory. Earlier screenshots without the `render-` prefix show superseded presentations.

## Design scope

The geometry follows the latest 4.2-inch Waveshare / ESP32-S3 / three-button / LiPo / solar brief. The supplied visual reference guides the presentation; its LiFePO4 label and optional speaker were not silently substituted for the current specified battery and component list. Display active area and module outline use the referenced Waveshare dimensions; other envelopes and circuitry remain clearly marked estimates in `static/product/README.md` and the component metadata.

Solar is lifted and turned outward for inspection, then restored to the rear in assembled mode. The inspection layout is not a literal physical removal-order animation. This is an engineering visualization, not validated manufacturing CAD.

Three.js is bundled locally under its MIT licence. Rendering pauses when the camera and model are stationary; reduced-motion preferences remove animated transitions. The textbook app remains accessible at the server root, with an Explore the device navigation link.
