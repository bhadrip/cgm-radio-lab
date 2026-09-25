import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer

from model.ble import CgmMeasurement, build_cgm_air_packet_bits


ADDRESS = 0xD1A2B3C4D5E6
MEASUREMENT = CgmMeasurement(0xA725, 142, -192, 0x09, 76)
CHANNEL = 38


async def reset_dut(dut):
    dut.reset.value = 1
    dut.write_enable.value = 0
    dut.read_enable.value = 0
    dut.register_address.value = 0
    dut.write_data.value = 0
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    dut.reset.value = 0


async def write_register(dut, address, value):
    dut.register_address.value = address
    dut.write_data.value = value
    dut.write_enable.value = 1
    await RisingEdge(dut.clk)
    dut.write_enable.value = 0


async def read_register(dut, address):
    dut.register_address.value = address
    dut.read_enable.value = 1
    await Timer(1, unit="ns")
    value = int(dut.read_data.value)
    dut.read_enable.value = 0
    return value


@cocotb.test()
async def register_programmed_packet_and_bist(dut):
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())
    await reset_dut(dut)

    await write_register(dut, 0x1, CHANNEL)
    for offset, value in enumerate(ADDRESS.to_bytes(6, "little")):
        await write_register(dut, 0x2 + offset, value)
    fields = b"".join(
        (
            MEASUREMENT.sequence.to_bytes(2, "little"),
            MEASUREMENT.glucose_mg_dl.to_bytes(2, "little"),
            MEASUREMENT.trend_q8_8.to_bytes(2, "little", signed=True),
            bytes((MEASUREMENT.status, MEASUREMENT.battery_percent)),
        )
    )
    for offset, value in enumerate(fields):
        await write_register(dut, 0x8 + offset, value)

    assert await read_register(dut, 0x1) == CHANNEL
    assert await read_register(dut, 0xA) == (MEASUREMENT.glucose_mg_dl & 0xFF)
    assert await read_register(dut, 0xB) == (MEASUREMENT.glucose_mg_dl >> 8)

    await write_register(dut, 0x0, 0x01)
    expected = build_cgm_air_packet_bits(MEASUREMENT, ADDRESS, CHANNEL)
    observed = []
    while len(observed) < len(expected):
        await Timer(1, unit="ns")
        if int(dut.packet_valid.value):
            observed.append(int(dut.packet_out.value))
        await RisingEdge(dut.clk)

    for _ in range(4):
        await RisingEdge(dut.clk)
        if int(dut.interrupt.value):
            break

    assert observed == expected
    assert int(dut.interrupt.value) == 1
    assert int(dut.bist_pass.value) == 1
    assert await read_register(dut, 0x0) == 0b00000110

    await write_register(dut, 0x0, 0x02)
    await RisingEdge(dut.clk)
    assert int(dut.interrupt.value) == 0

