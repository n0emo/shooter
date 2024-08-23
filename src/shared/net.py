from dataclasses import dataclass
import dataclasses
import socket
from enum import IntEnum
from typing import ClassVar, NamedTuple
from struct import Struct


Address = NamedTuple('Address', [("host", str), ("port", int)])


class MessageKind(IntEnum):
    Hello = 0
    PlayerConnect = 1
    PlayerReject = 2


@dataclass
class Header:
    struct: ClassVar[Struct] = Struct("<ii")

    length: int
    kind: MessageKind


    def pack(self) -> bytes:
        return Header.struct.pack(*dataclasses.astuple(self))

    @staticmethod
    def unpack(hdr: bytes) -> "Header":
        return Header(*Header.struct.unpack(hdr))


@dataclass
class Message:
    struct: ClassVar[Struct]

    @staticmethod
    def create(header: Header, body: bytes) -> "Message":
        match header.kind:
            case MessageKind.Hello:
                return HelloMessage.unpack(body)
            case MessageKind.PlayerConnect:
                return PlayerConnectMessage.unpack(body)
            case MessageKind.PlayerReject:
                return PlayerRejectMessage.unpack(body)

        raise ValueError()


    def pack(self) -> bytes:
        return self.struct.pack(*dataclasses.astuple(self))


    @classmethod
    def unpack(cls, body: bytes) -> "Message":
        obj = cls.__new__(cls)
        cls.__init__(obj, *cls.struct.unpack(body))
        return obj


@dataclass
class HelloMessage(Message):
    struct: ClassVar[Struct] = Struct("<i")

    player_count: int


@dataclass
class PlayerConnectMessage(Message):
    struct: ClassVar[Struct] = Struct('<120s')

    name: bytes


@dataclass
class PlayerRejectMessage(Message):
    struct: ClassVar[Struct] = Struct('<1024s')

    message: bytes


def recieve(sock: socket.socket) -> Message:
    header = Header.unpack(sock.recv(Header.struct.size))
    body = sock.recv(header.length)
    return Message.create(header, body)


def send(sock: socket.socket, message: Message) -> None:
    if isinstance(message, HelloMessage):
        kind = MessageKind.Hello
    elif isinstance(message, PlayerConnectMessage):
        kind = MessageKind.PlayerConnect
    elif isinstance(message, PlayerRejectMessage):
        kind = MessageKind.PlayerReject
    else:
        raise ValueError()

    body = message.pack()
    header = Header(len(body), kind)
    sock.sendall(header.pack())
    sock.sendall(body)

