`default_nettype none

// Synthesizable packet-level loop with a single hard-error injection point.
module cgm_packet_loop (
    input  logic        clk,
    input  logic        reset,
    input  logic        start,
    input  logic [5:0]  channel,
    input  logic [47:0] advertiser_address,
    input  logic [15:0] sample_sequence,
    input  logic [15:0] glucose_mg_dl,
    input  logic [15:0] trend_q8_8,
    input  logic [7:0]  status,
    input  logic [7:0]  battery_percent,
    input  logic        inject_error,
    output logic        tx_busy,
    output logic        tx_valid,
    output logic        tx_bit,
    output logic        tx_last,
    output logic        rx_done,
    output logic        rx_crc_ok,
    output logic        rx_format_ok,
    output logic [47:0] rx_advertiser_address,
    output logic [15:0] rx_sample_sequence,
    output logic [15:0] rx_glucose_mg_dl,
    output logic [15:0] rx_trend_q8_8,
    output logic [7:0]  rx_status,
    output logic [7:0]  rx_battery_percent
);
    logic tx_done;
    logic channel_bit;
    logic accepted_start;

    assign accepted_start = start && !tx_busy;
    assign channel_bit = tx_bit ^ inject_error;

    cgm_packet_tx transmitter (
        .clk(clk),
        .reset(reset),
        .start(start),
        .channel(channel),
        .advertiser_address(advertiser_address),
        .sample_sequence(sample_sequence),
        .glucose_mg_dl(glucose_mg_dl),
        .trend_q8_8(trend_q8_8),
        .status(status),
        .battery_percent(battery_percent),
        .tx_ready(1'b1),
        .busy(tx_busy),
        .tx_valid(tx_valid),
        .tx_bit(tx_bit),
        .tx_last(tx_last),
        .done(tx_done)
    );

    cgm_packet_rx receiver (
        .clk(clk),
        .reset(reset),
        .packet_start(accepted_start),
        .channel(channel),
        .rx_valid(tx_valid),
        .rx_bit(channel_bit),
        .active(),
        .done(rx_done),
        .crc_ok(rx_crc_ok),
        .format_ok(rx_format_ok),
        .advertiser_address(rx_advertiser_address),
        .sample_sequence(rx_sample_sequence),
        .glucose_mg_dl(rx_glucose_mg_dl),
        .trend_q8_8(rx_trend_q8_8),
        .status(rx_status),
        .battery_percent(rx_battery_percent)
    );
endmodule

`default_nettype wire
