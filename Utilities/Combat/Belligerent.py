from __future__ import annotations

from abc import ABC, abstractmethod
import random

from typing import Set, Optional, TYPE_CHECKING
if TYPE_CHECKING:
    from asyncpg import Connection
    from Utilities.Combat.Effects import BaseStatus

from Utilities import PlayerObject, Vars
from Utilities.AcolyteObject import EmptyAcolyte
from Utilities.AssociationObject import Association
from Utilities.ItemObject import Accessory, Weapon, Armor

class Belligerent(ABC):
    """Base class for the Combat engine combatants.
    
    Attributes
    ----------
    self.is_player: bool
        Whether the Belligerent is connected to a player
    self.cooldown: int
        An internal value that gets decremented until the Belligerent gets their
        turn in combat, before being reset to 1000
    self.status: Set[BaseStatus]
        a collection of the status effects applied to the Belligerent
    """
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
        self._current_hp = hp
        self.defense = defense
        self.speed = speed
        self.cooldown = 1000
        self.armor_pen = armor_pen
        self.status: Set[BaseStatus] = set()

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
    
    @property
    def current_hp(self):
        return self._current_hp
    
    @current_hp.setter
    def current_hp(self, value: int):
        self._current_hp = min(value, self.max_hp)

    def get_acolyte(self, name: str) -> Optional[EmptyAcolyte]:
        """Return the acolyte queried if the Belligerent has them equipped."""
        return None


class Boss(Belligerent):
    """The Belligerent class specifically for NPC combatants.

    Parameters
    ----------
    difficulty : int
        the difficulty level of the boss

    Attributes
    ----------
    difficulty : int
        the difficulty level of the boss
    """
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
        attack = 5 * (difficulty**(7/4)) // 6
        crit_rate = int(min((difficulty/3)**(15/8), 75))
        crit_damage = max(difficulty+25, 50)
        hp = int((3600 / (1 + (2.718)**(-(difficulty-16)/5))) - 100)
        defense = min(difficulty * 8 // 7, 65)
        speed = min(difficulty//2 + 20, 40)
        armor_pen = 0 if difficulty < 25 else 10

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
    """The Belligerent class specifically for player combatants.

    Parameters
    ----------
    player : PlayerObject.Player
        the player that this Belligerent is attached to.

    Attributes
    ----------
    player : PlayerObject.Player
        the underlying Player object for the Belligerent
    """
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

        try:
            cheez = player.get_acolyte("Cheez")
            crit_damage += int(crit_rate * cheez.get_effect_modifier(0) / 100)
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
