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
- Worst setup slack: +8.229 ns at `max_ss_125C_4v50`
- Maximum slew violations: 405
- Maximum capacitance violations: 84

The KLayout configuration follows the official Wafer.Space template: antenna
and density use dedicated decks, and CUP checks are excluded for the selected
non-CUP pad library. Decks run serially because parallel result aggregation was
nondeterministic in the pinned tool image.

The 16 MHz clock now matches `spec.yaml`, and the pad-facing register read is a
one-cycle synchronous transaction. This checkpoint produces GDS, passes
physical verification, and is setup/hold clean. It is not submission-ready:
maximum slew and capacitance warnings remain, and the prototype still lacks the
RF, product, package, and qualification work listed in the engineering basis.
