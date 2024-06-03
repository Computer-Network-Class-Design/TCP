import os
import socket
import random
import argparse
import shortuuid

from typing import List

from config import Settings
from util import CustomPackets, PacketType, CustomArgParser


class TCPClient:
    @staticmethod
    def __calculate_bytes(
        min_bytes: int, max_bytes: int, total_bytes: int
    ) -> List[int]:
        res = []

        while total_bytes > 0:
            each_byte = random.randint(
                min(min_bytes, total_bytes), min(max_bytes, total_bytes)
            )
            res.append(each_byte)
            total_bytes -= each_byte

        return res

    def __init__(
        self,
        min_bytes: int = 1,
        max_bytes: int = float("inf"),
        server_ip: str = Settings.IP,
        server_port: int = Settings.PORT,
    ):
        self.server_addr = (server_ip, server_port)
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client.connect(self.server_addr)

        with open(Settings.FILE_NAME, "r") as file:
            self.original_file = file.read()

        total_bytes, self.remain_bits = divmod(len(self.original_file), 8)

        self.blocks_to_send = list(
            map(
                lambda x: x * 8,
                TCPClient.__calculate_bytes(min_bytes, max_bytes, total_bytes),
            )
        )
        for i in range(1, len(self.blocks_to_send)):
            self.blocks_to_send[i] += self.blocks_to_send[i - 1]

        self.re_file_name = f"files/{shortuuid.random(Settings.UUID_LEN)}_client.txt"
        self.reversed_file = open(self.re_file_name, "a")

    def _send_initialization(self):
        initialize = CustomPackets(PacketType.initialize)
        self.client.send(initialize.generate_packet_bytes(N=len(self.blocks_to_send)))

    def _confirm_agreement(self) -> bool:
        agreement = CustomPackets(PacketType.agreement)
        ack = self.client.recv(Settings.TYPE_NUM * 8)
        return agreement.decode_from_bytes(ack)[0] == PacketType.agreement.value

    def _send_raw_data(self):
        request_req = CustomPackets(PacketType.reverse_req)
        request_ans = CustomPackets(PacketType.reverse_ans)
        already_sent_bits = 0

        for i in range(len(self.blocks_to_send)):
            bits_to_send = self.blocks_to_send[i]
            msg_to_send = self.original_file[already_sent_bits:bits_to_send]
            msg_to_send = request_req.generate_packet_bytes(
                length=bits_to_send // 8, data=msg_to_send
            )

            self.client.send(msg_to_send)
            reversed_raw_data = self.client.recv(len(msg_to_send))
            reversed_data = request_ans.decode_from_bytes(reversed_raw_data)[-1]

            print(f"No.{i+1}:".ljust(7), reversed_data)

            self.reversed_file.write(reversed_data)
            self.reversed_file.flush()

            already_sent_bits = bits_to_send

        msg_to_send = self.original_file[-self.remain_bits : :]
        msg_to_send = request_ans.generate_packet_bytes(
            length=self.remain_bits // 8, data=msg_to_send
        )

        self.client.send(msg_to_send)
        reversed_raw_data = self.client.recv(len(msg_to_send))
        reversed_data = request_req.decode_from_bytes(reversed_raw_data)[-1]
        print(f"No.{i+1}:".ljust(7), reversed_data)

        self.reversed_file.write(reversed_data)
        self.reversed_file.flush()

    def run(self):
        print("Client starts")
        self._send_initialization()
        if not self._confirm_agreement():
            print("Server clearance is not granted.")
            return

        self._send_raw_data()
        print(f"Reversed file stored under {self.re_file_name}")


if __name__ == "__main__":
    os.makedirs("files/", exist_ok=True)

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-min",
        "--minBytes",
        type=CustomArgParser.int_within_range,
        default=1,
        help="The minimum bytes to split the file",
    )
    parser.add_argument(
        "-max",
        "--maxBytes",
        type=CustomArgParser.int_within_range,
        default=int(1e9),
        help="The maximum bytes to split the file",
    )
    parser.add_argument(
        "-sip",
        "--serverIP",
        type=str,
        default="127.0.0.1",
        help="The IP address of the server",
    )

    parser.add_argument(
        "-spt", "--serverPort", type=int, default=8000, help="The port of the server"
    )

    args = parser.parse_args()
    if args.maxBytes < args.minBytes:
        parser.error("--maxBytes must be greater than or equal to --minBytes")

    client = TCPClient(args.minBytes, args.maxBytes, args.serverIP, args.serverPort)
    client.run()
