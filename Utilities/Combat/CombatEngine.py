import discord

import random
from collections import defaultdict
from typing import List, Tuple, Dict, Optional

from Utilities import PlayerObject, Vars

from Utilities.CombatObject import ActionChoice, InvalidMove, ACTION_COMBOS

from Utilities.Combat.Action import Action
from Utilities.Combat.Belligerent import Belligerent

class Modifier:
    def __init__(self, magnitude: int = 0, multiplier: float = 1.0) -> None:
        self.magnitude = magnitude
        self.multiplier = multiplier


class CombatTurn:
    def __init__(
            self, 
            actor: Belligerent, 
            target: Belligerent, 
            action: Action, turn: int
    ):
        self.actor = actor
        self.target = target
        self.turn = turn

        self.attacks: Dict[str, Modifier] = defaultdict(Modifier)  # Apply all sources of possible attacks e.g. attack action, acolyte effects, etc
        self.heals: Dict[str, Modifier] = defaultdict(Modifier)
        self.damages: Dict[str, Modifier] = defaultdict(Modifier)  # Apply all sources of possible damage at turn start e.g. poison

    def apply(self):  # When all things are calculated, run something like this to get stat changes
        damage_taken = 0
        for source in self.damages:
            damage_taken += source.magnitude
        self._damage_taken = damage_taken


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
        result = CombatTurn()
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
        if action not in Action:
            raise InvalidMove

        # match action:
        #     case Action.ATTACK:
        #         damage = random.randint(
        #             self.actor.attack * 0.75, self.actor.attack * 1.25
        #         )
        #         damage_multiplier += 1
        #     case Action.BLOCK:
        #         pass  # Replace with BRACE - add DEF boost status effect
        #     case Action.PARRY:
        #         pass  # Idk maybe make a special attack
        #     case Action.HEAL:
        #         heal = self.actor.max_hp * .2
        #         heal_multiplier += 1
        #     case Action.BIDE:
        #         self.actor.attack *= 1.05

        # Determine critical strikes

        # Calculate damage multiplier based off action combinations

        # Unique interactions with attack choices

        # Calculate final damage

        # Apply all stat changes

        # Check victory conditions

        # Create resulting object
        self.set_next_actor()
        return CombatTurn
    

    def set_next_actor(self):
        while min(self.player1, self.player2).cooldown > 0:
            self.player1.cooldown -= self.player1.speed
            self.player2.cooldown -= self.player2.speed
        self.actor, self.target, *other = sorted(self.player1, self.player2)
        self.actor.cooldown = 1000


    def get_victor(self) -> Belligerent:
        if self:
            raise Exception
        return self.victor
