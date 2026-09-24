`default_nettype none

// Streaming BLE CRC-24 engine for an LSB-first input stream.
module ble_crc24 (
    input  logic        clk,
    input  logic        reset,
    input  logic        packet_start,
    input  logic [23:0] crc_init,
    input  logic        data_valid,
    input  logic        data_in,
    output logic [23:0] crc_state
);
    wire feedback;
    wire [23:0] next_state;

    assign feedback = crc_state[23] ^ data_in;
    assign next_state = {crc_state[22:0], 1'b0}
                      ^ (feedback ? 24'h00065B : 24'h000000);

    always_ff @(posedge clk) begin
        if (reset) begin
            crc_state <= 24'h555555;
        end else if (packet_start) begin
            crc_state <= crc_init;
        end else if (data_valid) begin
            crc_state <= next_state;
        end
    end
endmodule

`default_nettype wire
