# GF180 routed checkpoint

- Status: passed through `OpenROAD.DetailedRouting`
- Detailed-route DRC errors: 0
- Antenna violations: 0
- Power-grid violations: 0
- Routed wire length: 367,758 um
- Vias: 36,123
- Core utilization: 44.76%
- Placed standard-cell instances: 17,776
- Timing-repair buffers: 2,436
- Setup/hold violations before extraction: 0 / 0

This checkpoint has a legal detailed route, but it is not sign-off. Timing
is clean before extraction, but extracted post-route STA has not run. GDS
generation, fill, foundry DRC, LVS, density, and the official Wafer.Space
precheck also remain outstanding.
