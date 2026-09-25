`default_nettype none

// Convert the signed instantaneous-frequency request into a calibrated DCO
// tuning code. First-order error feedback dithers adjacent codes when the
// requested offset falls between DCO steps.
module ble_dco_controller #(
    parameter integer DCO_GAIN_HZ_PER_LSB = 50000,
    parameter integer DCO_CODE_BITS = 12
) (
    input  logic                            clk,
    input  logic                            reset,
    input  logic                            frequency_valid,
    input  logic signed [18:0]              frequency_offset_hz,
    input  logic [DCO_CODE_BITS-1:0]        base_code,
    output logic                            code_valid,
    output logic [DCO_CODE_BITS-1:0]        dco_code,
    output logic                            saturated
);
    localparam integer DCO_CODE_MAX = (1 << DCO_CODE_BITS) - 1;

    integer residual_hz;
    integer combined_hz;
    integer step_code;
    integer candidate_code;
    integer next_residual_hz;
    logic [DCO_CODE_BITS-1:0] next_dco_code;
    logic next_saturated;

    always @* begin
        combined_hz = $signed(frequency_offset_hz) + residual_hz;
        if (combined_hz >= 11 * DCO_GAIN_HZ_PER_LSB / 2) begin
            step_code = 6;
        end else if (combined_hz >= 9 * DCO_GAIN_HZ_PER_LSB / 2) begin
            step_code = 5;
        end else if (combined_hz >= 7 * DCO_GAIN_HZ_PER_LSB / 2) begin
            step_code = 4;
        end else if (combined_hz >= 5 * DCO_GAIN_HZ_PER_LSB / 2) begin
            step_code = 3;
        end else if (combined_hz >= 3 * DCO_GAIN_HZ_PER_LSB / 2) begin
            step_code = 2;
        end else if (combined_hz >= DCO_GAIN_HZ_PER_LSB / 2) begin
            step_code = 1;
        end else if (combined_hz <= -11 * DCO_GAIN_HZ_PER_LSB / 2) begin
            step_code = -6;
        end else if (combined_hz <= -9 * DCO_GAIN_HZ_PER_LSB / 2) begin
            step_code = -5;
        end else if (combined_hz <= -7 * DCO_GAIN_HZ_PER_LSB / 2) begin
            step_code = -4;
        end else if (combined_hz <= -5 * DCO_GAIN_HZ_PER_LSB / 2) begin
            step_code = -3;
        end else if (combined_hz <= -3 * DCO_GAIN_HZ_PER_LSB / 2) begin
            step_code = -2;
        end else if (combined_hz <= -DCO_GAIN_HZ_PER_LSB / 2) begin
            step_code = -1;
        end else begin
            step_code = 0;
        end

        candidate_code = $signed({1'b0, base_code}) + step_code;
        next_saturated = 1'b0;
        case (step_code)
            -6: next_residual_hz = combined_hz + 6 * DCO_GAIN_HZ_PER_LSB;
            -5: next_residual_hz = combined_hz + 5 * DCO_GAIN_HZ_PER_LSB;
            -4: next_residual_hz = combined_hz + 4 * DCO_GAIN_HZ_PER_LSB;
            -3: next_residual_hz = combined_hz + 3 * DCO_GAIN_HZ_PER_LSB;
            -2: next_residual_hz = combined_hz + 2 * DCO_GAIN_HZ_PER_LSB;
            -1: next_residual_hz = combined_hz + DCO_GAIN_HZ_PER_LSB;
            1: next_residual_hz = combined_hz - DCO_GAIN_HZ_PER_LSB;
            2: next_residual_hz = combined_hz - 2 * DCO_GAIN_HZ_PER_LSB;
            3: next_residual_hz = combined_hz - 3 * DCO_GAIN_HZ_PER_LSB;
            4: next_residual_hz = combined_hz - 4 * DCO_GAIN_HZ_PER_LSB;
            5: next_residual_hz = combined_hz - 5 * DCO_GAIN_HZ_PER_LSB;
            6: next_residual_hz = combined_hz - 6 * DCO_GAIN_HZ_PER_LSB;
            default: next_residual_hz = combined_hz;
        endcase
        if (candidate_code < 0) begin
            next_dco_code = '0;
            next_residual_hz = 0;
            next_saturated = 1'b1;
        end else if (candidate_code > DCO_CODE_MAX) begin
            next_dco_code = DCO_CODE_MAX;
            next_residual_hz = 0;
            next_saturated = 1'b1;
        end else begin
            next_dco_code = candidate_code[DCO_CODE_BITS-1:0];
        end
    end

    always_ff @(posedge clk) begin
        if (reset) begin
            residual_hz <= 0;
            code_valid <= 1'b0;
            dco_code <= '0;
            saturated <= 1'b0;
        end else begin
            code_valid <= 1'b0;
            saturated <= 1'b0;
            if (frequency_valid) begin
                residual_hz <= next_residual_hz;
                code_valid <= 1'b1;
                dco_code <= next_dco_code;
                saturated <= next_saturated;
            end
        end
    end
endmodule

`default_nettype wire
