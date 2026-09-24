import random

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer

from model.gfsk import SAMPLES_PER_SYMBOL, frequency_words


def signed_word(value, width):
    raw = int(value)
    return raw - (1 << width) if raw & (1 << (width - 1)) else raw


async def reset_dut(dut):
    dut.reset.value = 1
    dut.bit_valid.value = 0
    dut.bit_in.value = 0
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    dut.reset.value = 0


async def send_symbol(dut, bit):
    while not int(dut.bit_ready.value):
        await RisingEdge(dut.clk)
    dut.bit_in.value = bit
    dut.bit_valid.value = 1
    await RisingEdge(dut.clk)
    dut.bit_valid.value = 0

    samples = []
    for index in range(SAMPLES_PER_SYMBOL):
        if index:
            await RisingEdge(dut.clk)
        await Timer(1, unit="ns")
        assert int(dut.sample_valid.value) == 1
        assert int(dut.sample_first.value) == int(index == 0)
        assert int(dut.sample_last.value) == int(index == SAMPLES_PER_SYMBOL - 1)
        samples.append(signed_word(dut.frequency_offset_hz.value, 19))
    return samples


@cocotb.test()
async def integer_frequency_words_match_reference_model(dut):
    cocotb.start_soon(Clock(dut.clk, 62.5, unit="ns").start())
    await reset_dut(dut)

    rng = random.Random(0xB1E1)
    bits = [rng.randrange(2) for _ in range(64)]
    observed = []
    for bit in bits:
        observed.extend(await send_symbol(dut, bit))

    assert observed == frequency_words(bits)
    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")
    assert int(dut.sample_valid.value) == 0


@cocotb.test()
async def back_to_back_symbols_have_no_sample_gap(dut):
    cocotb.start_soon(Clock(dut.clk, 62.5, unit="ns").start())
    await reset_dut(dut)

    bits = [int(value) for value in "1011001011100101"]
    expected = frequency_words(bits)
    source_index = 0
    observed = []
    started = False

    while len(observed) < len(expected):
        if int(dut.bit_ready.value) and source_index < len(bits):
            dut.bit_in.value = bits[source_index]
            dut.bit_valid.value = 1
            source_index += 1
        else:
            dut.bit_valid.value = 0

        await RisingEdge(dut.clk)
        await Timer(1, unit="ns")
        if int(dut.sample_valid.value):
            started = True
            sample_index = len(observed) % SAMPLES_PER_SYMBOL
            assert int(dut.sample_first.value) == int(sample_index == 0)
            assert int(dut.sample_last.value) == int(
                sample_index == SAMPLES_PER_SYMBOL - 1
            )
            observed.append(signed_word(dut.frequency_offset_hz.value, 19))
        elif started:
            raise AssertionError("sample_valid dropped between adjacent symbols")

    dut.bit_valid.value = 0
    assert observed == expected
