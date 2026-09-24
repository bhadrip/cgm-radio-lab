"""Small, dependency-free BLE LE 1M bit-level reference model.

The model deliberately stops at hard bits. GFSK pulse shaping, RF impairments,
and clock recovery belong to later slices.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Sequence

ADV_ACCESS_ADDRESS = 0x8E89BED6
ADV_CRC_INIT = 0x555555
CRC_POLY = 0x00065B


def bytes_to_lsb_bits(data: bytes) -> list[int]:
    """Return BLE on-air bit order: least-significant bit of each octet first."""

    return [(octet >> bit) & 1 for octet in data for bit in range(8)]


def lsb_bits_to_bytes(bits: Sequence[int]) -> bytes:
    if len(bits) % 8:
        raise ValueError("bit count must be a multiple of eight")
    output = bytearray(len(bits) // 8)
    for index, bit in enumerate(bits):
        if bit not in (0, 1):
            raise ValueError("bits must contain only zero or one")
        output[index // 8] |= bit << (index % 8)
    return bytes(output)


def crc24_bits(bits: Iterable[int], init: int = ADV_CRC_INIT) -> int:
    """Calculate the BLE CRC LFSR state over an LSB-first bit stream."""

    state = init & 0xFFFFFF
    for bit in bits:
        feedback = ((state >> 23) & 1) ^ (int(bit) & 1)
        state = (state << 1) & 0xFFFFFF
        if feedback:
            state ^= CRC_POLY
    return state


def crc24(data: bytes, init: int = ADV_CRC_INIT) -> int:
    return crc24_bits(bytes_to_lsb_bits(data), init)


def crc_bits(value: int) -> list[int]:
    """Return the CRC state in BLE on-air order, highest LFSR stage first."""

    return [(value >> (23 - bit)) & 1 for bit in range(24)]


def whitening_seed(channel: int) -> int:
    if not 0 <= channel <= 39:
        raise ValueError("BLE channel must be in the range 0..39")
    return 0x40 | channel


def whiten_bits(bits: Iterable[int], channel: int) -> list[int]:
    """Apply the BLE x^7 + x^4 + 1 data whitening sequence."""

    state = whitening_seed(channel)
    output: list[int] = []
    for bit in bits:
        output.append((int(bit) & 1) ^ (state & 1))
        feedback = state & 1
        state >>= 1
        if feedback:
            state ^= 0x44
    return output


def dewhiten_bits(bits: Iterable[int], channel: int) -> list[int]:
    return whiten_bits(bits, channel)


def build_test_pdu(payload: bytes) -> bytes:
    """Build a minimal test PDU: two-byte header followed by the payload."""

    if len(payload) > 255:
        raise ValueError("test payload is limited to 255 bytes")
    return bytes((0x00, len(payload))) + payload


def add_crc(pdu: bytes, init: int = ADV_CRC_INIT) -> list[int]:
    body = bytes_to_lsb_bits(pdu)
    return body + crc_bits(crc24_bits(body, init))


def crc_ok(packet_bits: Sequence[int], init: int = ADV_CRC_INIT) -> bool:
    if len(packet_bits) < 24:
        return False
    body = packet_bits[:-24]
    received = packet_bits[-24:]
    return received == crc_bits(crc24_bits(body, init))


@dataclass(frozen=True)
class LoopResult:
    transmitted_bits: int
    flipped_bits: int
    crc_passed: bool
    payload_recovered: bool


def run_hard_bit_loop(
    payload: bytes,
    channel: int,
    error_mask: Sequence[int],
) -> LoopResult:
    packet = add_crc(build_test_pdu(payload))
    if len(error_mask) != len(packet):
        raise ValueError("error mask length must match encoded packet")
    channel_bits = whiten_bits(packet, channel)
    impaired = [bit ^ int(flip) for bit, flip in zip(channel_bits, error_mask)]
    recovered = dewhiten_bits(impaired, channel)
    recovered_pdu = lsb_bits_to_bytes(recovered[:-24])
    return LoopResult(
        transmitted_bits=len(packet),
        flipped_bits=sum(error_mask),
        crc_passed=crc_ok(recovered),
        payload_recovered=recovered_pdu == build_test_pdu(payload),
    )
