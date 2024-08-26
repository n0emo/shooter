from typing import Dict
from abc import ABC, abstractmethod

from pyray import Vector2


class Event(ABC):
    pass


class EventHandler(ABC):
    @abstractmethod
    def handle_event(self, event: Event): ...


class Player:
    name: str
    position: Vector2
    velocity: Vector2

    def __init__(self, name: str) -> None:
        self.name = name
        self.position = Vector2(0, 0)
        self.velocity = Vector2(0, 0)

    def update(self, delta_time):
        self.position.x += self.velocity.x * delta_time
        self.position.y += self.velocity.y * delta_time


class Game:
    players: Dict[str, Player]
    event_handler: EventHandler

    def __init__(self, event_handler: EventHandler) -> None:
        self.players = {}
        self.event_handler = event_handler

    def append_player(self, player: Player) -> bool:
        if player.name in self.players.keys():
            return False

        self.players[player.name] = player

        return True


    def remove_player(self, player: Player):
        self.players.pop(player.name)

    def update(self, delta_time: float):
        for player in self.players.values():
            player.update(delta_time)
