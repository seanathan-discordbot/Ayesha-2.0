from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from Utilities.Combat.Belligerent import Belligerent
from Utilities.Combat.CombatTurn import CombatTurn

if TYPE_CHECKING:
    from Utilities.Combat.Belligerent import Belligerent
    from Utilities.Combat.CombatTurn import CombatTurn


class BaseStatus(ABC):
    def __init__(self, target: Belligerent, duration: int):
        self.target = target
        self._counter = duration

    def __str__(self) -> str:
        return f"{self.counter}"
    
    def __repr__(self) -> str:
        return self.__str__()

    @property
    def counter(self):
        return self._counter
    
    @counter.setter
    def counter(self, value):
        self._counter = value
        if self._counter <= 0:
            self.remove()

    def remove(self):
        self.on_remove()
        self.target.status.remove(self)  # Might be effective removal?

    @abstractmethod
    def on_application(self):
        pass

    @abstractmethod
    def on_turn(self, data: CombatTurn):  # TODO: should all methods take the data?
        pass

    @abstractmethod
    def on_remove(self):
        pass


class Brace(BaseStatus):
    def __init__(self, target: Belligerent):
        super().__init__(target, 2)  # Brace always lasts 2 turns
        self.defense_boost = 25

    def __str__(self) -> str:
        return "BRACE[" + super().__str__() + "]"

    def on_application(self):
        self.target.defense += self.defense_boost

    def on_turn(self, data: CombatTurn):
        self.counter -= 1

    def on_remove(self):
        self.target.defense -= self.defense_boost


class Bide(BaseStatus):
    def __init__(self, target: Belligerent):
        super().__init__(target, 2)  # Bide always lasts 2 turns
        self.attack_boost = int(target.base_attack * 1.1)

    def on_application(self):
        self.target.attack += self.attack_boost
    
    def on_turn(self, data: CombatTurn):
        self.counter -= 1
    
    def on_remove(self):
        self.target.attack -= self.attack_boost


class Slow(BaseStatus):
    def __init__(self, amount: int, **kwargs):
        self.amount = amount
        super.__init__(**kwargs)

    def on_application(self):
        self.target.speed -= self.amount

    def on_turn(self, data: CombatTurn):
        self.counter -= 1
    
    def on_remove(self):
        self.target.speed += self.amount
    

class Poison(BaseStatus):
    def __init__(self, amount: float, **kwargs):
        self.amount = amount
        super().__init__(**kwargs)

    def on_application(self):
        return
    
    def on_turn(self, data: CombatTurn):
        damage = data.target.current_hp * self.amount
        data.damages["Poison"].magnitude += damage

    def on_remove(self):
        return


