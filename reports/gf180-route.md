# GF180 routed checkpoint

- Status: passed through `OpenROAD.DetailedRouting`
- Detailed-route DRC errors: 0
- Antenna violations: 0
- Power-grid violations: 0
- Routed wire length: 278,269 um
- Vias: 26,025
- Core utilization: 42.47%
- Standard cells after repair and clock-tree synthesis: 16,408
- Timing-repair buffers: 1,918

This checkpoint has a legal detailed route, but it is not sign-off. Timing
repair reported unresolved setup paths before routing; extracted post-route STA
has not run. GDS generation, fill, foundry DRC, LVS, density, and the official
Wafer.Space precheck also remain outstanding.
