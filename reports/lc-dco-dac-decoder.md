# LC-DCO fast-DAC decoder

## Result

The 7-bit fast modulation code now has a synthesizable, registered 5+2 decoder.
Bits 6:2 select a monotonic bank of 31 thermometer controls and bits 1:0 drive
the two binary-weighted controls. All 33 analog controls update only on a valid
16 MHz clock edge and otherwise hold their prior value.

An exhaustive cocotb test checks all 128 input codes, thermometer population and
monotonic ordering, binary residue, invalid-cycle hold, and reset. Generic Yosys
synthesis reports 65 cells: 31 greater-than comparisons, 32 enabled register
groups, one valid register, and one mux.

Registering the decoder output prevents combinational decode hazards from
propagating directly to the DAC switches. It also gives place and route a clear
final-stage register bank for the 750 ps output-skew constraint derived by the
[transition budget](lc-dco-dac-transition.md).

## Boundary

This is generic RTL synthesis, not a GF180 mapped timing, area, or power result.
It does not prove clock-tree skew, register-to-switch routing skew, analog switch
delay, charge injection, or the DAC output waveform. Those require mapped and
post-route timing plus transistor-level transient verification. Complete-chip
power and production evidence continue to follow the
[PR11 local verification report](https://github.com/bhadrip/cgm-radio-lab/blob/e58d49ba81c756ac0118f7782ccf35791c83b7d8/docs/pr11-local-verification-report.md).

The first [switched-current cell experiment](gf180-fast-dac.md) uses these
controls conceptually but rejects its analog switch topology on measured glitch.
The [current-steered follow-on](gf180-fast-dac-steered.md) passes only after
moving to a 6+1 split, so this 5+2 decoder is now a superseded prototype.

Run the exhaustive test through `make rtl-test` and reproduce the synthesis
summary with `make dco-dac-yosys-stat`. The latter writes
`dco-dac-yosys-stat.txt`.
