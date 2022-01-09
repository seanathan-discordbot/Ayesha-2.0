import discord
from discord.commands.commands import Option, OptionChoice

from discord.ext import commands, pages
from discord.ext.commands import BucketType, cooldown

import random

from Utilities import Checks, CombatObject, ItemObject, PlayerObject, Vars
from Utilities.CombatObject import CombatInstance

class PvE(commands.Cog):
    """PvE Text"""

    def __init__(self, bot):
        self.bot = bot

    # EVENTS
    @commands.Cog.listener()
    async def on_ready(self):
        print("PvE is ready.")

    # AUXILIARY FUNCTIONS
    def level_to_rewards(self, level):
        """Returns the rarity of weapon/armor based on the level the player beat
        Dict: weapon, armor
        """
        if level < 2:
            weapon = "Common"
            armor = "Cloth"
        elif level < 5:
            weapon = "Common"
            armor = "Leather"
        elif level < 9:
            weapon = "Common"
            armor = "Gambeson"
        elif level == 9:
            weapon = "Uncommon"
            armor = "Bearskin"
        elif level == 13:
            weapon = "Uncommon"
            armor = "Wolfskin"
        elif level < 15:
            weapon = "Uncommon"
            armor = "Bronze"
        elif level < 18:
            weapon = "Rare"
            armor = "Ceramic Plate"
        elif level < 21:
            weapon = "Rare"
            armor = "Chainmail"
        elif level < 25:
            weapon = "Rare"
            armor = "Iron"
        elif level < 40:
            weapon = "Epic"
            armor = "Steel"
        elif level < 50:
            weapon = "Epic"
            armor = "Mysterious"
        else:
            weapon = "Legendary"
            armor = "Dragonscale"

        return {
            "weapon" : weapon,
            "armor" : armor
        }

    # COMMANDS
    @commands.slash_command(guild_ids=[762118688567984151])
    @commands.check(Checks.is_player)
    @cooldown(1, 15, BucketType.user)
    async def pve(self, ctx,
            level : Option(int,
                description="The difficulty level of your opponent",
                min_value=1)):
        """Fight an enemy for gold, xp, and items!"""
        async with self.bot.db.acquire() as conn:
            author = await PlayerObject.get_player_by_id(conn, ctx.author.id)
        # Create belligerents
        if level > author.pve_limit:
            return await ctx.respond(
                f"You cannot attempt this level yet! To challenge bosses past "
                f"level 25, you will have to beat each level sequentially. "
                f"You can currently challenge up to level {author.pve_limit}.")

        player = CombatObject.Belligerent.load_player(player=author)
        boss = CombatObject.Belligerent.load_boss(difficulty=level)
        
        # Main game loop
        interaction = await ctx.respond("Loading battle...")
        turn_counter = 1
        boss_next_move = random.choices(
            population=["Attack", "Block", "Parry", "Heal", "Bide"],
            weights=[50, 20, 20, 3, 7])[0]
        # Stores string information to display to player
        recent_turns = [
            f"Battle begins between **{player.name}** and **{boss.name}**.",] 
        while turn_counter <= 25: # Manually broken if HP hits 0
            # Update information display
            embed = discord.Embed(
                title=f"{player.name} vs. {boss.name} (Level {level})",
                color=Vars.ABLUE)
            embed.add_field(name="Attack", value=player.attack)
            embed.add_field(name="Crit Rate", value=f"{player.crit}%")
            embed.add_field(name="HP", value=player.current_hp)
            embed.add_field(name="Defense", value=f"{player.defense}%")
            embed.add_field(
                name=f"Enemy HP: `{boss.current_hp}`",
                value=(
                    f"🗡️ Attack, \N{SHIELD} Block, \N{CROSSED SWORDS} "
                    f"Parry, \u2764 Heal, \u23F1 Bide"),
                inline=False)
            embed.add_field(
                name=f"Turn {turn_counter}", 
                value="\n".join(recent_turns[-5:]),
                inline=False)

            view = CombatObject.ActionChoice(author_id=ctx.author.id)
            # Remaking the view every time is a bit of a problem but results
            # in more readable code than having one view handle everything
            await interaction.edit_original_message(
                content=None, embed=embed, view=view)

            # Determine belligerent actions
            await view.wait()
            if view.choice is None:
                return await ctx.respond(
                    f"You fled the battle as you ran out of time to move.")

            player.last_move = view.choice
            boss.last_move = boss_next_move
            boss_next_move = random.choices(
                population=["Attack", "Block", "Parry", "Heal", "Bide"],
                weights=[50, 20, 20, 3, 7])[0]

            # Calculate damage based off actions
            combat_turn = CombatInstance(player, boss, turn_counter)
            turn_msg = combat_turn.get_turn_str()
            if random.randint(1,100) < 55: # ~60% chance of accurate prediction 
                turn_msg += (
                    f"**{boss.name}** seems poised to "
                    f"**{boss_next_move}**!")
            else: # Throw the player off with a lie (might be true though)
                deception = random.choice(
                    ["Attack", "Block", "Parry", "Heal", "Bide"])
                turn_msg += f"**{boss.name}** seems poised to **{deception}**!"
            recent_turns.append(turn_msg)
            player, boss = combat_turn.apply_damage() # Apply to belligerents

            # Check for victory
            if boss.current_hp <= 0 or player.current_hp <= 0:
                break

            # Set up for next turn
            player, boss = CombatInstance.on_turn_end(player, boss)

            turn_counter += 1

        # With loop over, determine winner and give rewards
        async with self.bot.db.acquire() as conn:
            weapon = None
            armor = None

            if boss.current_hp <= 0: # Win
                victory = True
                if player.current_hp < 1:
                    player.current_hp = 1

                gold = random.randint(level**2 + 20, level**2 + 80)
                xp = 2**(level/10)
                xp *= (level+10)**2 # Put weight on high levels and HP
                xp *= (player.current_hp / 750) + .2
                xp = int(xp)

                # Possibly get weapons + armor
                item_rarities = self.level_to_rewards(level)
                if random.randint(1, 4) == 1 or player.type == "Merchant":
                    weapon = await ItemObject.create_weapon(
                        conn, author.disc_id, item_rarities["weapon"])

                if random.randint(1, 100) < 6: # 5% chance at armor
                    armor = await ItemObject.create_armor(
                        conn=conn, user_id=author.disc_id,
                        type=random.choice(("Helmet", "Bodypiece", "Boots")),
                        material=item_rarities['armor'])

                title = f"You have defeated {boss.name}!"
                header = f"You had {player.current_hp} HP remaining."

            else: # Loss
                victory = False
                if boss.current_hp < 1:
                    boss.current_hp = 1
                gold = 0
                xp = 5 * level + 20

                title = f"You were defeated by {boss.name}!"
                header = f"They had {boss.current_hp} HP remaining."

            # ON GAME END event technically
            acolytes = [a.acolyte_name 
                for a in (player.acolyte1, player.acolyte2)]
            if "Sean" in acolytes:
                xp = int(xp * 1.2)
            if "Spartacus" in acolytes:
                gold += 200

            # Create and send embed
            embed = discord.Embed(title=title, color=Vars.ABLUE)
            embed.add_field(
                name=header,
                value=(
                    f"You received `{gold}` gold and `{xp}` xp from the battle."
                ))
            if weapon is not None:
                embed.add_field(
                    name="While fighting you found a weapon!",
                    value=(
                        f"`{weapon.weapon_id}`: **{weapon.name}**, a  "
                        f"{weapon.rarity} {weapon.type} with {weapon.attack} "
                        f"ATK and {weapon.crit} crit."),
                    inline=False)
            if armor is not None:
                embed.add_field(
                    name="After the battle you salvaged some armor.",
                    value=(
                        f"`{armor.id}`: **{armor.name}**, with {armor.defense} "
                        f" defense!"),
                    inline=False)

            await author.give_gold(conn, gold)
            await author.check_xp_increase(conn, ctx, xp)
            await author.log_pve(conn, victory)
            if level == author.pve_limit and victory:
                await author.increment_pve_limit(conn)
                embed.set_footer(
                    text=f"You have unlocked PvE level {author.pve_limit}.")

        await interaction.edit_original_message(embed=embed, view=None)




def setup(bot):
    bot.add_cog(PvE(bot))