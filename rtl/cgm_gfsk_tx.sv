`default_nettype none

// Complete digital BLE LE 1M transmit path from a CGM measurement to a
// Gaussian-shaped instantaneous-frequency stream. The packet serializer only
// advances when the modulator accepts the next 1 us symbol.
module cgm_gfsk_tx (
    input  logic               clk,
    input  logic               reset,
    input  logic               start,
    input  logic [5:0]         channel,
    input  logic [47:0]        advertiser_address,
    input  logic [15:0]        sample_sequence,
    input  logic [15:0]        glucose_mg_dl,
    input  logic [15:0]        trend_q8_8,
    input  logic [7:0]         status,
    input  logic [7:0]         battery_percent,
    output logic               busy,
    output logic               symbol_valid,
    output logic               symbol_bit,
    output logic               symbol_last,
    output logic               frequency_valid,
    output logic signed [18:0] frequency_offset_hz,
    output logic               done
);
    logic packet_busy;
    logic packet_valid;
    logic packet_bit;
    logic packet_last;
    logic bit_ready;
    logic frequency_first;
    logic frequency_last;
    logic final_symbol_pending;
    logic final_symbol_active;

    assign busy = packet_busy || frequency_valid;

    cgm_packet_tx packetizer (
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
        .tx_ready(bit_ready),
        .busy(packet_busy),
        .tx_valid(packet_valid),
        .tx_bit(packet_bit),
        .tx_last(packet_last),
        .done()
    );

    ble_gfsk_modulator modulator (
        .clk(clk),
        .reset(reset),
        .bit_valid(packet_valid),
        .bit_in(packet_bit),
        .bit_ready(bit_ready),
        .sample_valid(frequency_valid),
        .sample_first(frequency_first),
        .sample_last(frequency_last),
        .frequency_offset_hz(frequency_offset_hz)
    );

    always_ff @(posedge clk) begin
        if (reset) begin
            final_symbol_pending <= 1'b0;
            final_symbol_active <= 1'b0;
            symbol_valid <= 1'b0;
            symbol_bit <= 1'b0;
            symbol_last <= 1'b0;
            done <= 1'b0;
        end else begin
            done <= 1'b0;
            symbol_valid <= 1'b0;
            if (packet_valid && bit_ready && packet_last) begin
                final_symbol_pending <= 1'b1;
            end
            if (packet_valid && bit_ready) begin
                symbol_valid <= 1'b1;
                symbol_bit <= packet_bit;
                symbol_last <= packet_last;
            end
            if (final_symbol_pending && frequency_valid && frequency_first) begin
                final_symbol_pending <= 1'b0;
                final_symbol_active <= 1'b1;
            end
            if (final_symbol_active && frequency_valid && frequency_last) begin
                final_symbol_active <= 1'b0;
                done <= 1'b1;
            end
        end
    end
endmodule

`default_nettype wire
