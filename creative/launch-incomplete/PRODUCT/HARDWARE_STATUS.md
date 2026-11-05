# Hardware source of truth

Read in full: supplied ASTAR_V0.1_Software_and_Hardware_Build_Guide.docx and ASTAR.pdf. The build guide governs the next prototype: ESP32-S3-DevKitC-1, 2.13-inch 250x122-class SPI e-paper, microSD module/card, seven buttons, USB power, breadboard/modules. It expressly defers solar, battery and custom PCB design.

The earlier pitch's ESP32-C3, price estimates, large display, solar illustration and three-button imagery describe an older vision. They are not the V0 build specification. Legacy renders are retained only in design references.

The new industrial concept assumes a 190 x 120 x 18 mm envelope with seven buttons and a larger future display. These are visual design choices, not measured fit, purchase specifications or manufacturable CAD. The exploded view and component layout are schematic. Exact large display, battery, charger, protective circuit, PCB and enclosure material are undecided. No device assembly, firmware, battery runtime, solar autonomy, environmental protection or drop performance was tested.

The supplied GPIO table is incomplete: microSD MISO is omitted. No wiring chart is supplied here. The official Espressif DevKitC-1 v1.0 guide confirms module-board architecture, exposed GPIO, USB power and board regulation, but exact board revision and module voltages must be selected before wiring. The guide's display example is a Pico-oriented module, so the exact ESP32-compatible SPI breakout/revision remains a procurement decision.

Official references checked 2026-11-02:
- https://docs.espressif.com/projects/esp-dev-kits/en/latest/esp32s3/esp32-s3-devkitc-1/user_guide_v1.0.html
- https://www.waveshare.com/wiki/Pico-ePaper-2.13 (access returned 403; module figures retained only as supplied-guide specifications, not independently verified measurements)

Required engineering work: choose exact modules, complete pin mapping and schematic, inspect voltage compatibility, test USB-powered subsystems, implement minimal capsule reader, measure use-cycle energy, then select solar/storage/charging components. The 1 W panel in the guide is an untested hypothesis and is not used as a launch claim.
