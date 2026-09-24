# GF180 ring-oscillator feasibility

## Decision

Do not use the tested three-stage ring as the BLE local oscillator. It cannot
cover 2402--2480 MHz across the tested PVT corners, even before layout
parasitics are added.

## Experiment

The ngspice bench uses GF180MCU `nfet_03v3` and `pfet_03v3` devices at 1.8 V,
minimum 0.28 um channel length, and three single-ended inverter stages. It
sweeps 0--80 fF of explicit load per stage at typical/25 C, fast/-40 C, and
slow/125 C. Zero explicit load is an optimistic schematic-only ceiling; device
capacitance remains in the model.

| Corner | Maximum frequency | Power at maximum | BLE band covered? |
|---|---:|---:|:---:|
| Typical, 25 C | 2.420 GHz | 152 uW | No |
| Fast, -40 C | 3.630 GHz | 220 uW | Yes, within the swept load envelope |
| Slow, 125 C | 1.583 GHz | 103 uW | No |

At typical conditions, adding only 1 fF per stage reduces frequency to
2.100 GHz. The unloaded typical case does not reach the 2480 MHz top channel,
and the unloaded slow case misses the entire BLE band by more than 800 MHz.

## Scope

These are schematic transient results, not oscillator qualification. The bench
does not measure phase noise, modulation bandwidth, pulling, startup yield,
supply sensitivity, radiation, or extracted layout behavior. Its valid use is
to reject this topology before spending effort on layout.

Reproduce the data with `make analog-test`. Machine-readable results are in
`ring_dco_sweep.json` and `ring_dco_sweep.csv` in this directory.
