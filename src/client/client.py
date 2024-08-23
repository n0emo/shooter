from enum import IntEnum
import socket

import pyray as rl
from raylib import ffi

from ..shared import net
from ..shared import game as shared_game
from ..shared.settings import SERVER_ADDRESS


class GameState(IntEnum):
    Menu = 1
    Started = 2
    Disconnected = 3


game = shared_game.Game()
state = GameState.Menu
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

name_input = ffi.new("char[20]") # type: ignore
pointer = ffi.addressof(name_input) # type: ignore

def connect(player: shared_game.Player):
    print("Connecting")
    sock.connect(SERVER_ADDRESS)
    print("Connected")
    net.send(sock, net.PlayerConnectMessage(player.name.encode()))
    print("Sent message")
    hello = net.recieve(sock)
    print("Recieved message")
    if not isinstance(hello, net.HelloMessage):
        raise Exception()
    print(f"Connected to server with {hello.player_count} players")


def main():
    global state
    global game
    global sock

    rl.init_window(800, 600, "Shooter")

    while not rl.window_should_close():
        match state:
            case GameState.Menu:
                rl.draw_text("Enter your name", 100, 50, 48, rl.WHITE)
                rl.gui_text_box(
                    rl.Rectangle(100, 100, 400, 50),
                    pointer, # type: ignore
                    20,
                    True
                )
                value = rl.gui_button(
                    rl.Rectangle(450, 150, 50, 25),
                    "Enter"
                )
                if value:
                    print(value)
                    name = ffi.string(name_input)
                    assert isinstance(name, bytes)
                    name = name.decode("ascii")
                    player = shared_game.Player(name)
                    try:
                        connect(player)
                        state = GameState.Started
                    except Exception as e:
                        print(e)
            case GameState.Started:
                pass
            case GameState.Disconnected:
                pass

        rl.begin_drawing()
        rl.clear_background(rl.get_color(0x181818FF))
        rl.end_drawing()

    sock.close()
