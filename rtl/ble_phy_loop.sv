`default_nettype none

// First vertical slice: TX whitening -> hard-bit channel -> RX dewhitening,
// with independent CRC observations on each side of the channel.
module ble_phy_loop (
    input  logic        clk,
    input  logic        reset,
    input  logic        packet_start,
    input  logic [5:0]  channel,
    input  logic [23:0] crc_init,
    input  logic        data_valid,
    input  logic        crc_valid,
    input  logic        data_in,
    input  logic        inject_error,
    output logic        tx_bit,
    output logic        rx_bit,
    output logic [23:0] tx_crc_state,
    output logic [23:0] rx_crc_state
);
    logic impaired_bit;

    ble_whitener tx_whitener (
        .clk(clk),
        .reset(reset),
        .packet_start(packet_start),
        .channel(channel),
        .data_valid(data_valid),
        .data_in(data_in),
        .data_out(tx_bit)
    );

    assign impaired_bit = tx_bit ^ inject_error;

    ble_whitener rx_whitener (
        .clk(clk),
        .reset(reset),
        .packet_start(packet_start),
        .channel(channel),
        .data_valid(data_valid),
        .data_in(impaired_bit),
        .data_out(rx_bit)
    );

    ble_crc24 tx_crc (
        .clk(clk),
        .reset(reset),
        .packet_start(packet_start),
        .crc_init(crc_init),
        .data_valid(crc_valid),
        .data_in(data_in),
        .crc_state(tx_crc_state)
    );

    ble_crc24 rx_crc (
        .clk(clk),
        .reset(reset),
        .packet_start(packet_start),
        .crc_init(crc_init),
        .data_valid(crc_valid),
        .data_in(rx_bit),
        .crc_state(rx_crc_state)
    );
endmodule

`default_nettype wire

