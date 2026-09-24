import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer


async def reset_dut(dut):
    dut.reset.value = 1
    dut.code_valid.value = 0
    dut.modulation_code.value = 0
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    dut.reset.value = 0


@cocotb.test()
async def exhaustive_codes_are_registered_and_monotonic(dut):
    cocotb.start_soon(Clock(dut.clk, 62.5, unit="ns").start())
    await reset_dut(dut)

    for code in range(128):
        dut.modulation_code.value = code
        dut.code_valid.value = 1
        await RisingEdge(dut.clk)
        await Timer(1, unit="ns")
        thermometer_count = code >> 2
        expected_thermometer = (1 << thermometer_count) - 1
        assert int(dut.control_valid.value) == 1
        assert int(dut.thermometer_msb.value) == expected_thermometer
        assert int(dut.binary_lsb.value) == (code & 0b11)
        assert int(dut.thermometer_msb.value).bit_count() == thermometer_count

    held_thermometer = int(dut.thermometer_msb.value)
    held_binary = int(dut.binary_lsb.value)
    dut.code_valid.value = 0
    dut.modulation_code.value = 0
    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")
    assert int(dut.control_valid.value) == 0
    assert int(dut.thermometer_msb.value) == held_thermometer
    assert int(dut.binary_lsb.value) == held_binary

    dut.reset.value = 1
    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")
    assert int(dut.control_valid.value) == 0
    assert int(dut.thermometer_msb.value) == 0
    assert int(dut.binary_lsb.value) == 0
