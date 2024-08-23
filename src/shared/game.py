from typing import Dict, List
from dataclasses import dataclass

from threading import Lock


@dataclass
class Vector2:
    x: float
    y: float


class Player:
    name: str
    position: Vector2

    def __init__(self, name: str) -> None:
        self.name = name


class Game:
    players: Dict[str, Player]
    lock: Lock

    def __init__(self) -> None:
        self.players = {}
        self.lock = Lock()

    def append_player(self, player: Player) -> bool:
        with self.lock:
            if player.name in self.players.keys():
                return False

            self.players[player.name] = player

        return True


    def remove_player(self, player: Player):
        with self.lock:
            self.players.pop(player.name)

