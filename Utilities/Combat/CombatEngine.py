import discord

import random
from typing import Optional

from Utilities import PlayerObject, Vars

from Utilities.CombatObject import ActionChoice, InvalidMove, ACTION_COMBOS
from Utilities.Combat.Belligerent import Belligerent


class CombatTurn:
    def __init__(self):
        pass


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

        # Select first turn
        self.set_next_actor()


    def __bool__(self):
        """Return True if combat is still in progress and victor attr is None"""
        return self.victor is None


    def process_turn(self, action: Action) -> CombatTurn:
        """Process a new turn"""
        self.turn += 1
        damage, damage_multiplier = 0, 0
        heal, heal_multiplier = 0, 0
        is_crit = False

        # Process status effects

        # Create raw damage count
        if action not in Action:
            raise InvalidMove

        match action:
            case Action.ATTACK:
                damage = random.randint(
                    self.actor.attack * 0.75, self.actor.attack * 1.25
                )
                damage_multiplier += 1
            case Action.BLOCK:
                pass  # Replace with BRACE - add DEF boost status effect
            case Action.PARRY:
                pass  # Idk maybe make a special attack
            case Action.HEAL:
                heal = self.actor.max_hp * .2
                heal_multiplier += 1
            case Action.BIDE:
                self.actor.attack *= 1.05

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
        self.actor = min(self.player1, self.player2)
        self.actor.cooldown = 1000


    def get_victor(self) -> Belligerent:
        if self:
            raise Exception
        return self.victor
