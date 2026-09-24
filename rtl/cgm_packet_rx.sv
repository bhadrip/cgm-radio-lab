`default_nettype none

// Companion fixed-length parser used for loopback, BIST, and first-silicon test.
module cgm_packet_rx (
    input  logic        clk,
    input  logic        reset,
    input  logic        packet_start,
    input  logic [5:0]  channel,
    input  logic        rx_valid,
    input  logic        rx_bit,
    output logic        active,
    output logic        done,
    output logic        crc_ok,
    output logic        format_ok,
    output logic [47:0] advertiser_address,
    output logic [15:0] sample_sequence,
    output logic [15:0] glucose_mg_dl,
    output logic [15:0] trend_q8_8,
    output logic [7:0]  status,
    output logic [7:0]  battery_percent
);
    localparam logic [31:0] ACCESS_ADDRESS = 32'h8E89BED6;
    localparam integer PREAMBLE_BITS = 8;
    localparam integer BODY_START = 40;
    localparam integer CRC_START = 200;
    localparam integer PACKET_BITS = 224;

    logic [8:0] bit_index;
    logic plain_bit;
    logic whiten_valid;
    logic crc_valid;
    logic [23:0] crc_state;
    logic [23:0] received_crc;
    logic format_error;
    logic [7:0] body_byte_index;
    logic [2:0] body_bit_index;
    logic [4:0] crc_bit_index;

    function automatic logic octet_bit(
        input logic [7:0] octet,
        input logic [2:0] sub_index
    );
        begin
            octet_bit = octet[sub_index];
        end
    endfunction

    assign whiten_valid = active && rx_valid && (bit_index >= BODY_START);
    assign crc_valid = active && rx_valid && (bit_index >= BODY_START) && (bit_index < CRC_START);
    assign body_byte_index = (bit_index - BODY_START) >> 3;
    assign body_bit_index = (bit_index - BODY_START) & 3'h7;
    assign crc_bit_index = bit_index - CRC_START;

    ble_whitener dewhitener (
        .clk(clk),
        .reset(reset),
        .packet_start(packet_start),
        .channel(channel),
        .data_valid(whiten_valid),
        .data_in(rx_bit),
        .data_out(plain_bit)
    );

    ble_crc24 crc (
        .clk(clk),
        .reset(reset),
        .packet_start(packet_start),
        .crc_init(24'h555555),
        .data_valid(crc_valid),
        .data_in(plain_bit),
        .crc_state(crc_state)
    );

    always_ff @(posedge clk) begin
        if (reset) begin
            active <= 1'b0;
            done <= 1'b0;
            crc_ok <= 1'b0;
            format_ok <= 1'b0;
            bit_index <= 9'd0;
            received_crc <= 24'd0;
            format_error <= 1'b0;
            advertiser_address <= 48'd0;
            sample_sequence <= 16'd0;
            glucose_mg_dl <= 16'd0;
            trend_q8_8 <= 16'd0;
            status <= 8'd0;
            battery_percent <= 8'd0;
        end else begin
            done <= 1'b0;
            if (packet_start) begin
                active <= 1'b1;
                bit_index <= 9'd0;
                received_crc <= 24'd0;
                format_error <= 1'b0;
                crc_ok <= 1'b0;
                format_ok <= 1'b0;
                advertiser_address <= 48'd0;
                sample_sequence <= 16'd0;
                glucose_mg_dl <= 16'd0;
                trend_q8_8 <= 16'd0;
                status <= 8'd0;
                battery_percent <= 8'd0;
            end else if (active && rx_valid) begin
                if (bit_index < PREAMBLE_BITS) begin
                    if (rx_bit != octet_bit(8'hAA, bit_index[2:0])) begin
                        format_error <= 1'b1;
                    end
                end else if (bit_index < BODY_START) begin
                    if (rx_bit != ACCESS_ADDRESS[bit_index - PREAMBLE_BITS]) begin
                        format_error <= 1'b1;
                    end
                end else if (bit_index < CRC_START) begin
                    case (body_byte_index)
                        8'd0: if (plain_bit != octet_bit(8'h42, body_bit_index)) format_error <= 1'b1;
                        8'd1: if (plain_bit != octet_bit(8'h12, body_bit_index)) format_error <= 1'b1;
                        8'd2, 8'd3, 8'd4, 8'd5, 8'd6, 8'd7:
                            advertiser_address[((body_byte_index - 8'd2) * 8) + body_bit_index] <= plain_bit;
                        8'd8: if (plain_bit != octet_bit(8'h0B, body_bit_index)) format_error <= 1'b1;
                        8'd9: if (plain_bit != octet_bit(8'hFF, body_bit_index)) format_error <= 1'b1;
                        8'd10: if (plain_bit != octet_bit(8'hFF, body_bit_index)) format_error <= 1'b1;
                        8'd11: if (plain_bit != octet_bit(8'hFF, body_bit_index)) format_error <= 1'b1;
                        8'd12, 8'd13:
                            sample_sequence[((body_byte_index - 8'd12) * 8) + body_bit_index] <= plain_bit;
                        8'd14, 8'd15:
                            glucose_mg_dl[((body_byte_index - 8'd14) * 8) + body_bit_index] <= plain_bit;
                        8'd16, 8'd17:
                            trend_q8_8[((body_byte_index - 8'd16) * 8) + body_bit_index] <= plain_bit;
                        8'd18: status[body_bit_index] <= plain_bit;
                        8'd19: battery_percent[body_bit_index] <= plain_bit;
                        default: format_error <= 1'b1;
                    endcase
                end else begin
                    received_crc[23 - crc_bit_index] <= plain_bit;
                end

                if (bit_index == PACKET_BITS - 1) begin
                    active <= 1'b0;
                    done <= 1'b1;
                    crc_ok <= ({received_crc[23:1], plain_bit} == crc_state);
                    format_ok <= !format_error;
                    bit_index <= 9'd0;
                end else begin
                    bit_index <= bit_index + 1'b1;
                end
            end
        end
    end
endmodule

`default_nettype wire
