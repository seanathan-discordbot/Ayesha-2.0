from __future__ import annotations

from collections import defaultdict
from typing import Dict, TYPE_CHECKING

from Utilities.Combat.Action import Action, InvalidAction
from Utilities.Combat.Modifier import Modifier

if TYPE_CHECKING:
    from Utilities.Combat.Belligerent import Belligerent
    

class CombatTurn:
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
                case Action.BLOCK:
                    return f"braced for an attack, boosting their defense"
                case Action.PARRY:
                    return f"for {self.attack_total} damage"
                case Action.HEAL:
                    return f"for {self.heal_total} HP"
                case Action.BIDE:
                    return "bided their time to boost their attack"
                
        def breakdown(coll: Dict[str, Modifier]):
            keys = sorted(coll, key=lambda k: coll[k].final, reverse=True)
            sources = [
                f"{k} ({coll[k].magnitude}\*{coll[k].multiplier})"
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
