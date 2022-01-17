import discord
from discord import Option, OptionChoice
from discord.commands.context import ApplicationContext

from discord.ext import commands
from discord.ext.commands import BucketType, cooldown

import random

from Utilities import Checks, ItemObject, PlayerObject, Vars

class Raid(commands.Cog):
    """Raid Text"""

    def __init__(self, bot):
        self.bot = bot
        self.raid_info = {
            "Active" : False,
            "Enemy" : None,
            "Max_HP" : 0,
            "HP" : 0,
            "Message" : None
        }
        self.raid_participants = {}

    # EVENTS
    @commands.Cog.listener()
    async def on_ready(self):
        print("Raid is ready.")

    # COMMANDS
    r = discord.commands.SlashCommandGroup("raid", 
        "Commands related to the raid mechanic", )

    @r.command()
    @commands.check(Checks.is_player)
    @cooldown(1, 900, BucketType.user)
    async def attack(self, ctx):
        """Attack the current raid if it exists."""
        if not self.raid_info["Active"]:
            ctx.command.reset_cooldown(ctx)
            return await ctx.respond((
                f"No raid is currently being fought. Wait for one to start "
                f"in {self.bot.announcement_channel.mention}!"))

        async with self.bot.db.acquire() as conn:
            player = await PlayerObject.get_player_by_id(conn, ctx.author.id)

        damage = random.randint(int(player.get_attack() / 2), 
            int(player.get_attack() * 1.5))
        if player.occupation == "Soldier":
            damage = int(damage * 1.5)

        self.raid_info['HP'] -= damage
        try:
            self.raid_participants[player.disc_id] += damage
        except KeyError:
            self.raid_participants[player.disc_id] = damage
        
        await ctx.respond((
            f"Your attack dealt **{damage}** damage to the "
            f"**{self.raid_info['Enemy']}**."))
        await self.bot.announcement_channel.send((
            f"**{ctx.author.name}#{ctx.author.discriminator}** dealt "
            f"**{damage}** attack, for a total of "
            f"**{self.raid_participants[ctx.author.id]}** damage this "
            f"campaign!"))

        # End the raid if applicable
        if self.raid_info['HP'] < 0:
            self.raid_info['HP'] = 99999 # in case of concurrency issues
            async with self.bot.db.acquire() as conn:
                weapon = await ItemObject.create_weapon(
                    conn, ctx.author.id, "Legendary")
                await self.raid_info['Message'].reply((
                    f"**{ctx.author.name}#{ctx.author.discriminator}** dealt "
                    f"the finishing blow to {self.raid_info['Enemy']}. As the "
                    f"enemy fled, they dropped a legendary weapon:\n"
                    f"- **{weapon.name}**, a {weapon.type} with "
                    f"`{weapon.attack}` ATK and `{weapon.crit}%` CRIT.\n\n"
                    f"Every participant received a gold bonus equal to the "
                    f"amount of damage they took this campaign."))
                self.raid_info = {
                    "Active" : False,
                    "Enemy" : None,
                    "Max_HP" : 0,
                    "HP" : 0,
                    "Message" : None
                }
            
                for p in self.raid_participants:
                    temp = await PlayerObject.get_player_by_id(conn, p)
                    await temp.give_gold(conn, self.raid_participants[p] * 3)

                self.raid_participants = {}

    @r.command()
    @commands.check(Checks.is_player)
    @commands.check(Checks.is_admin)
    async def secret(self, ctx : ApplicationContext, 
            spawn : Option(int,
                description="HP of raid you are spawning",
                min_value = 1,
                required=False),
            print_info : Option(str,
                description="Print the raid info",
                choices = [OptionChoice("Print")],
                required=False)):
        """>:("""
        if spawn is not None:
            if self.raid_info["Active"]:
                return await ctx.respond("A raid is currently running", 
                    ephemeral=True)

            self.raid_info["Active"] = True
            self.raid_info["Enemy"] = random.choice(
                ["Maritimialan Raiders", "Teh Epik Duck", "Crumidian Invasion",
                "Riverburn Revolt", "Glakelyctic Brigands", "Pirates", "Seamus"]
            )
            self.raid_info["Max_HP"] = spawn
            self.raid_info["HP"] = spawn

            embed = discord.Embed(
                title=f"{self.raid_info['Enemy']} has appeared in Aramythia!",
                description=(
                    f"Only a coordinated assault from the strongest "
                    f"Aramythians will push them back. Use the `/raid attack` "
                    f"command to defend against it!\nEach participant will "
                    f"receive a cash prize when the boss is defeated, with the "
                    f"one who deals the final blow receiving a **legendary "
                    f"weapon!**"),
                color=Vars.ABLUE)

            self.raid_info["Message"]=await self.bot.announcement_channel.send(
                content=self.bot.raider_role.mention, embed=embed)

            await ctx.respond("Spawned", ephemeral=True)

        elif print_info is not None:

            await ctx.respond(
                content=f"{self.raid_info}\n\n{self.raid_participants}", 
                ephemeral=True)

        else:
            await ctx.respond("No")


def setup(bot):
    bot.add_cog(Raid(bot))