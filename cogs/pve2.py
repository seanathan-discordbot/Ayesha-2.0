import discord
from discord import Option, OptionChoice

from discord.ext import commands
from discord.ext.commands import BucketType, cooldown

import asyncio
import random
import time
from typing import Iterable, Tuple

from Utilities import Checks, Vars, ItemObject
from Utilities.Analytics import stringify_gains
from Utilities.AyeshaBot import Ayesha
from Utilities.Combat import Action, Belligerent, CombatEngine


class pve2(commands.Cog):
    def __init__(self, bot: Ayesha) -> None:
        self.bot = bot


    # EVENTS
    @commands.Cog.listener()
    async def on_ready(self):
        print("PvE2 is ready.")

    # AUXILIARY FUNCTIONS
    def list2str(self, arr: Iterable):
        return " ".join(str(x) for x in arr)
    
    def gold(self, level: int):
        return random.randint(level**2 + 20, level**2 + 80)
    
    def xp(self, level: int, hp: int):
        return int(2**(level/10) * (level+10)**2 * (hp / 750 + .2))
    
    def level2items(self, level: int) -> Tuple[str, str]:
        if level <= 0:
            raise ValueError("Level must be a positive integer")
        armor = accessory = None
        match level:
            case a if level in (1, 2):
                armor = "Cloth"
                accessory = random.choice(["Wood", "Glass", "Copper"])
            case b if level in (3, 4, 5):
                armor = "Leather"
                accessory = random.choice(["Glass", "Copper", "Jade"])
            case c if level in (6, 7, 8):
                armor = "Gambeson"
                accessory = random.choice(["Copper", "Jade", "Pearl"])
            case d if level in (9,):
                armor = "Bearskin"
                accessory = random.choice(["Copper", "Jade", "Pearl"])
            case e if level in (10, 11, 12, 14, 15):
                armor = "Bronze"
                accessory = "Sapphire"
            case f if level in (13,):
                armor = "Wolfskin"
                accessory = random.choice(["Pearl", "Aquamarine", "Sappire"])
            case g if level in (16, 17):
                armor = "Ceramic Plate"
                accessory = random.choice(["Sapphire", "Amethyst"])
            case h if level in (18, 19, 20):
                armor = "Chainmail"
                accessory = random.choice(["Sapphire", "Amethyst", "Ruby"])
            case i if level in (21, 22, 23, 24):
                armor = "Iron"
                accessory = random.choice(["Ruby", "Garnet"])
            case j if level in range(25, 41):
                armor = "Steel"
                accessory = random.choice(["Ruby", "Garnet", "Diamond"])
            case k if level in range(41, 51):
                armor = random.choice(["Steel", "Mysterious"])
                accessory = random.choice(["Garnet", "Diamond", "Emerald"])
            case DEFAULT:
                armor = random.choice(["Mysterious", "Dragonscale"])
                accessory = random.choice(["Emerald", "Black Opal"])
            
        return armor, accessory

    # COMMANDS
    @commands.slash_command()
    @commands.check(Checks.is_player)
    @cooldown(1, 15, BucketType.user)
    async def pve2(self, ctx: discord.ApplicationContext,
            level : Option(int,
                description="The difficulty level of your opponent",
                min_value=1),
            auto : Option(str,
                description=(
                    "Play interactive with buttons or simulate an automatic "
                    "battle for decreased rewards"),
                choices = [
                    OptionChoice("Play Interactively", "Y"),
                    OptionChoice("Play Auto (Decreased Rewards)", "N")],
                required = False,
                default = "Y")):
        """Fight an enemy for gold, xp, and items!"""
        # Create Belligerents
        async with self.bot.db.acquire() as conn:
            player = await Belligerent.CombatPlayer.from_id(conn, ctx.author.id)

        if level > player.player.pve_limit:
            return await ctx.respond(
                f"You cannot attempt this level yet! To challenge bosses past "
                f"level 25, you will have to beat each level sequentially. You "
                f"can currently challenge up to level {player.player.pve_limit}.")

        interaction = await ctx.respond("Loading battle...")
        boss = Belligerent.Boss(level)

        # Main Game Loop
        engine, results = CombatEngine.CombatEngine.initialize(player, boss)
        while engine:
            actor = engine.actor
            view = None
            
            embed = discord.Embed(
                title=f"{player.name} vs. {boss.name} (Level {level})",
                color=Vars.ABLUE
            )
            embed.set_thumbnail(url="https://i.imgur.com/d7srIjy.png")
            embed.add_field(name="Attack", value=player.attack)
            embed.add_field(
                name="Crit Rate/Damage", 
                value=f"{player.crit_rate}%/+{player.crit_damage}%"
            )
            embed.add_field(
                name="HP",
                value=f"{player.current_hp}/{player.max_hp}"
            )
            embed.add_field(name="Defense", value=f"{player.defense}%")
            embed.add_field(name="Speed", value=player.speed)
            embed.add_field(name="DEF Pen", value=player.armor_pen)
            embed.add_field(
                name=f"Enemy HP: `{boss.current_hp}`   {self.list2str(boss.status)}",
                value=(
                    f"🗡️ Attack, \N{SHIELD} Block, \N{CROSSED SWORDS} "
                    f"Parry, \u2764 Heal, \u23F1 Bide"),
                inline=False)
            embed.add_field(
                name=f"Turn {results.turn}   {self.list2str(player.status)}", 
                value=results.description,
                inline=False)

            if actor.is_player:
                # Update information display
                view = Action.ActionView(ctx.author.id)
                await interaction.edit_original_message(
                    content=None,
                    embed=embed,
                    view=view
                )

                await view.wait()
                if not view.choice:
                    return await ctx.respond(
                        f"You fled the battle as you ran out of time to move.")
                action = view.choice
            else:
                await interaction.edit_original_message(
                    content=None,
                    embed=embed,
                    view=None
                )
                action = Action.Action.ATTACK
                await asyncio.sleep(3)  # If boss turn, let player read results

            # Process turn and generate responses
            results = engine.process_turn(action)

        # Process Game End; `results` will hold last turn info
        victor = engine.get_victor()

        async with self.bot.db.acquire() as conn:
            if isinstance(victor, Belligerent.CombatPlayer):  # Victory condition
                victory = True
                gold = self.gold(level)
                xp = self.xp(level, player.current_hp)
                armor = accessory = weapon = None

                armor_type, accessory_type = self.level2items(level)
                if random.randint(1, 15) == 1:
                    armor = await ItemObject.create_armor(
                        conn=conn,
                        user_id=player.player.disc_id,
                        type=random.choice(("Helmet", "Bodypiece", "Boots")),
                        material=armor_type
                    )
                if random.randint(1, 20) == 1:
                    accessory = await ItemObject.create_accessory(
                        conn=conn,
                        user_id=player.player.disc_id,
                        type=accessory_type,
                        prefix=random.choice(list(Vars.ACCESSORY_BONUS))
                    )
                if random.randint(1, 10) == 1 or player.occupation == "Merchant":
                    if level <= 30:
                        weapon = await ItemObject.create_weapon(
                            conn, player.player.disc_id)
                    elif level <= 50:
                        attack = random.randint(120, 140)
                        crit_rate = random.randint(10, 20)
                        weapon = await ItemObject.create_weapon(
                            conn, player.player.disc_id, attack, crit_rate
                        )
                    else:
                        attack = random.randint(130, 150)
                        crit_rate = random.randint(15, 20)
                        weapon = await ItemObject.create_weapon(
                            conn, player.player.disc_id, attack, crit_rate
                        )

                title = f"You have defeated {boss.name}!"
                header = f"You had {player.current_hp} HP remaining."

            else:
                victory = False
                gold = 0
                xp = 5 * level + 20

                title = f"You were defeated by {boss.name}!"
                header = f"They had {boss.current_hp} HP remaining."

            # ON_GAME_END : Other event that's independent of combat
            # Lines of code for combat: 50, calculating rewards: 99999999999 wth
            gold_bonus, gold_bonus_sources = 0, []
            xp_bonus, xp_bonus_sources = 0, []
            try:
                sean = player.get_acolyte("Sean")
                bonus = int(xp * (sean.get_effect_modifier(0) * .01))
                xp_bonus += bonus
                xp_bonus_sources.append((bonus, "Sean"))
            except AttributeError:
                pass

            try:
                spartacus = player.get_acolyte("Spartacus")
                bonus = spartacus.get_effect_modifier(0)
                gold_bonus += bonus
                gold_bonus_sources.append((bonus, "Spartacus"))
            except AttributeError:
                pass

            if player.accessory.prefix == "Lucky":
                mult = Vars.ACCESSORY_BONUS["Lucky"][player.accessory.type]
                bonus = int(xp * (mult / 100.0))
                xp_bonus += bonus
                xp_bonus_sources.append((bonus, "Lucky Accessory"))
                bonus = int(gold * (mult / 100.0))
                gold_bonus += bonus
                gold_bonus_sources.append((bonus, "Lucky Accessory"))
            if player.accessory.prefix == "Old" and level >= 25 and victory:
                gravitas = Vars.ACCESSORY_BONUS["Old"][player.accessory.type]
                await player.player.give_gravitas(conn, gravitas)
            try: # 20% booster for 30 minutes after voting for bot
                if int(time.time()) < self.bot.recent_voters[player.player.disc_id]:
                    bonus = xp // 5
                    xp_bonus += bonus
                    xp_bonus_sources.append((bonus, "voting for the bot"))
                    bonus = gold // 5
                    gold_bonus += bonus
                    gold_bonus_sources.append((bonus, "voting for the bot"))
            except KeyError:
                pass
            gold += gold_bonus
            xp += xp_bonus

            await player.player.give_gold(conn, gold)
            await player.player.check_xp_increase(conn, ctx, xp)
            await player.player.log_pve(conn, victory)
            if level == player.player.pve_limit and victory:
                await player.player.increment_pve_limit(conn)
                embed.set_footer(
                    text=f"You have unlocked PvE level {player.player.pve_limit}.")

        # Create and send result embed
        gold_gains_str = stringify_gains("gold", gold, gold_bonus_sources)
        xp_gains_str = stringify_gains("xp", xp, xp_bonus_sources)
        embed = discord.Embed(title=title, color=Vars.ABLUE)
        embed.add_field(
            name=header,
            value=(
                f"You received {gold_gains_str} and {xp_gains_str} "
                f"from the battle."))
        if weapon is not None:
            embed.add_field(
                name="While fighting you found a weapon!",
                value=(
                    f"`{weapon.weapon_id}`: **{weapon.name}**, a  "
                    f"{weapon.type} with {weapon.attack} "
                    f"ATK and {weapon.crit} crit."),
                inline=False)
        if armor is not None:
            embed.add_field(
                name="After the battle you salvaged some armor.",
                value=(
                    f"`{armor_type.id}`: **{armor_type.name}**, with {armor_type.defense} "
                    f" defense!"),
                inline=False)
        if accessory is not None:
            embed.add_field(
                name="You also retrieved a beautiful accessory!",
                value=(
                    f"`{accessory_type.id}`: **{accessory_type.name}**"),
                inline=False)

        await interaction.edit_original_message(embed=embed, view=None)

        
def setup(bot: Ayesha):
    bot.add_cog(pve2(bot))
