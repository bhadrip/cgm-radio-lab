import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer

from model.ble import CgmMeasurement, build_cgm_air_packet_bits


ADDRESS = 0xC0DEC0FFEE01
MEASUREMENT = CgmMeasurement(
    sequence=0x1234,
    glucose_mg_dl=117,
    trend_q8_8=-384,
    status=0x05,
    battery_percent=83,
)


async def reset_dut(dut):
    dut.reset.value = 1
    dut.start.value = 0
    dut.inject_error.value = 0
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    dut.reset.value = 0


async def transmit(dut, channel, error_locations=frozenset()):
    expected = build_cgm_air_packet_bits(MEASUREMENT, ADDRESS, channel)
    dut.channel.value = channel
    dut.advertiser_address.value = ADDRESS
    dut.sample_sequence.value = MEASUREMENT.sequence
    dut.glucose_mg_dl.value = MEASUREMENT.glucose_mg_dl
    dut.trend_q8_8.value = MEASUREMENT.trend_q8_8 & 0xFFFF
    dut.status.value = MEASUREMENT.status
    dut.battery_percent.value = MEASUREMENT.battery_percent
    dut.start.value = 1
    await RisingEdge(dut.clk)
    dut.start.value = 0

    observed = []
    for index, expected_bit in enumerate(expected):
        dut.inject_error.value = int(index in error_locations)
        await Timer(1, unit="ns")
        assert int(dut.tx_valid.value) == 1
        assert int(dut.tx_bit.value) == expected_bit
        assert int(dut.tx_last.value) == int(index == len(expected) - 1)
        observed.append(int(dut.tx_bit.value))
        await RisingEdge(dut.clk)

    dut.inject_error.value = 0
    await Timer(1, unit="ns")
    assert int(dut.tx_busy.value) == 0
    assert int(dut.rx_done.value) == 1
    return observed


def assert_payload(dut):
    assert int(dut.rx_advertiser_address.value) == ADDRESS
    assert int(dut.rx_sample_sequence.value) == MEASUREMENT.sequence
    assert int(dut.rx_glucose_mg_dl.value) == MEASUREMENT.glucose_mg_dl
    assert int(dut.rx_trend_q8_8.value) == (MEASUREMENT.trend_q8_8 & 0xFFFF)
    assert int(dut.rx_status.value) == MEASUREMENT.status
    assert int(dut.rx_battery_percent.value) == MEASUREMENT.battery_percent


@cocotb.test()
async def clean_cgm_packet_matches_golden_model(dut):
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())
    await reset_dut(dut)
    observed = await transmit(dut, channel=37)
    assert observed == build_cgm_air_packet_bits(MEASUREMENT, ADDRESS, 37)
    assert int(dut.rx_crc_ok.value) == 1
    assert int(dut.rx_format_ok.value) == 1
    assert_payload(dut)


@cocotb.test()
async def payload_error_fails_crc(dut):
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())
    await reset_dut(dut)
    await transmit(dut, channel=38, error_locations={150})
    assert int(dut.rx_crc_ok.value) == 0
    assert int(dut.rx_format_ok.value) == 1


@cocotb.test()
async def preamble_error_fails_format_check(dut):
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())
    await reset_dut(dut)
    await transmit(dut, channel=39, error_locations={3})
    assert int(dut.rx_crc_ok.value) == 1
    assert int(dut.rx_format_ok.value) == 0

