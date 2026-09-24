import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer


NUM_BIDIR_PADS = 38


async def reset_dut(dut):
    dut.rst_n.value = 0
    dut.input_in.value = 0
    dut.bidir_in.value = 0
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    dut.rst_n.value = 1


async def write_register(dut, address, value):
    dut.bidir_in.value = (value << 4) | address
    dut.input_in.value = 0b0001
    await RisingEdge(dut.clk)
    dut.input_in.value = 0


async def read_register(dut, address):
    dut.bidir_in.value = address
    dut.input_in.value = 0b0010
    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")
    value = (int(dut.bidir_out.value) >> 17) & 0xFF
    dut.input_in.value = 0
    return value


@cocotb.test()
async def smallest_slot_pin_map_runs_packet_bist(dut):
    cocotb.start_soon(Clock(dut.clk, 40, unit="ns").start())
    await reset_dut(dut)

    input_mask = (1 << 12) - 1
    assert int(dut.bidir_oe.value) == ((1 << NUM_BIDIR_PADS) - 1) ^ input_mask
    assert int(dut.bidir_ie.value) == input_mask

    await write_register(dut, 0xA, 0x8E)
    await write_register(dut, 0xB, 0x00)
    assert await read_register(dut, 0xA) == 142

    await write_register(dut, 0x0, 0x01)
    packet_bits = []
    while len(packet_bits) < 224:
        await Timer(1, unit="ns")
        pins = int(dut.bidir_out.value)
        if (pins >> 13) & 1:
            packet_bits.append((pins >> 12) & 1)
        await RisingEdge(dut.clk)

    for _ in range(4):
        await RisingEdge(dut.clk)
        if (int(dut.bidir_out.value) >> 15) & 1:
            break

    pins = int(dut.bidir_out.value)
    assert len(packet_bits) == 224
    assert (pins >> 15) & 1
    assert (pins >> 16) & 1
    assert await read_register(dut, 0x0) == 0b00000110
