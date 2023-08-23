from __future__ import annotations
import discord

from abc import ABC, abstractmethod
from enum import Enum
import random

from typing import List, Optional, TYPE_CHECKING
if TYPE_CHECKING:
    from asyncpg import Connection

from Utilities import PlayerObject, Vars
from Utilities.AcolyteObject import EmptyAcolyte, InfoAcolyte, OwnedAcolyte
from Utilities.AssociationObject import Association
from Utilities.ItemObject import Accessory, Weapon, Armor


class Belligerent(ABC):
    @abstractmethod
    def __init__(self, 
            name: str, 
            attack: int, 
            crit: int, 
            hp: int,
            defense: int, 
            speed: int
        ):
        # Useful Information
        self.name = name

        # Combat Stats
        self.attack = attack
        self.crit = crit
        self.max_hp = hp
        self.current_hp = hp
        self.defense = defense
        self.speed = speed
        self.cooldown = 1000
        self.status: List[BaseStatus] = []

        # Related Objects - initialized in subclass
        self.weapon: Weapon
        self.helmet: Armor
        self.bodypiece: Armor
        self.boots: Armor
        self.accessory: Accessory
        self.acolyte1: EmptyAcolyte
        self.acolyte2: EmptyAcolyte
        self.assc: Association

    @abstractmethod
    def __str__(self) -> str:
        return f"(HP: {self.current_hp}/{self.max_hp})"

    def __lt__(self, other: "Belligerent"):
        if not isinstance(other, Belligerent):
            raise TypeError
        return self.cooldown < other.cooldown
    
    def get_acolyte(self, name: str) -> Optional[EmptyAcolyte]:
        return None


class Boss(Belligerent):
    def __init__(self, difficulty: int):
        self.difficulty = difficulty

        # Calculate Boss Stats
        if difficulty <= 25:
            name = Vars.BOSSES[difficulty]
        else:
            NAMES = ( # credit to rea
                "Spinning Sphinx", "Black Witch of the Prairie", "Crocc",
                "James Juvenile", "Shorttimber King", "Darkness of the Dark",
                "Sealed Demon Lord", "Elysia", "Three-headed Anaconda",
                "Blood Tiger", "The Great Imyutarian", "Corrupted Dragon Slayer"
            )
            name = random.choice(NAMES)

        speed = 25
        if difficulty == 1:
            attack = 1
            crit = 0
            hp = 50
            defense = 10
        elif difficulty < 16:
            attack = difficulty * 7
            crit = int(difficulty * 1.2) + 5
            hp = difficulty * 67
            defense = int(difficulty * 1.2)
        elif difficulty < 25:
            attack = difficulty * 10
            crit = int(difficulty * 1.5) + 5
            hp = difficulty * 75
            defense = int(difficulty * 1.3)
        elif difficulty < 40:
            attack = difficulty * 20
            crit = 65
            hp = difficulty * 125
            defense = 40
        elif difficulty < 50:
            attack = difficulty * 25
            crit = 75
            hp = difficulty * 140
            defense = 55
        else:
            attack = difficulty * 28
            crit = 78
            hp = difficulty * 150
            defense = 70

        super().__init__(name, attack, crit, hp, defense, speed)

        # Initialize objs
        self.weapon = Weapon()
        self.helmet = Armor()
        self.bodypiece = Armor()
        self.boots = Armor()
        self.accessory = Accessory()
        self.acolyte1 = EmptyAcolyte()
        self.acolyte2 = EmptyAcolyte()
        self.assc = Association()  

    def __str__(self) -> str:
        return f"Boss: {self.name}-{self.difficulty} " + super().__str__()


class CombatPlayer(Belligerent):
    def __init__(self, player: PlayerObject.Player):
        self.player = player

        attack = player.get_attack()
        crit = player.get_crit()
        hp = player.get_hp()
        defense = player.get_defense()
        speed = 25

        # ON_PLAYER_LOAD event lol
        try:
            arsaces = player.get_acolyte("Arsaces")
            attack += crit * arsaces.get_effect_modifier(0)
            hp += crit * arsaces.get_effect_modifier(1)
            crit = 0
        except AttributeError:
            pass

        super().__init__(player.char_name, attack, crit, hp, defense, speed) 

        # Initialize objs
        self.weapon = player.equipped_item
        self.helmet = player.helmet
        self.bodypiece = player.bodypiece
        self.boots = player.boots
        self.accessory = player.accessory
        self.acolyte1 = player.acolyte1
        self.acolyte2 = player.acolyte2
        self.assc = player.assc

    @classmethod
    async def from_id(cls, conn: Connection, user_id: int):
        """Create a CombatPlayer using a discord user's ID."""
        return cls(await PlayerObject.get_player_by_id(conn, user_id))

    def __str__(self) -> str:
        return f"Player: {self.name}-{self.player.level} " + super().__str__()

    def get_acolyte(self, name: str) -> Optional[EmptyAcolyte]:
        """Returns the equipped acolyte with the name given. If no acolyte
        with the name is equipped, `None` is returned
        """
        if self.acolyte1.name == name:
            return self.acolyte1
        elif self.acolyte2.name == name:
            return self.acolyte2
        else:
            return None


class BaseStatus:
    def __init__(self, target: Belligerent, duration: int):
        self.target = target
        self.counter = duration

    def on_application(self):
        pass

    def on_turn(self):
        self.counter -= 1

    def on_remove(self):
        pass

class Slow(BaseStatus):
    def __init__(self, amount: int, **kwargs):
        self.amount = amount
        super().__init__(**kwargs)

    def on_application(self):
        self.target.speed -= self.amount
        return super().on_application()
    
    def on_remove(self):
        self.target.speed += self.amount
        return super().on_remove()
    

if __name__ == "__main__":
    x = Belligerent(16)
    y = Belligerent(34)

    # for _ in range(5):
    #     print(set_next_actor(x, y), x.cooldown, y.cooldown)

    status = Slow(5, target=x, duration=2)
    print(status.__dict__)