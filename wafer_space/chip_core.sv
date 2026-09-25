// SPDX-License-Identifier: Apache-2.0

`default_nettype none

// Drop-in chip_core for the wafer.space GF180MCU project template.
// The pin map targets the smallest 0p5x0p5 slot.
module chip_core #(
    parameter NUM_INPUT_PADS = 4,
    parameter NUM_BIDIR_PADS = 38,
    parameter NUM_ANALOG_PADS = 4
) (
`ifdef USE_POWER_PINS
    inout wire VDD,
    inout wire VSS,
`endif
    input  wire                         clk,
    input  wire                         rst_n,
    input  wire [NUM_INPUT_PADS-1:0]    input_in,
    output wire [NUM_INPUT_PADS-1:0]    input_pu,
    output wire [NUM_INPUT_PADS-1:0]    input_pd,
    input  wire [NUM_BIDIR_PADS-1:0]    bidir_in,
    output wire [NUM_BIDIR_PADS-1:0]    bidir_out,
    output wire [NUM_BIDIR_PADS-1:0]    bidir_oe,
    output wire [NUM_BIDIR_PADS-1:0]    bidir_cs,
    output wire [NUM_BIDIR_PADS-1:0]    bidir_sl,
    output wire [NUM_BIDIR_PADS-1:0]    bidir_ie,
    output wire [NUM_BIDIR_PADS-1:0]    bidir_pu,
    output wire [NUM_BIDIR_PADS-1:0]    bidir_pd,
    inout  wire [NUM_ANALOG_PADS-1:0]   analog
);
    wire [7:0] read_data;
    wire packet_out;
    wire packet_valid;
    wire frequency_valid;
    wire signed [18:0] frequency_offset_hz;
    wire busy;
    wire interrupt;
    wire bist_pass;

    assign input_pu = '0;
    assign input_pd = '0;

    // bidir[11:0] are inputs; bidir[37:12] are outputs.
    assign bidir_oe = {{(NUM_BIDIR_PADS-12){1'b1}}, 12'b0};
    assign bidir_ie = ~bidir_oe;
    assign bidir_cs = '0;
    assign bidir_sl = '1;
    assign bidir_pu = '0;
    assign bidir_pd = '0;

    wire [NUM_BIDIR_PADS-1:0] legacy_bidir_out = {
        {(NUM_BIDIR_PADS-25){1'b0}},
        read_data,
        bist_pass,
        interrupt,
        busy,
        packet_valid,
        packet_out,
        12'b0
    };
    wire [NUM_BIDIR_PADS-1:0] gfsk_bidir_out = {
        1'b0,
        packet_valid,
        packet_out,
        bist_pass,
        interrupt,
        busy,
        frequency_valid,
        frequency_offset_hz,
        12'b0
    };
    assign bidir_out = input_in[2] ? gfsk_bidir_out : legacy_bidir_out;

    cgm_chip_core core (
        .clk(clk),
        .reset(~rst_n),
        .write_enable(input_in[0]),
        .read_enable(input_in[1]),
        .register_address(bidir_in[3:0]),
        .write_data(bidir_in[11:4]),
        .read_data(read_data),
        .packet_out(packet_out),
        .packet_valid(packet_valid),
        .frequency_valid(frequency_valid),
        .frequency_offset_hz(frequency_offset_hz),
        .busy(busy),
        .interrupt(interrupt),
        .bist_pass(bist_pass)
    );

    wire _unused = &{input_in[NUM_INPUT_PADS-1:3],
                     bidir_in[NUM_BIDIR_PADS-1:12], analog};
endmodule

`default_nettype wire
