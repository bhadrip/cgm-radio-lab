import random

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer

from model.ble import ADV_CRC_INIT, add_crc, build_test_pdu, crc24_bits, whiten_bits


async def reset_dut(dut):
    dut.reset.value = 1
    dut.packet_start.value = 0
    dut.data_valid.value = 0
    dut.crc_valid.value = 0
    dut.data_in.value = 0
    dut.inject_error.value = 0
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    dut.reset.value = 0


async def run_packet(dut, payload, channel, error_locations=frozenset()):
    pdu = build_test_pdu(payload)
    packet = add_crc(pdu)
    body_length = len(packet) - 24
    expected_tx = whiten_bits(packet, channel)

    dut.channel.value = channel
    dut.crc_init.value = ADV_CRC_INIT
    dut.packet_start.value = 1
    await RisingEdge(dut.clk)
    dut.packet_start.value = 0

    received = []
    for index, bit in enumerate(packet):
        dut.data_in.value = bit
        dut.inject_error.value = int(index in error_locations)
        dut.data_valid.value = 1
        dut.crc_valid.value = int(index < body_length)
        await Timer(1, unit="ns")
        assert int(dut.tx_bit.value) == expected_tx[index]
        received.append(int(dut.rx_bit.value))
        await RisingEdge(dut.clk)

    dut.data_valid.value = 0
    dut.crc_valid.value = 0
    dut.inject_error.value = 0
    await Timer(1, unit="ns")
    return packet, received, int(dut.tx_crc_state.value), int(dut.rx_crc_state.value)


@cocotb.test()
async def clean_packets_match_python_and_crc(dut):
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())
    await reset_dut(dut)
    rng = random.Random(0xB1E)

    for channel in (0, 19, 37, 38, 39):
        payload = rng.randbytes(8)
        packet, received, tx_crc, rx_crc = await run_packet(dut, payload, channel)
        expected_crc = crc24_bits(packet[:-24])
        assert received == packet
        assert tx_crc == expected_crc
        assert rx_crc == expected_crc


@cocotb.test()
async def channel_error_is_visible_to_receiver_crc(dut):
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())
    await reset_dut(dut)
    packet, received, tx_crc, rx_crc = await run_packet(
        dut, b"CGM00001", channel=37, error_locations={23}
    )
    assert received != packet
    assert tx_crc != rx_crc

