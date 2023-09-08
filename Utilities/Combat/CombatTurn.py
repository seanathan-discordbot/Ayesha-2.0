from __future__ import annotations

from collections import defaultdict
from typing import Dict, TYPE_CHECKING

from Utilities.Combat.Action import Action, InvalidAction
from Utilities.Combat.Modifier import Modifier

if TYPE_CHECKING:
    from Utilities.Combat.Belligerent import Belligerent
    

class CombatTurn:
    """A summary of a turn's results from CombatEngine.

    Parameters
    ----------
    actor, target : Belligerent
        the participants of the combat turn
    action : Action.Action
        the action taken by the actor
    turn : int
        the current turn number

    Attributes
    ----------
    attacks: defaultdict[str, Modifier]
        a collection of sources that contributed to the damage dealt by the
        actor to the target
    heals: defaultdict[str, Modifier]
        a list of sources that contributed to the actor's heals
    damages: defaultdict[str, Modifier]
        a list of sources that caused damage to the actor this turn
    is_crit: bool
        whether the action this turn was a critical hit
    attack_total: int
        the sum of attack damages (before DEF-application) from attacks
    heal_total: int
        the sum of healing from heals
    damage_total: int
        the sum of damage taken from damages
    description: str
        a quick summary of all other information encapsulated in this object

    Raises
    ------
    Action.InvalidAction
        if the action provided is not one of the `Action.Action`s
    """
    def __init__(
            self, 
            actor: Belligerent, 
            target: Belligerent, 
            action: Action, 
            turn: int
    ):
        if action not in Action:
            raise InvalidAction

        self.actor = actor
        self.target = target
        self.action = action
        self.turn = turn

        self.attacks: Dict[str, Modifier] = defaultdict(Modifier)  # Apply all sources of possible attacks e.g. attack action, acolyte effects, etc
        self.heals: Dict[str, Modifier] = defaultdict(Modifier)
        self.damages: Dict[str, Modifier] = defaultdict(Modifier)  # Apply all sources of possible damage at turn start e.g. poison

        self.is_crit = False
        self.attack_total = 0
        self.heal_total = 0
        self.damage_total = 0

    def __str__(self) -> str:
        return (
            f"```"
            f"{self.action} {self.turn}"
            f"{self.attacks} {self.heals} {self.damages}"
            f"{self.attack_total} {self.heal_total} {self.damage_total}"
            f"```"
        )
    
    def __repr__(self) -> str:
        return self.__str__()
    
    @property
    def description(self):
        def action2sentence(action: Action):
            match action:
                case Action.ATTACK:
                    return f"for {self.attack_total} damage"
                case Action.BRACE:
                    return f"braced for an attack, boosting their defense"
                case Action.THRUST:
                    return f"for {self.attack_total} damage"
                case Action.HEAL:
                    return f"for {self.heal_total} HP"
                case Action.BIDE:
                    return "bided their time to boost their attack"
                
        def breakdown(coll: Dict[str, Modifier]):
            keys = sorted(coll, key=lambda k: coll[k].final, reverse=True)
            sources = [
                f"{k} ({int(coll[k].magnitude)}\*{coll[k].multiplier:.2f})"
                for k in keys
            ]
            return ", ".join(sources)
        
        if self.action == Action.DEFAULT:
            return f"Battle begins between **{self.actor.name}** and **{self.target.name}**."

        desc = (
            f"**{self.actor.name}** {'critically' if self.is_crit else ''} "
            f"{self.action.value} {action2sentence(self.action)}."
        )
        if self.attack_total:
            desc += "\n**Attack Sources:** " + breakdown(self.attacks)
        if self.heal_total:
            desc += "\n**Heal Sources:** " + breakdown(self.heals)
        if self.damage_total:
            desc += "\n**Damage Sources:** " + breakdown(self.damages)
        return desc

    def apply(self):  # When all things are calculated, run something like this to get stat changes
        """Set the attack_total, heal_total, and damage_total based on all
        sources in their respective collection.
        """
        total = 0
        for modifier in self.attacks.values():
            modifier.apply()
            total += modifier.final
        defense = self.target.defense * (100 - self.actor.armor_pen) / 100
        total *= (100 - defense) / 100
        self.attack_total = int(total)

        total = 0
        for modifier in self.heals.values():
            modifier.apply()
            total += modifier.final
        self.heal_total = int(total)

        total = 0
        for modifier in self.damages.values():
            modifier.apply()
            total += modifier.final
        defense = self.actor.defense * (100 - self.target.armor_pen) / 100
        total *= (100 - defense) / 100
        self.damage_total = int(total)
