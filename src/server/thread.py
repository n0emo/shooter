from socket import socket
from threading import Thread
from _thread import interrupt_main
from typing import override

from ..shared.game import Game, Player
from ..shared import net

class RecieveThread(Thread):
    sock: socket

    def __init__(self, sock: socket) -> None:
        super().__init__()
        self.sock = sock

    @override
    def run(self) -> None:
        try:
            while True:
                message = net.recieve(self.sock)
        except KeyboardInterrupt:
            interrupt_main()
        except:
            # TODO
            pass


class SendThread(Thread):
    sock: socket
    is_stopped: bool

    def __init__(self, sock: socket) -> None:
        super().__init__()
        self.sock = sock
        self.is_stopped = False

    @override
    def run(self) -> None:
        while not self.is_stopped:
            try:
                self.sock.getpeername()
            except KeyboardInterrupt:
                interrupt_main()
            except:
                pass

    def stop(self):
        self.is_stopped = True


class ClientThread(Thread):
    sock: socket
    address: net.Address 
    game: Game

    def __init__(
            self,
            sock: socket,
            address: net.Address,
            game: Game
    ) -> None:
        super().__init__()

        self.sock = sock
        self.address = address
        self.game = game

    @override
    def run(self) -> None:
        try:
            self.handle_player()
        except KeyboardInterrupt:
            interrupt_main()
        finally:
            self.stop()

    def handle_player(self) -> None:
        player_connect = net.recieve(self.sock)
        if not isinstance(player_connect, net.PlayerConnectMessage):
            return

        player = Player(player_connect.name.decode())
        print(f"{player.name} joined ({self.address})")

        if not self.game.append_player(player):
            reject = net.PlayerRejectMessage("Player with the same name already joined".encode())
            net.send(self.sock, reject)
            return

        player_count = len(self.game.players)
        hello = net.HelloMessage(player_count)
        net.send(self.sock, hello)

        send_thread, recieve_thread = SendThread(self.sock), RecieveThread(self.sock)

        send_thread.start()
        recieve_thread.start()

        recieve_thread.join()
        send_thread.stop()

        print(f"{player.name} disconnected ({self.address})")

    def stop(self):
        self.sock.close()

