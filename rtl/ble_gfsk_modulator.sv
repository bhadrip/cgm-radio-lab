`default_nettype none

// BLE LE 1M Gaussian pulse shaper for a direct-modulation frequency-control
// path. One signed integer-Hz sample is emitted per 16 MHz clock; sixteen
// samples form one 1 Msym/s symbol. The four-symbol Gaussian FIR is collapsed
// into five symbol-history weights for each of the sixteen sample phases.
module ble_gfsk_modulator (
    input  logic               clk,
    input  logic               reset,
    input  logic               bit_valid,
    input  logic               bit_in,
    output logic               bit_ready,
    output logic               sample_valid,
    output logic               sample_first,
    output logic               sample_last,
    output logic signed [18:0] frequency_offset_hz
);
    localparam logic [3:0] LAST_PHASE = 4'd15;

    logic [4:0] symbol_history;
    logic [3:0] sample_phase;
    logic       active;
    logic [4:0] next_history;

    assign bit_ready = !active || (sample_phase == LAST_PHASE);
    assign next_history = {symbol_history[3:0], bit_in};

    function automatic signed [18:0] shaped_frequency;
        input logic [4:0] history;
        input logic [3:0] phase;
        integer w0;
        integer w1;
        integer w2;
        integer w3;
        integer w4;
        integer value;
        begin
            case (phase)
                4'd0:  begin w0=0;  w1=31;     w2=136730; w3=113227; w4=12; end
                4'd1:  begin w0=0;  w1=76;     w2=159562; w3=90358;  w4=4;  end
                4'd2:  begin w0=0;  w1=177;    w2=180505; w3=69316;  w4=2;  end
                4'd3:  begin w0=0;  w1=391;    w2=198604; w3=51004;  w4=1;  end
                4'd4:  begin w0=0;  w1=820;    w2=213250; w3=35930;  w4=0;  end
                4'd5:  begin w0=0;  w1=1633;   w2=224173; w3=24194;  w4=0;  end
                4'd6:  begin w0=0;  w1=3091;   w2=231358; w3=15551;  w4=0;  end
                4'd7:  begin w0=0;  w1=5563;   w2=234907; w3=9530;   w4=0;  end
                4'd8:  begin w0=0;  w1=9530;   w2=234907; w3=5563;   w4=0;  end
                4'd9:  begin w0=0;  w1=15551;  w2=231358; w3=3091;   w4=0;  end
                4'd10: begin w0=0;  w1=24194;  w2=224173; w3=1633;   w4=0;  end
                4'd11: begin w0=0;  w1=35930;  w2=213250; w3=820;    w4=0;  end
                4'd12: begin w0=1;  w1=51004;  w2=198604; w3=391;    w4=0;  end
                4'd13: begin w0=2;  w1=69316;  w2=180505; w3=177;    w4=0;  end
                4'd14: begin w0=4;  w1=90358;  w2=159562; w3=76;     w4=0;  end
                default: begin w0=12; w1=113227; w2=136730; w3=31; w4=0; end
            endcase
            value = (history[0] ? w0 : -w0)
                  + (history[1] ? w1 : -w1)
                  + (history[2] ? w2 : -w2)
                  + (history[3] ? w3 : -w3)
                  + (history[4] ? w4 : -w4);
            shaped_frequency = value;
        end
    endfunction

    always_ff @(posedge clk) begin
        if (reset) begin
            symbol_history <= 5'b00000;
            sample_phase <= 4'd0;
            active <= 1'b0;
            sample_valid <= 1'b0;
            sample_first <= 1'b0;
            sample_last <= 1'b0;
            frequency_offset_hz <= '0;
        end else begin
            sample_valid <= 1'b0;
            sample_first <= 1'b0;
            sample_last <= 1'b0;

            if (!active) begin
                if (bit_valid) begin
                    symbol_history <= next_history;
                    frequency_offset_hz <= shaped_frequency(next_history, 4'd0);
                    sample_phase <= 4'd1;
                    sample_valid <= 1'b1;
                    sample_first <= 1'b1;
                    active <= 1'b1;
                end
            end else begin
                frequency_offset_hz <= shaped_frequency(symbol_history, sample_phase);
                sample_valid <= 1'b1;
                sample_first <= sample_phase == 4'd0;
                sample_last <= sample_phase == LAST_PHASE;
                if (sample_phase == LAST_PHASE) begin
                    if (bit_valid) begin
                        symbol_history <= next_history;
                        sample_phase <= 4'd0;
                    end else begin
                        active <= 1'b0;
                    end
                end else begin
                    sample_phase <= sample_phase + 1'b1;
                end
            end
        end
    end
endmodule

`default_nettype wire
