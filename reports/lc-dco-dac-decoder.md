# LC-DCO fast-DAC decoder

## Result

The 7-bit fast modulation code now has a synthesizable, registered 6+1 decoder.
Bits 6:1 select a monotonic bank of 63 thermometer controls and bit 0 drives
the binary LSB control. All 64 analog controls update only on a valid
16 MHz clock edge and otherwise hold their prior value.

An exhaustive cocotb test checks all 128 input codes, thermometer population and
monotonic ordering, binary residue, invalid-cycle hold, and reset. Generic Yosys
synthesis reports 129 cells: 63 greater-than comparisons, 64 enabled register
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

The first [switched-current cell experiment](gf180-fast-dac.md) rejects its
analog switch topology on measured glitch. The
[current-steered follow-on](gf180-fast-dac-steered.md) establishes the 6+1 split
implemented here.

Run the exhaustive test through `make rtl-test` and reproduce the synthesis
summary with `make dco-dac-yosys-stat`. The latter writes
`dco-dac-yosys-stat.txt`.
