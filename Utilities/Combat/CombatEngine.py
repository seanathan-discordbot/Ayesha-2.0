import discord

import random
from typing import List, Tuple, Dict, Optional

from Utilities import PlayerObject, Vars
from Utilities.Combat import Effects
from Utilities.Combat.Action import Action
from Utilities.Combat.Belligerent import Belligerent
from Utilities.Combat.CombatTurn import CombatTurn


class CombatEngine:
    """Class which provides abstract and unified access to a combat console.

    Parameters
    ----------
    player1, player2 : Belligerent
        the combatants of this specific combat instance
    turn_limit : int
        a soft limit of turns allowed in play, after which all characters 
        take extra decay damage on their turn

    Attributes
    ----------
    turn : int
        the current turn of play
    victor : Optional[Belligerent]
        the winner of the combat instance, initially set to None
    __bool__
        True if combat is still in play (if victor is None)
    actor : Belligerent
        Either of player1 or player2 who has the current turn
    target : Belligerent
        Either of player1 or player2 that is not the actor, and is subject to
        the actor's action this turn.
    """
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
        """Process the current turn with the given action. 
        This will apply the next action to the target as if the current actor
        had just played it. Returns an object describing the resulting effects.

        Parameters
        ----------
        action : Action
            the action that the current actor will perform

        Returns
        -------
        CombatTurn
            an object detailing the results of the turn and action
        """
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

                # Punish attacking an enemy that blocks
                if any(isinstance(x, Effects.Brace) for x in target.status):
                    deflection = random.randint(
                        self.target.attack * 3 // 16, 
                        self.target.attack * 5 // 16
                    )
                    result.damages["Deflection"].magnitude = deflection
                    result.damages["Deflection"].multiplier = 1
            case Action.BRACE:
                brace = Effects.Brace(actor)
                actor.status.add(brace)
                brace.on_application()
            case Action.THRUST:
                atk_dmg = random.randint(
                    actor.attack * 3 // 4, actor.attack * 5 // 4
                )
                result.attacks["Attack"].magnitude += atk_dmg
                result.attacks["Attack"].multiplier += 1

                def_break = Effects.Break(25, target=target, duration=2)
                target.status.add(def_break)
                def_break.on_application()

                slow = Effects.Slow(10, target=actor, duration=2)
                actor.status.add(slow)
                slow.on_application()
            case Action.HEAL:
                heal = self.actor.max_hp * .2
                result.heals["Heal"].magnitude += heal
                result.heals["Heal"].multiplier += 1
            case Action.BIDE:
                bide = Effects.Bide(actor)
                actor.status.add(bide)
                bide.on_application()

        # Determine critical strikes
        crit_cond = action in (Action.ATTACK, Action.THRUST)
        if crit_cond and random.randint(1, 100) <= actor.crit_rate:
            self._on_critical_hit(result)

        # Process status effects
        for status in list(self.actor.status):  # Make copy as original might get modified
            status.on_turn(result)

        # Unique interactions with attack choices
        self._run_events(result)

        # Calculate final damage
        if self.turn >= self.turn_limit:
            result.damages["Decay"].magnitude = 100
            mult = 1 + ((self.turn - self.turn_limit) / 10)**2
            result.damages["Decay"].multiplier = mult
            
            for source in result.heals:
                result.heals[source].multiplier /= 5
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
    
    def recommend_action(self, 
            actor: Belligerent, 
            data: CombatTurn, 
            k: int = 1
    ) -> List[Action]:
        """Selects an action based on a turn's data.

        Parameters
        ----------
        actor : Belligerent
            the combatant for which an action is being recommended
        data : CombatTurn
            ideally the last turn's results, which will be analyzed to recommend
            an actioin
        k : int, optional
            the amount of actions to recommend, by default 1

        Returns
        -------
        List[Action]
            a non-unique, non-ordered list of actions to recommend
        """
        if actor not in (data.actor, data.target):
            return ValueError("Actor must be one of `data.actor`, `data.target`.")
        
        # Algorithm: Randomly select from the actions with different weights
        # Weights determined as function of HP percentages of both combatants
        # Functions are completely made up!!!
        x = actor.current_hp / actor.max_hp * 100
        target = data.target if actor == data.actor else data.actor
        y = target.current_hp / target.max_hp * 100

        weights = {}
        # Attack: Scale with high HP and low enemy HP
        weights[Action.ATTACK] = max(30, x * y / 100)  # [30, 100]

        # Brace: Scale with low HP and high enemy HP
        weights[Action.BRACE] = max(30, 100 - (75*x)**(1/2))  # [30, 100]

        # Thrust: Scale with high enemy DEF
        weights[Action.THRUST] = 4 * (target.defense)**(1/2)  # [0, 40]

        # Heal: Scale with low HP
        if x >= 80:  # Heal is 20% so don't waste an action here
            weights[Action.HEAL] = 0
        else:  # Chance peaks ~10% HP, lower it drops because its a lost cause
            weights[Action.HEAL] = 100 / (abs(x-10)**(1/2) + 1)

        # Bide: Scale with high HP and high enemy HP
        weights[Action.BIDE] = (x * y / 100) / 3  # [0, 25]

        return random.choices(
            population=list(weights.keys()),
            weights=list(weights.values()),
            k=k
        )


    def set_next_actor(self):
        """Calculate and set the next combatant to move based on speed values"""
        r1 = self.player1.cooldown / self.player1.speed
        r2 = self.player2.cooldown / self.player2.speed

        if r1 <= r2:  # Player 1 reaches 0 faster, they go next
            self.actor, self.target = self.player1, self.player2
        else:
            self.actor, self.target = self.player2, self.player1

        self.player1.cooldown -= r1 * self.player1.speed
        self.player2.cooldown -= r2 * self.player2.speed 

        # while self.player1.cooldown > 0 and self.player2.cooldown > 0:
        #     self.player1.cooldown -= self.player1.speed
        #     self.player2.cooldown -= self.player2.speed
        # if self.player1.cooldown <= self.player2.cooldown:
        #     self.actor, self.target = self.player1, self.player2
        # else:
        #     self.actor, self.target = self.player2, self.player1
        self.actor.cooldown = 1000


    def get_victor(self) -> Optional[Belligerent]:
        """Return the combatant that won the battle, if it is over."""
        if self:
            raise Exception
        return self.victor
    
    def _on_critical_hit(self, data: CombatTurn):
        """If an attack was a crit, adjust the result object to reflect it."""
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

    def _run_events(self, data: CombatTurn):
        """Apply extra effects (e.g. acolytes) to the turn results"""
        # ON_DAMAGE : Apply to all damage types
        if data.attacks:
            try:
                paterius = data.actor.get_acolyte("Paterius")
                buff = paterius.get_effect_modifier(0) * .01
                for attack in data.attacks:
                    data.attacks[attack].multiplier += buff
                data.attacks["Paterius"].magnitude = 15
                data.attacks["Paterius"].multiplier = 1
            except AttributeError:
                pass

        # ON_ATTACK : Agent attacks
        if data.turn <= 3 and data.actor.occupation == "Hunter":
            data.attacks["Attack"].multiplier += 1

        if data.action == Action.ATTACK:
            try:
                alia = data.actor.get_acolyte("Alia")
                buff = Effects.SpeedBoost(
                    alia.get_effect_modifier(0),
                    target=data.actor,
                    duration=2
                )
                data.actor.status.add(buff)
                buff.on_application()
            except AttributeError:
                pass

        # ON_BRACE : Agent blocks
        if data.action == Action.BRACE:
            try:
                demi = data.actor.get_acolyte("Demi")
                damage = data.actor.defense * demi.get_effect_modifier(0) * .01
                data.attacks["Demi"].magnitude = damage
                data.attacks["Demi"].multiplier = 1
            except AttributeError:
                pass 

        # ON_THRUST : Agent parries
        if data.action == Action.THRUST:
            if random.randint(1, 4) == 1:
                try:
                    rea = data.actor.get_acolyte("Rea")
                    bleed = Effects.Bleed(
                        rea.get_effect_modifier(0),
                        target=data.target,
                        duration=3
                    )
                    data.target.status.add(bleed)
                    bleed.on_application()
                except AttributeError:
                    pass

        # ON_HEAL : Agent heals
        if data.action == Action.HEAL:
            if data.actor.occupation == "Butcher":
                for heal in data.heals:
                    data.heals[heal].multiplier += 1
            
            try:
                nyleptha = data.actor.get_acolyte("Nyleptha")
                reduction = nyleptha.get_effect_modifier(0) * .01
                for damage in data.damages:
                    data.damages[damage].multiplier -= reduction
            except AttributeError:
                pass
                
        # ON_BIDE : Agent bides
        
        # GENERAL DAMAGE CALC
        if data.target.occupation == "Leatherworker":
            for damage in data.attacks:
                data.attacks[damage].multiplier -= .15
        
        if data.target.accessory.prefix == "Thorned":
            data.apply()  # TODO: The fact that I have to do this may justify protecting the damage sums with a setter
            d = Vars.ACCESSORY_BONUS["Thorned"][data.target.accessory.type] / 100
            data.damages["Armor"].magnitude += d
            data.damages["Armor"].multiplier |= 1  # Set to 1 if 0, else keep

        # ON_COMBAT_END : After everything else has been calculated
        try:
            onion = data.actor.get_acolyte("Onion")
            if self.turn == onion.get_effect_modifier(0):
                data.actor.crit_rate *= 2
        except AttributeError:
            pass

        try:
            ajar = data.actor.get_acolyte("Ajar")
            data.actor.attack += ajar.get_effect_modifier(1)
            data.damages["Ajar"].magnitude = ajar.get_effect_modifier(2)
            data.damages["Ajar"].multiplier = 1
        except AttributeError:
            pass

        try:
            # Lauren: If you take less than x dmg in a turn, increase ATK
            data.apply()
            lauren = data.target.get_acolyte("Lauren")
            if data.attack_total < lauren.get_effect_modifier(1):
                data.target.attack *= 1 + (lauren.get_effect_modifier(0) * .01)
        except AttributeError:
            pass

        try:
            thorp = data.actor.get_acolyte("Thorp")
            modifier = 100 + thorp.get_effect_modifier(0)
            match random.randint(1, 6):
                case 1:
                    data.actor.attack = (data.actor.attack * modifier) // 100
                case 2:
                    data.actor.crit_rate = (data.actor.crit_rate * modifier) // 100
                case 3:
                    data.actor.current_hp = (data.actor.current_hp * modifier) // 100
                case 4:
                    data.actor.defense = (data.actor.defense * modifier) // 100
                case 5:
                    data.actor.crit_damage = (data.actor.crit_damage * modifier) // 100
                case 6:
                    data.actor.speed = (data.actor.speed * modifier) // 100
        except AttributeError:
            pass
