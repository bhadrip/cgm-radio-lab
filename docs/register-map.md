# Prototype register map

The interface is synchronous to `clk`. Assert `write_enable` or `read_enable`
for one cycle with a stable address and data value.

| Address | Read | Write |
|---:|---|---|
| `0x0` | bit 0 busy, bit 1 interrupt, bit 2 BIST pass | bit 0 start, bit 1 clear interrupt |
| `0x1` | BLE channel | BLE channel, 0–39 |
| `0x2`–`0x7` | advertiser address, little-endian | advertiser address, little-endian |
| `0x8`–`0x9` | sample sequence | sample sequence |
| `0xA`–`0xB` | glucose, mg/dL | glucose, mg/dL |
| `0xC`–`0xD` | signed trend, Q8.8 | signed trend, Q8.8 |
| `0xE` | status flags | status flags |
| `0xF` | battery percentage | battery percentage |

A start command serializes one packet and runs the internal TX-to-RX loopback.
`interrupt` rises when the receiver completes. `bist_pass` requires matching
format, CRC, advertiser address, and all CGM fields.

