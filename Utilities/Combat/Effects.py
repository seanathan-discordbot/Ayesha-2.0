from abc import ABC, abstractmethod
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from Utilities.Combat.Belligerent import Belligerent


class BaseStatus(ABC):
    def __init__(self, target: Belligerent, duration: int):
        self.target = target
        self._counter = duration

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
    def on_turn(self):
        pass

    @abstractmethod
    def on_remove(self):
        pass


class Slow(BaseStatus):
    def __init__(self, amount: int, **kwargs):
        self.amount = amount
        super().__init__(**kwargs)

    def on_application(self):
        self.target.speed -= self.amount
        self.counter -= 1
    
    def on_remove(self):
        self.target.speed += self.amount
        return super().on_remove()
