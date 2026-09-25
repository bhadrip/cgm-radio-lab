# GF180 floorplan result

- Status: passed through `OpenROAD.Floorplan`
- Slot: Wafer.Space `0p5x0p5`
- Template: `0de7e394337a1f7f5303ac7a3681bf2481b58176`
- PDK: `gf180mcuD` at `026824c7969ce6f4fc9678e6ca04b0a06a596c4b`
- Standard cells: 3,267
- Sequential cells: 445
- Standard-cell area: 73,987 um^2
- Core utilization after floorplan: 4.62%
- Pre-PnR setup/hold violations: 0 / 0
- Worst pre-PnR setup slack: 27.406 ns
- Worst pre-PnR hold slack: 0.206 ns

This is an early feasibility checkpoint, not a tapeout result. The design still
has 48 width/unused lint warnings and pre-PnR slew, fanout, and capacitance
violations. Placement, clock tree, routing, extracted timing, DRC, LVS, the
Wafer.Space precheck, RF, and analog blocks have not run.
