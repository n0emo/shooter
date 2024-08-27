from queue import Queue
import threading
import signal
import time

from ..shared.game import Game, Player
from ..shared.settings import SERVER_ADDRESS
from ..shared.net import Address, HelloStruct, MessageSocket, PlayerConnectStruct, PlayerDisconnectStruct, PlayerUpdateStruct


class Clock:
    previous: float
    delta: float

    def __init__(self) -> None:
        self.previous = time.time()

    def tick(self, tps: float) -> None:
        current = time.time()
        whole_time = 1 / tps
        self.delta = current - self.previous

        if self.delta < whole_time:
            time.sleep(whole_time - self.delta)
        self.previous = current



def main():
    sock = MessageSocket()
    sock.bind(SERVER_ADDRESS)

    queue = Queue()
    stop_event = threading.Event()
    recieve_thread = sock.create_recieve_thread(queue, stop_event)
    recieve_thread.start()

    clock = Clock()

    player_updates: dict[str, float] = {}

    def handle_sigint(signum, _):
        assert signum == signal.SIGINT

        print("\nStopping server")

        stop_event.set()
        sock.close()
        exit(0)


    signal.signal(signal.SIGINT, handle_sigint)

    handler = None
    game = Game(handler)

    addresses: dict[str, Address] = {}

    def disconnect_player(name: str) -> None:
        if name in addresses:
            game.players.pop(name)
            addresses.pop(name)
            player_updates.pop(name)
            for n in game.players.keys():
                message = PlayerDisconnectStruct(name.encode())
                sock.send(message, addresses[n])

    while True:
        clock.tick(60)
        while queue.qsize() > 0:
            message, address = queue.get_nowait()
            if isinstance(message, PlayerConnectStruct):
                player = Player(message.name_decoded)
                game.append_player(player)
                sock.send(HelloStruct(len(game.players)), address)
                for name, _ in addresses.items():
                    sock.send(PlayerConnectStruct(name.encode()), address)

                for a in addresses.values():
                    sock.send(message, a)
                addresses[player.name] = address


            elif isinstance(message, PlayerUpdateStruct):
                name = message.name_decoded
                if name in game.players:
                    player = game.players[message.name_decoded]
                    player.velocity.x = message.vel_x
                    player.velocity.y = message.vel_y
                    player_updates[name] = time.time()

            elif isinstance(message, PlayerDisconnectStruct):
                disconnect_player(message.name_decoded)


        game.update(clock.delta)

        for current_player in game.players.values():
            address = addresses[current_player.name]
            for player in game.players.values():
                msg = PlayerUpdateStruct(
                    player.name.encode(),
                    player.position.x,
                    player.position.y,
                    player.velocity.x,
                    player.velocity.y,
                )

                sock.send(msg, address)

        for player, updated in list(player_updates.items()):
            if time.time() - updated > 5:
                disconnect_player(player)

