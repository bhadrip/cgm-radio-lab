# GF180 sign-off checkpoint

- Magic DRC errors: 0
- KLayout DRC errors: 0
- KLayout density errors: 0
- KLayout antenna errors: 0
- Magic/KLayout XOR differences: 0
- LVS errors: 0
- Illegal overlaps: 0
- Hold violations: 0
- Worst setup slack: -2.379 ns at `max_ss_125C_4v50`
- Setup violations: 101
- Maximum slew violations: 367
- Maximum capacitance violations: 79

The KLayout configuration follows the official Wafer.Space template: antenna
and density use dedicated decks, and CUP checks are excluded for the selected
non-CUP pad library. This checkpoint produces GDS and passes physical
verification, but it is not timing clean and is not ready for submission.
