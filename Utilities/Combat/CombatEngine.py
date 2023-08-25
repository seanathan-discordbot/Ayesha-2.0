import discord

import random
from collections import defaultdict
from typing import List, Tuple, Dict, Optional

from Utilities import PlayerObject, Vars

from Utilities.CombatObject import ActionChoice, InvalidMove, ACTION_COMBOS

from Utilities.Combat import Effects
from Utilities.Combat.Action import Action
from Utilities.Combat.Belligerent import Belligerent

class Modifier:
    def __init__(self, magnitude: int = 0, multiplier: float = 0) -> None:
        self.magnitude = magnitude
        self.multiplier = multiplier
        self.final = 0
    
    def apply(self):
        self.final = int(self.magnitude * self.multiplier)


class CombatTurn:
    def __init__(
            self, 
            actor: Belligerent, 
            target: Belligerent, 
            action: Action, 
            turn: int
    ):
        if action not in Action:
            raise InvalidMove

        self.actor = actor
        self.target = target
        self.action = action
        self.turn = turn

        self.attacks: Dict[str, Modifier] = defaultdict(Modifier)  # Apply all sources of possible attacks e.g. attack action, acolyte effects, etc
        self.heals: Dict[str, Modifier] = defaultdict(Modifier)
        self.damages: Dict[str, Modifier] = defaultdict(Modifier)  # Apply all sources of possible damage at turn start e.g. poison

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
                    return f"for {self.attack_total} damage"
                case Action.PARRY:
                    return f"for {self.attack_total} damage"
                case Action.HEAL:
                    return f"for {self.heal_total} HP"
                case Action.BIDE:
                    return "bided their time to boost their attack"
                
        def breakdown(coll: Dict[str, Modifier]):
            return str(sorted(coll, key=lambda k: coll[k].final, reverse=True))
        
        if self.action == Action.DEFAULT:
            return f"Battle begins between **{self.actor.name}** and **{self.target.name}**."

        desc = f"**{self.actor.name}** {self.action.value} {action2sentence(self.action)}."
        if self.attack_total:
            desc += "\n" + breakdown(self.attacks)
        if self.heal_total:
            desc += "\n" + breakdown(self.heals)
        if self.damage_total:
            desc += "\n" + breakdown(self.damages)
        return desc

    def apply(self):  # When all things are calculated, run something like this to get stat changes
        total = 0
        for modifier in self.attacks.values():
            modifier.apply()
            total += modifier.final
        self.attack_total = total

        total = 0
        for modifier in self.heals.values():
            modifier.apply()
            total += modifier.final
        self.heal_total = total

        total = 0
        for modifier in self.damages.values():
            modifier.apply()
            total += modifier.final
        self.damage_total = total


class CombatEngine:
    def __init__(self, 
            player1: Belligerent, 
            player2: Belligerent,
            turn_limit: int = 50
    ):
        self.player1 = player1
        self.player2 = player2
        self.turn_limit = turn_limit
        
        # Prepare Battle
        self.turn = 0
        self.victor: Belligerent = None
        self.actor: Belligerent = None
        self.target: Belligerent = None

        # Select first turn
        self.set_next_actor()


    def __bool__(self):
        """Return True if combat is still in progress and victor attr is None"""
        return self.victor is None


    @classmethod
    def initialize(cls, 
            player1: Belligerent, 
            player2: Belligerent, 
            turn_limit: int = 50
    ) -> Tuple["CombatEngine", CombatTurn]:
        """Create a new Engine and carry out a dummy turn 1, returning both"""
        engine = cls(player1, player2, turn_limit)
        result = CombatTurn(player1, player2, Action.DEFAULT, 0)
        return engine, result


    def process_turn(self, action: Action) -> CombatTurn:
        """Process a new turn"""
        self.turn += 1
        actor = self.actor
        target = self.target
        result = CombatTurn(actor, target, action, self.turn)

        # Process status effects
        for status in self.actor.status:
            status.on_turn(result)

        # Create raw damage count
        match action:
            case Action.ATTACK:
                atk_dmg = random.randint(
                    self.actor.attack * 3 // 4, self.actor.attack * 5 // 4
                )
                result.attacks["Attack"].magnitude += atk_dmg
                result.attacks["Attack"].multiplier += 1
            case Action.BLOCK:
                pass  # Replace with BRACE - add DEF boost status effect
            case Action.PARRY:
                pass  # Idk maybe make a special attack
            case Action.HEAL:
                heal = self.actor.max_hp * .2
                result.heals["Heal"].magnitude += heal
                result.heals["Heal"].multiplier += 1
            case Action.BIDE:
                bide = Effects.Bide(actor)
                actor.status.append(bide)
                bide.on_application()

        # Determine critical strikes
        crit_cond = action in (Action.ATTACK, Action.BLOCK, Action.PARRY)
        if crit_cond and random.randint(1, 100) <= actor.crit_rate:
            pass  # TODO: add on_crit()

        # Calculate damage multiplier based off action combinations

        # Unique interactions with attack choices

        # Calculate final damage
        result.apply()

        # Apply all stat changes
        actor.current_hp += result.heal_total - result.damage_total
        target.current_hp -= result.attack_total

        # Check victory conditions
        if target.current_hp <= 0:
            self.victor = actor
        if actor.current_hp <= 0:
            self.victor = target

        # Create resulting object
        self.set_next_actor()
        return result
    

    def set_next_actor(self):
        while min(self.player1, self.player2).cooldown > 0:
            self.player1.cooldown -= self.player1.speed
            self.player2.cooldown -= self.player2.speed
        self.actor, self.target = sorted([self.player1, self.player2])
        self.actor.cooldown = 1000


    def get_victor(self) -> Belligerent:
        if self:
            raise Exception
        return self.victor
