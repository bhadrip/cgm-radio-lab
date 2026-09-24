`default_nettype none

// BLE data whitening/dewhitening primitive. Bits arrive in on-air order.
module ble_whitener (
    input  logic       clk,
    input  logic       reset,
    input  logic       packet_start,
    input  logic [5:0] channel,
    input  logic       data_valid,
    input  logic       data_in,
    output logic       data_out
);
    logic [6:0] lfsr;
    wire [6:0] shifted;

    assign data_out = data_in ^ lfsr[0];
    assign shifted = {1'b0, lfsr[6:1]} ^ (lfsr[0] ? 7'h44 : 7'h00);

    always_ff @(posedge clk) begin
        if (reset) begin
            lfsr <= 7'h40;
        end else if (packet_start) begin
            lfsr <= {1'b1, channel};
        end else if (data_valid) begin
            lfsr <= shifted;
        end
    end
endmodule

`default_nettype wire
