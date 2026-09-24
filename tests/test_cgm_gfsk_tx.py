import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer

from model.ble import CgmMeasurement, build_cgm_air_packet_bits
from model.gfsk import SAMPLES_PER_SYMBOL, frequency_words


ADDRESS = 0xD1A2B3C4D5E6
MEASUREMENT = CgmMeasurement(0xA725, 142, -192, 0x09, 76)
CHANNEL = 38


def signed_word(value, width):
    raw = int(value)
    return raw - (1 << width) if raw & (1 << (width - 1)) else raw


async def reset_dut(dut):
    dut.reset.value = 1
    dut.start.value = 0
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    dut.reset.value = 0


@cocotb.test()
async def cgm_packet_drives_gapless_one_mbps_gfsk(dut):
    cocotb.start_soon(Clock(dut.clk, 62.5, unit="ns").start())
    await reset_dut(dut)

    dut.channel.value = CHANNEL
    dut.advertiser_address.value = ADDRESS
    dut.sample_sequence.value = MEASUREMENT.sequence
    dut.glucose_mg_dl.value = MEASUREMENT.glucose_mg_dl
    dut.trend_q8_8.value = MEASUREMENT.trend_q8_8 & 0xFFFF
    dut.status.value = MEASUREMENT.status
    dut.battery_percent.value = MEASUREMENT.battery_percent

    bits = build_cgm_air_packet_bits(MEASUREMENT, ADDRESS, CHANNEL)
    expected = frequency_words(bits)

    dut.start.value = 1
    await RisingEdge(dut.clk)
    dut.start.value = 0

    observed = []
    observed_bits = []
    started = False
    cycles = 0
    while not int(dut.done.value):
        await RisingEdge(dut.clk)
        await Timer(1, unit="ns")
        cycles += 1
        if int(dut.frequency_valid.value):
            started = True
            observed.append(signed_word(dut.frequency_offset_hz.value, 19))
        elif started and len(observed) < len(expected):
            raise AssertionError("frequency_valid dropped inside the packet")
        assert cycles <= len(expected) + 4
        if int(dut.symbol_valid.value):
            observed_bits.append(int(dut.symbol_bit.value))

    assert len(bits) == 224
    assert len(observed) == len(bits) * SAMPLES_PER_SYMBOL
    assert observed == expected
    assert observed_bits == bits
    assert int(dut.symbol_last.value) == 1
    assert int(dut.busy.value) == 0
