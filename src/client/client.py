from enum import IntEnum
from queue import Queue
import threading
from time import sleep

import pyray as rl
from raylib import ffi

from ..shared import net
from ..shared.game import Game, Player
from ..shared.settings import SERVER_ADDRESS


class GameState(IntEnum):
    Menu = 1
    Started = 2
    Disconnected = 3


game = Game(None)
state = GameState.Menu
sock = net.MessageSocket()

name_input = ffi.new("char[160]") # type: ignore
pointer = ffi.addressof(name_input) # type: ignore

queue = Queue()
stop_event = threading.Event()
recieve_thread = None

current_player = None

def connect(player: Player):
    sock.sock.setblocking(True)
    sock.send(net.PlayerConnectStruct(player.name.encode()), SERVER_ADDRESS)
    hello, _ = sock.recieve()
    assert isinstance(hello, net.HelloStruct)
    sock.sock.setblocking(False)


def disconnect(player: Player):
    stop_event.set()
    sleep(0.01)
    sock.sock.setblocking(True)
    sock.send(net.PlayerDisconnectStruct(player.name.encode()), SERVER_ADDRESS)
    sock.sock.setblocking(False)

def main():
    global state
    global game
    global sock
    global name_input
    global pointer
    global queue
    global recieve_thread
    global current_player

    rl.init_window(800, 600, "Shooter")
    rl.set_target_fps(60)

    should_close = False
    while not should_close:
        should_close = rl.window_should_close()

        match state:
            case GameState.Menu:
                rl.draw_text("Enter your name", 100, 50, 48, rl.WHITE)
                rl.gui_text_box(
                    rl.Rectangle(100, 100, 400, 50),
                    pointer, # type: ignore
                    20,
                    True
                )
                if rl.gui_button(
                    rl.Rectangle(450, 150, 50, 25),
                    "Enter"
                ):
                    name = ffi.string(name_input)
                    assert isinstance(name, bytes)
                    name = name.decode()
                    player = Player(name)
                    try:
                        connect(player)
                        state = GameState.Started
                        recieve_thread = sock.create_recieve_thread(queue, stop_event)
                        recieve_thread.start()
                        current_player = player
                        game.append_player(current_player)
                    except Exception as e:
                        print(e)
                        raise e

            case GameState.Started:
                assert isinstance(current_player, Player)

                if should_close:
                    disconnect(current_player)
                    break

                while queue.qsize() > 0:
                    message, address = queue.get_nowait()
                    if isinstance(message, net.PlayerConnectStruct):
                        name = message.name_decoded
                        player = Player(name)
                        game.append_player(player)

                    elif isinstance(message, net.PlayerUpdateStruct):
                        name = message.name_decoded
                        if name in game.players:
                            player = game.players[message.name_decoded]

                            player.position.x = message.pos_x
                            player.position.y = message.pos_y
                            player.velocity.x = message.vel_x
                            player.velocity.y = message.vel_y

                    elif isinstance(message, net.PlayerDisconnectStruct):
                        name = message.name_decoded
                        if name in game.players:
                            game.players.pop(name)


                x = 0
                y = 0
                speed = 100
                if rl.is_key_down(rl.KeyboardKey.KEY_A):
                    x = -speed
                elif rl.is_key_down(rl.KeyboardKey.KEY_D):
                    x = speed

                if rl.is_key_down(rl.KeyboardKey.KEY_W):
                    y = -speed
                elif rl.is_key_down(rl.KeyboardKey.KEY_S):
                    y = speed

                current_player.velocity.x = x
                current_player.velocity.y = y

                game.update(rl.get_frame_time())
                for player in game.players.values():
                    rl.draw_circle_v(player.position, 10, rl.RED)

                update_player = net.PlayerUpdateStruct(
                    current_player.name.encode(),
                    current_player.position.x,
                    current_player.position.y,
                    current_player.velocity.x,
                    current_player.velocity.y
                )
                sock.send(update_player, SERVER_ADDRESS)

            case GameState.Disconnected:
                pass

        rl.begin_drawing()
        rl.clear_background(rl.get_color(0x181818FF))
        rl.end_drawing()

    sock.close()
