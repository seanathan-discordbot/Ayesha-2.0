from __future__ import annotations

from abc import ABC, abstractmethod
import random

from typing import List, Optional, TYPE_CHECKING
if TYPE_CHECKING:
    from asyncpg import Connection
    from Utilities.Combat.Effects import BaseStatus

from Utilities import PlayerObject, Vars
from Utilities.AcolyteObject import EmptyAcolyte
from Utilities.AssociationObject import Association
from Utilities.ItemObject import Accessory, Weapon, Armor

class Belligerent(ABC):
    @abstractmethod
    def __init__(self, 
            name: str, 
            occupation: str,
            attack: int, 
            crit_rate: int, 
            crit_damage: int,
            hp: int,
            defense: int, 
            speed: int,
            armor_pen: int
        ):
        # Useful Information
        self.name = name
        self.occupation = occupation
        self.is_player = False

        # Combat Stats
        self.base_attack = attack
        self.attack = attack
        self.crit_rate = crit_rate
        self.crit_damage = crit_damage
        self.max_hp = hp
        self.current_hp = hp
        self.defense = defense
        self.speed = speed
        self.cooldown = 1000
        self.armor_pen = armor_pen
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

        occupation = "Boss"
        speed = 25
        crit_damage = 50
        armor_pen = 0
        if difficulty == 1:
            attack = 1
            crit_rate = 0
            hp = 50
            defense = 10
        elif difficulty < 16:
            attack = difficulty * 7
            crit_rate = int(difficulty * 1.2) + 5
            hp = difficulty * 67
            defense = int(difficulty * 1.2)
        elif difficulty < 25:
            attack = difficulty * 10
            crit_rate = int(difficulty * 1.5) + 5
            hp = difficulty * 75
            defense = int(difficulty * 1.3)
        elif difficulty < 40:
            attack = difficulty * 20
            crit_rate = 65
            hp = difficulty * 125
            defense = 40
        elif difficulty < 50:
            attack = difficulty * 25
            crit_rate = 75
            hp = difficulty * 140
            defense = 55
        else:
            attack = difficulty * 28
            crit_rate = 78
            hp = difficulty * 150
            defense = 70

        super().__init__(
            name, occupation, attack, crit_rate, crit_damage, hp, defense, 
            speed, armor_pen)

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
        
        occupation = player.occupation
        attack = player.get_attack()
        crit_rate = player.get_crit_rate()
        crit_damage = player.get_crit_damage()
        hp = player.get_hp()
        defense = player.get_defense()
        speed = player.get_speed()
        armor_pen = player.get_armor_pen()

        # ON_PLAYER_LOAD event lol
        try:
            arsaces = player.get_acolyte("Arsaces")
            attack += crit_rate * arsaces.get_effect_modifier(0)
            hp += crit_rate * arsaces.get_effect_modifier(1)
            crit_rate = 0
        except AttributeError:
            pass

        super().__init__(player.char_name, occupation, attack, crit_rate, crit_damage, hp, defense, speed, armor_pen) 
        self.is_player = True

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
