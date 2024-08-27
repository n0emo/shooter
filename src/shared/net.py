from dataclasses import astuple, dataclass
from io import BytesIO
import socket
from enum import IntEnum
from threading import Event, Thread
from typing import ClassVar, NamedTuple
from struct import Struct
from queue import Queue


Address = NamedTuple("Address", [("host", str), ("port", int)])


def decode(s: bytes) -> str:
    return s.decode().rstrip('\x00')


@dataclass
class HelloStruct:
    struct: ClassVar[Struct] = Struct("i")

    player_count: int


@dataclass
class PlayerConnectStruct:
    struct: ClassVar[Struct] = Struct("160s")

    name: bytes

    @property
    def name_decoded(self) -> str:
        return decode(self.name)


@dataclass
class PlayerRejectStruct:
    struct: ClassVar[Struct] = Struct("400s")

    message: bytes

    @property
    def message_decoded(self) -> str:
        return decode(self.message)


@dataclass
class PlayerUpdateStruct:
    struct: ClassVar[Struct] = Struct("160sffff")

    name: bytes
    pos_x: float
    pos_y: float
    vel_x: float
    vel_y: float

    @property
    def name_decoded(self) -> str:
        return decode(self.name)


@dataclass
class PlayerDisconnectStruct:
    struct: ClassVar[Struct] = Struct("160s")

    name: bytes

    @property
    def name_decoded(self) -> str:
        return decode(self.name)


StructBase = (
      HelloStruct
    | PlayerConnectStruct
    | PlayerRejectStruct
    | PlayerUpdateStruct
    | PlayerDisconnectStruct
)


class MessageKind(IntEnum):
    Hello = 0
    PlayerConnect = 1
    PlayerReject = 2
    PlayerUpdate = 3
    PlayerDisconnect = 4


KIND_TO_TYPE: dict[MessageKind, type[StructBase]] = {
    MessageKind.Hello:            HelloStruct,
    MessageKind.PlayerConnect:    PlayerConnectStruct,
    MessageKind.PlayerReject:     PlayerRejectStruct,
    MessageKind.PlayerUpdate:     PlayerUpdateStruct,
    MessageKind.PlayerDisconnect: PlayerDisconnectStruct,
}


TYPE_TO_KIND = { v: k for k, v in KIND_TO_TYPE.items() }


@dataclass
class Header:
    struct: ClassVar[Struct] = Struct("ii")

    length: int
    kind: MessageKind


class MessageSocket:
    sock: socket.socket

    def __init__(self) -> None:
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setblocking(False)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    def bind(self, address: Address) -> None:
        self.sock.bind(address)

    def close(self):
        self.sock.close()

    def create_recieve_thread(
            self,
            queue: Queue[tuple[StructBase, Address]],
            stop_event: Event
    ) -> Thread:
        def target():
            while not stop_event.is_set():
                try:
                    struct, address = self.recieve()
                    if struct is not None:
                        queue.put((struct, address))
                except BlockingIOError:
                    pass
                except OSError as e:
                    if not stop_event.is_set():
                        raise e

        return Thread(target=target)

    def recieve(self) -> tuple[StructBase | None, Address]:
        io = BytesIO()
        io.seek(512)
        io.write(b'\x00')
        io.seek(0)
        io.getbuffer

        bytes_recieved, address = self.sock.recvfrom_into(io.getbuffer(), 512);

        if bytes_recieved < Header.struct.size:
            return None, address

        header = Header(*Header.struct.unpack(io.read(Header.struct.size)))

        body = io.read(header.length)
        if len(body) != header.length:
            return None, address

        if header.kind not in KIND_TO_TYPE:
            return None, address

        struct_type = KIND_TO_TYPE[header.kind]

        return struct_type(*struct_type.struct.unpack(body)), address


    def send(self, message: StructBase, address: Address) -> None:
        io = BytesIO()

        kind = TYPE_TO_KIND[type(message)]
        body = message.struct.pack(*astuple(message))
        header = Header.struct.pack(*astuple(Header(len(body), kind)))
        io.write(header)
        io.write(body)

        self.sock.sendto(io.getbuffer(), address)

