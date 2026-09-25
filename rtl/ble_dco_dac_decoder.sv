`default_nettype none

// Register the 7-bit fast-DAC code into 31 thermometer MSB controls and two
// binary LSB controls. The final register bank prevents combinational decoder
// hazards from reaching the analog switches; physical output skew is a separate
// place-and-route constraint.
module ble_dco_dac_decoder (
    input  logic        clk,
    input  logic        reset,
    input  logic        code_valid,
    input  logic [6:0]  modulation_code,
    output logic        control_valid,
    output logic [30:0] thermometer_msb,
    output logic [1:0]  binary_lsb
);
    integer element;

    always_ff @(posedge clk) begin
        if (reset) begin
            control_valid <= 1'b0;
            thermometer_msb <= '0;
            binary_lsb <= '0;
        end else begin
            control_valid <= 1'b0;
            if (code_valid) begin
                control_valid <= 1'b1;
                binary_lsb <= modulation_code[1:0];
                for (element = 0; element < 31; element = element + 1) begin
                    thermometer_msb[element] <= modulation_code[6:2] > element;
                end
            end
        end
    end
endmodule

`default_nettype wire
