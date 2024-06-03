"""
We define the following 4 kinds of packets.

 Type 1 -- Initialization     Type 2 -- Agree
+ - - - - - - - - - - - - +   + - - - - - - +
+ Type (Enum) |     N     +   + Type (Enum) +
+ -  -  -  -  -  -  -  -  +   + -  -  -  -  +
+  2 bytes    |  4 bytes  +   +   2 bytes   +
+ - - - - - - - - - - - - +   + - - - - - - +

          Type 3 -- reverseRequest
+ - - - - - - - - - - - - + - - - - - - - - +
+ Type (Enum) |  Length   |       Data      |
+ -  -  -  -  -  -  -  -  -  -  -  -  -  -  +
+  2 bytes    |  4 bytes  |     No Limit    |
+ - - - - - - - - - - - - + - - - - - - - - +

          Type 4 -- reverseAnswer
+ - - - - - - - - - - - - + - - - - - - - - +
+ Type (Enum) |  Length   |   reversedData  |
+ -  -  -  -  -  -  -  -  -  -  -  -  -  -  +
+  2 bytes    |  4 bytes  |     No Limit    |
+ - - - - - - - - - - - - + - - - - - - - - +
"""

import argparse
from enum import Enum
from config import Settings


class PacketType(Enum):
    initialize = 1
    agreement = 2
    reverse_req = 3
    reverse_ans = 4


class CustomPackets:
    @staticmethod
    def _to_binary(val: int, length: int) -> str:
        bin_val = bin(val)[2:]
        if len(bin_val) < length * 8:
            return "0" * (length * 8 - len(bin_val)) + bin_val
        return bin_val

    def __init__(self, packet_type: PacketType):
        self.__type = packet_type
        self.packet_type = CustomPackets._to_binary(
            packet_type.value, Settings.TYPE_NUM
        )

    def generate_packet_bytes(self, *, N=None, length=None, data=None):
        if self.__type == PacketType.initialize:
            msg_to_send = (
                f"{self.packet_type}{CustomPackets._to_binary(N, Settings.LEN_OR_N)}"
            )
        if self.__type == PacketType.agreement:
            msg_to_send = self.packet_type
        if (
            self.__type == PacketType.reverse_req
            or self.__type == PacketType.reverse_ans
        ):
            msg_to_send = f"{self.packet_type}{CustomPackets._to_binary(length, Settings.LEN_OR_N)}{data}"

        return msg_to_send.encode(Settings.FORMAT)

    def decode_from_bytes(self, data: bytes):
        decoded_data = data.decode(Settings.FORMAT)
        type_num = int(decoded_data[: Settings.TYPE_NUM * 8], 2)

        if self.__type == PacketType.agreement:
            return (type_num,)
        if self.__type == PacketType.initialize:
            N = int(
                decoded_data[
                    Settings.TYPE_NUM * 8 : (Settings.TYPE_NUM + Settings.LEN_OR_N) * 8
                ],
                2,
            )
            return (type_num, N)

        if (
            self.__type == PacketType.reverse_req
            or self.__type == PacketType.reverse_ans
        ):
            length = int(
                decoded_data[
                    Settings.TYPE_NUM * 8 : (Settings.TYPE_NUM + Settings.LEN_OR_N) * 8
                ],
                2,
            )
            raw_data = decoded_data[(Settings.TYPE_NUM + Settings.LEN_OR_N) * 8 :]

            return (type_num, length, raw_data)


class CustomArgParser:
    @staticmethod
    def int_within_range(val: str) -> int:
        try:
            int_val = int(val)
        except ValueError:
            raise argparse.ArgumentTypeError(f"{val} is not a valid integer.")

        if int_val <= 0:
            raise argparse.ArgumentTypeError(f"{int_val} should be at least 1.")

        return int_val
