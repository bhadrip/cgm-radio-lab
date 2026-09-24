`default_nettype none

// Fixed-purpose CGM advertising packet serializer for the first silicon path.
// The manufacturer identifier 0xFFFF is reserved for laboratory testing.
module cgm_packet_tx (
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
    input  logic        tx_ready,
    output logic        busy,
    output logic        tx_valid,
    output logic        tx_bit,
    output logic        tx_last,
    output logic        done
);
    localparam logic [31:0] ACCESS_ADDRESS = 32'h8E89BED6;
    localparam integer PREAMBLE_BITS = 8;
    localparam integer ACCESS_BITS = 32;
    localparam integer BODY_BYTES = 20;
    localparam integer BODY_BITS = BODY_BYTES * 8;
    localparam integer CRC_BITS = 24;
    localparam integer BODY_START = PREAMBLE_BITS + ACCESS_BITS;
    localparam integer CRC_START = BODY_START + BODY_BITS;
    localparam integer PACKET_BITS = CRC_START + CRC_BITS;

    logic [8:0] bit_index;
    logic raw_bit;
    logic whitened_bit;
    logic [23:0] crc_state;
    logic accepted_start;
    logic whiten_valid;
    logic crc_valid;
    logic [7:0] body_byte_index;
    logic [2:0] body_bit_index;
    logic [4:0] crc_bit_index;
    logic accepted_bit;

    function automatic logic octet_bit(
        input logic [7:0] octet,
        input logic [2:0] sub_index
    );
        begin
            octet_bit = octet[sub_index];
        end
    endfunction

    function automatic logic selected_body_bit(
        input logic [7:0] byte_index,
        input logic [2:0] sub_index
    );
        begin
            case (byte_index)
                8'd0: selected_body_bit = octet_bit(8'h42, sub_index);
                8'd1: selected_body_bit = octet_bit(8'h12, sub_index);
                8'd2, 8'd3, 8'd4, 8'd5, 8'd6, 8'd7:
                    selected_body_bit = advertiser_address[((byte_index - 8'd2) * 8) + sub_index];
                8'd8: selected_body_bit = octet_bit(8'h0B, sub_index);
                8'd9: selected_body_bit = octet_bit(8'hFF, sub_index);
                8'd10: selected_body_bit = octet_bit(8'hFF, sub_index);
                8'd11: selected_body_bit = octet_bit(8'hFF, sub_index);
                8'd12, 8'd13:
                    selected_body_bit = sample_sequence[((byte_index - 8'd12) * 8) + sub_index];
                8'd14, 8'd15:
                    selected_body_bit = glucose_mg_dl[((byte_index - 8'd14) * 8) + sub_index];
                8'd16, 8'd17:
                    selected_body_bit = trend_q8_8[((byte_index - 8'd16) * 8) + sub_index];
                8'd18: selected_body_bit = status[sub_index];
                8'd19: selected_body_bit = battery_percent[sub_index];
                default: selected_body_bit = 1'b0;
            endcase
        end
    endfunction

    assign accepted_start = start && !busy;
    assign accepted_bit = busy && tx_ready;
    assign tx_valid = busy;
    assign tx_last = busy && (bit_index == PACKET_BITS - 1);
    assign body_byte_index = (bit_index - BODY_START) >> 3;
    assign body_bit_index = (bit_index - BODY_START) & 3'h7;
    assign crc_bit_index = bit_index - CRC_START;
    assign whiten_valid = accepted_bit && (bit_index >= BODY_START);
    assign crc_valid = accepted_bit && (bit_index >= BODY_START) && (bit_index < CRC_START);

    always @* begin
        raw_bit = 1'b0;
        if (bit_index < PREAMBLE_BITS) begin
            raw_bit = octet_bit(8'hAA, bit_index[2:0]);
        end else if (bit_index < BODY_START) begin
            raw_bit = ACCESS_ADDRESS[bit_index - PREAMBLE_BITS];
        end else if (bit_index < CRC_START) begin
            raw_bit = selected_body_bit(body_byte_index, body_bit_index);
        end else begin
            raw_bit = crc_state[23 - crc_bit_index];
        end
    end

    assign tx_bit = bit_index < BODY_START ? raw_bit : whitened_bit;

    ble_whitener whitener (
        .clk(clk),
        .reset(reset),
        .packet_start(accepted_start),
        .channel(channel),
        .data_valid(whiten_valid),
        .data_in(raw_bit),
        .data_out(whitened_bit)
    );

    ble_crc24 crc (
        .clk(clk),
        .reset(reset),
        .packet_start(accepted_start),
        .crc_init(24'h555555),
        .data_valid(crc_valid),
        .data_in(raw_bit),
        .crc_state(crc_state)
    );

    always_ff @(posedge clk) begin
        if (reset) begin
            busy <= 1'b0;
            bit_index <= 9'd0;
            done <= 1'b0;
        end else begin
            done <= 1'b0;
            if (accepted_start) begin
                busy <= 1'b1;
                bit_index <= 9'd0;
            end else if (accepted_bit) begin
                if (bit_index == PACKET_BITS - 1) begin
                    busy <= 1'b0;
                    bit_index <= 9'd0;
                    done <= 1'b1;
                end else begin
                    bit_index <= bit_index + 1'b1;
                end
            end
        end
    end
endmodule

`default_nettype wire
