import discord

import random
from typing import List, Tuple, Dict, Optional

from Utilities import PlayerObject, Vars
from Utilities.Combat import Effects
from Utilities.Combat.Action import Action
from Utilities.Combat.Belligerent import Belligerent
from Utilities.Combat.CombatTurn import CombatTurn


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

        # Create raw damage count
        match action:
            case Action.ATTACK:
                atk_dmg = random.randint(
                    self.actor.attack * 3 // 4, self.actor.attack * 5 // 4
                )
                result.attacks["Attack"].magnitude += atk_dmg
                result.attacks["Attack"].multiplier += 1
            case Action.BLOCK:
                brace = Effects.Brace(actor)
                actor.status.append(brace)
                brace.on_application()
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
        crit_cond = action in (Action.ATTACK, Action.PARRY)
        if crit_cond and random.randint(1, 100) <= actor.crit_rate:
            self.on_critical_hit(result)

        # Unique interactions with attack choices
        # self.run_events()

        # Process status effects
        for status in self.actor.status:
            status.on_turn(result)

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
    
    def on_critical_hit(self, data: CombatTurn):
        # Base damage boost from crit
        data.is_crit = True
        multiplier = self.actor.crit_damage / 100.0

        # Applicable acolytes: Aulus, Ayesha
        try:
            aulus = data.actor.get_acolyte("Aulus")
            data.actor.attack += aulus.get_effect_modifier(0)
        except AttributeError:
            pass

        try:
            ayesha = data.actor.get_acolyte("Ayesha")
            heal = self.actor.attack * .01 * ayesha.get_effect_modifier(0)
            data.heals["Ayesha"].magnitude += heal
            data.heals["Ayesha"].multiplier += 1
        except AttributeError:
            pass

        # Accessory Effects
        if data.target.accessory.prefix == "Shiny":  # Reduces crit dmg
            r = Vars.ACCESSORY_BONUS["Shiny"][self.target.accessory.type] / 100
            multiplier *= 1 - r

        # Apply crit bonuses
        data.attacks["Attack"].multiplier += multiplier
