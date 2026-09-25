`default_nettype none

// Pad-facing control shell for FPGA bring-up and a small GF180 test chip.
module cgm_chip_core (
    input  logic       clk,
    input  logic       reset,
    input  logic       write_enable,
    input  logic       read_enable,
    input  logic [3:0] register_address,
    input  logic [7:0] write_data,
    output logic [7:0] read_data,
    output logic       packet_out,
    output logic       packet_valid,
    output logic       frequency_valid,
    output logic signed [18:0] frequency_offset_hz,
    output logic       busy,
    output logic       interrupt,
    output logic       bist_pass
);
    logic [5:0] channel;
    logic [47:0] advertiser_address;
    logic [15:0] sample_sequence;
    logic [15:0] glucose_mg_dl;
    logic [15:0] trend_q8_8;
    logic [7:0] status;
    logic [7:0] battery_percent;
    logic start_pulse;

    logic gfsk_done;
    logic rx_done;
    logic rx_crc_ok;
    logic rx_format_ok;
    logic [47:0] rx_advertiser_address;
    logic [15:0] rx_sample_sequence;
    logic [15:0] rx_glucose_mg_dl;
    logic [15:0] rx_trend_q8_8;
    logic [7:0] rx_status;
    logic [7:0] rx_battery_percent;
    logic bist_result;

    cgm_gfsk_tx transmitter (
        .clk(clk),
        .reset(reset),
        .start(start_pulse),
        .channel(channel),
        .advertiser_address(advertiser_address),
        .sample_sequence(sample_sequence),
        .glucose_mg_dl(glucose_mg_dl),
        .trend_q8_8(trend_q8_8),
        .status(status),
        .battery_percent(battery_percent),
        .busy(busy),
        .symbol_valid(packet_valid),
        .symbol_bit(packet_out),
        .symbol_last(),
        .frequency_valid(frequency_valid),
        .frequency_offset_hz(frequency_offset_hz),
        .done(gfsk_done)
    );

    cgm_packet_rx receiver (
        .clk(clk),
        .reset(reset),
        .packet_start(start_pulse),
        .channel(channel),
        .rx_valid(packet_valid),
        .rx_bit(packet_out),
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

    // Reads are sampled and returned on the following clock edge. Keeping the
    // pad-facing bus synchronous avoids a long input-pad-to-output-pad path.
    always_ff @(posedge clk) begin
        if (reset) begin
            read_data <= 8'h00;
        end else if (read_enable) begin
            case (register_address)
                4'h0: read_data <= {5'b00000, bist_pass, interrupt, busy};
                4'h1: read_data <= {2'b00, channel};
                4'h2: read_data <= advertiser_address[7:0];
                4'h3: read_data <= advertiser_address[15:8];
                4'h4: read_data <= advertiser_address[23:16];
                4'h5: read_data <= advertiser_address[31:24];
                4'h6: read_data <= advertiser_address[39:32];
                4'h7: read_data <= advertiser_address[47:40];
                4'h8: read_data <= sample_sequence[7:0];
                4'h9: read_data <= sample_sequence[15:8];
                4'hA: read_data <= glucose_mg_dl[7:0];
                4'hB: read_data <= glucose_mg_dl[15:8];
                4'hC: read_data <= trend_q8_8[7:0];
                4'hD: read_data <= trend_q8_8[15:8];
                4'hE: read_data <= status;
                4'hF: read_data <= battery_percent;
            endcase
        end else begin
            read_data <= 8'h00;
        end
    end

    always_ff @(posedge clk) begin
        if (reset) begin
            channel <= 6'd37;
            advertiser_address <= 48'hC0DEC0FFEE01;
            sample_sequence <= 16'd0;
            glucose_mg_dl <= 16'd100;
            trend_q8_8 <= 16'd0;
            status <= 8'd0;
            battery_percent <= 8'd100;
            start_pulse <= 1'b0;
            interrupt <= 1'b0;
            bist_pass <= 1'b0;
            bist_result <= 1'b0;
        end else begin
            start_pulse <= 1'b0;

            if (write_enable) begin
                case (register_address)
                    4'h0: begin
                        if (write_data[0] && !busy) begin
                            start_pulse <= 1'b1;
                            interrupt <= 1'b0;
                            bist_pass <= 1'b0;
                            bist_result <= 1'b0;
                        end
                        if (write_data[1]) begin
                            interrupt <= 1'b0;
                        end
                    end
                    4'h1: if (write_data[5:0] <= 6'd39) channel <= write_data[5:0];
                    4'h2: advertiser_address[7:0] <= write_data;
                    4'h3: advertiser_address[15:8] <= write_data;
                    4'h4: advertiser_address[23:16] <= write_data;
                    4'h5: advertiser_address[31:24] <= write_data;
                    4'h6: advertiser_address[39:32] <= write_data;
                    4'h7: advertiser_address[47:40] <= write_data;
                    4'h8: sample_sequence[7:0] <= write_data;
                    4'h9: sample_sequence[15:8] <= write_data;
                    4'hA: glucose_mg_dl[7:0] <= write_data;
                    4'hB: glucose_mg_dl[15:8] <= write_data;
                    4'hC: trend_q8_8[7:0] <= write_data;
                    4'hD: trend_q8_8[15:8] <= write_data;
                    4'hE: status <= write_data;
                    4'hF: battery_percent <= write_data;
                endcase
            end

            if (rx_done) begin
                bist_result <= rx_crc_ok
                            && rx_format_ok
                            && (rx_advertiser_address == advertiser_address)
                            && (rx_sample_sequence == sample_sequence)
                            && (rx_glucose_mg_dl == glucose_mg_dl)
                            && (rx_trend_q8_8 == trend_q8_8)
                            && (rx_status == status)
                            && (rx_battery_percent == battery_percent);
            end

            if (gfsk_done) begin
                interrupt <= 1'b1;
                bist_pass <= bist_result;
            end
        end
    end
endmodule

`default_nettype wire
