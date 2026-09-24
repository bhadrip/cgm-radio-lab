import random

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer

from model.dco import dco_codes
from model.gfsk import frequency_words


async def reset_dut(dut):
    dut.reset.value = 1
    dut.frequency_valid.value = 0
    dut.frequency_offset_hz.value = 0
    dut.base_code.value = 2048
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    dut.reset.value = 0


@cocotb.test()
async def dco_codes_match_error_feedback_model(dut):
    cocotb.start_soon(Clock(dut.clk, 62.5, unit="ns").start())
    await reset_dut(dut)

    rng = random.Random(0xDC0)
    bits = [rng.randrange(2) for _ in range(80)]
    offsets = frequency_words(bits)
    expected_codes, expected_saturation = dco_codes(offsets, 2048)
    observed_codes = []
    observed_saturation = []

    for offset_hz in offsets:
        dut.frequency_offset_hz.value = offset_hz
        dut.frequency_valid.value = 1
        await RisingEdge(dut.clk)
        await Timer(1, unit="ns")
        assert int(dut.code_valid.value) == 1
        observed_codes.append(int(dut.dco_code.value))
        observed_saturation.append(bool(dut.saturated.value))

    dut.frequency_valid.value = 0
    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")
    assert int(dut.code_valid.value) == 0
    assert observed_codes == expected_codes
    assert observed_saturation == expected_saturation
