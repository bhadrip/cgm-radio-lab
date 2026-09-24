# GF180 sign-off checkpoint

- Magic DRC errors: 0
- KLayout DRC errors: 0
- KLayout density errors: 0
- KLayout antenna errors: 0
- Magic/KLayout XOR differences: 0
- LVS errors: 0
- Illegal overlaps: 0
- Setup violations: 0
- Hold violations: 0
- Worst setup slack: +1.197 ns at `max_ss_125C_4v50`
- Worst hold slack: +0.235 ns at `min_ff_n40C_5v50`
- Maximum slew violations: 519
- Maximum capacitance violations: 92
- Synthesized logic cells: 3,267
- Synthesized standard-cell area: 73,987 um^2

The KLayout configuration follows the official Wafer.Space template: antenna
and density use dedicated decks, and CUP checks are excluded for the selected
non-CUP pad library. Decks run serially because parallel result aggregation was
nondeterministic in the pinned tool image.

The 16 MHz clock matches `spec.yaml`. This checkpoint includes the packet
engine and digital GFSK path, produces GDS, passes physical verification, and
is setup/hold clean. It is not submission-ready: maximum slew and capacitance
warnings remain, and the prototype still lacks the PLL/DCO, PA, RF, product,
package, and qualification work listed in the engineering basis.
