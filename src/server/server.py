from queue import Queue
import threading
import signal
import time

from ..shared.game import Game, Player
from ..shared.settings import SERVER_ADDRESS
from ..shared.net import Address, HelloStruct, MessageSocket, PlayerConnectStruct, PlayerUpdateStruct


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

    while True:
        clock.tick(60)
        while queue.qsize() > 0:
            message, address = queue.get_nowait()
            if isinstance(message, PlayerConnectStruct):
                player = Player(message.name.decode())
                addresses[player.name] = address
                game.append_player(player)
                sock.send(HelloStruct(len(game.players)), address)
            elif isinstance(message, PlayerUpdateStruct):
                try:
                    player = game.players[message.name.decode()]
                    player.velocity.x = message.vel_x
                    player.velocity.y = message.vel_y
                except:
                    pass

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

