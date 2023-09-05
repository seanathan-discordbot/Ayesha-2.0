import discord
from discord import Option, OptionChoice

from discord.commands.core import SlashCommand, SlashCommandGroup
from discord.ext import commands, pages

from typing import List

import aiofiles
import aiofiles.os
from pathlib import Path

from Utilities import Vars, config
from Utilities.AyeshaBot import Ayesha

class Help(commands.Cog):
    """Get help with the bot!"""

    def __init__(self, bot : Ayesha):
        self.bot = bot

    # EVENTS
    @commands.Cog.listener()
    async def on_ready(self):
        print("Help is ready.")

    # AUXILIARY FUNCTIONS
    def strf_cooldown(self, cooldown : commands.Cooldown) -> str:
        """Stringifies the cooldown to something accessible."""
        if cooldown is None:
            return None

        leftovers = cooldown.per # Repeatedly cut down each unit of time
        units = []
        if leftovers > 86400:
            units.append(f"{int(leftovers / 86400)} days")
            leftovers = leftovers % 86400
        if leftovers > 3600:
            units.append(f"{int(leftovers / 3600)} hours")
            leftovers = leftovers % 3600
        if leftovers > 60:
            units.append(f"{int(leftovers / 60)} minutes")
            leftovers = leftovers % 60
        if leftovers > 0:
            units.append(f"{leftovers} seconds")

        if cooldown.rate == 1:
            rate = f"1 use every "
        else:
            rate = f"{cooldown.rate} uses every "

        return rate + ", ".join(units)

    def strf_parameters(self, options : List[Option]) -> str:
        """Stringifies the command's parameters."""
        if len(options) == 0:
            return None

        params = []
        for param in options:
            fmt = f"`{param.name}` (*{param.input_type.name}*): "
            if not param.required:
                fmt += "[OPTIONAL] "
            fmt += param.description
            if param.min_value is not None and param.max_value is not None:
                fmt += f" ({param.min_value}-{param.max_value})"
            elif param.min_value is not None and param.max_value is None:
                fmt += f" ({param.min_value}-inf)"
            elif param.min_value is None and param.max_value is not None:
                fmt += f" (0-{param.max_value})"
            params.append(fmt)

        return "\n\n".join(params)

    def write_help_embed(self, command : discord.SlashCommand):
        """Returns an embed listing a command's information."""
        command_info = {
            "name" : command.qualified_name,
            "description" : command.description,
            "cooldown" : self.strf_cooldown(command.cooldown),
            "parameters" : self.strf_parameters(command.options)
        }

        embed = discord.Embed(
            title=command_info["name"],
            description=command_info["description"],
            color=Vars.ABLUE)
        if command_info["parameters"] is not None:
            embed.add_field(
                name="Arguments",
                value=command_info["parameters"])
        if command_info["cooldown"] is not None:
            embed.add_field(
                name="Cooldown",
                value=command_info["cooldown"],
                inline=False)
        embed.set_thumbnail(url=self.bot.user.avatar.url)

        return embed

    # COMMANDS
    @commands.slash_command()
    async def help(self, ctx,
            cmd_query : Option(str,
                name="command",
                description="A specific command you need help with",
                required=False),
            cog_query : Option(str,
                name="command_group",
                description="A specific set of commands you need help with",
                required=False,
                choices=[
                    OptionChoice("Profile"),
                    OptionChoice("Occupations"),
                    OptionChoice("Items"),
                    OptionChoice("Acolytes"),
                    OptionChoice("Travel"),
                    OptionChoice("Gacha"),
                    OptionChoice("Associations"),
                    OptionChoice("PvE"),
                    OptionChoice("PvP"),
                    OptionChoice("Raid"),
                    OptionChoice("Offices"),
                    OptionChoice("Misc")])):
        """Get help with the bot!"""
        if cmd_query is not None:
            command = None
            # command = self.bot.get_application_command(cmd_query.lower())
            # Use walk... instead to get commands in command groups
            for cmd in self.bot.walk_application_commands():
                if cmd_query == cmd.qualified_name:
                    command = cmd
            if command is None:
                return await ctx.respond(
                    f"No such command exists with the name `{cmd_query}`.")

            await ctx.respond(embed=self.write_help_embed(command))

        elif cog_query is not None:
            cog = self.bot.get_cog(cog_query)
            list_commands = []
            for command in cog.get_commands():
                if isinstance(command, SlashCommandGroup):
                    for cmd in command.subcommands:
                        list_commands.append(cmd)
                elif isinstance(command, SlashCommand):
                    list_commands.append(command)

            embeds = [self.write_help_embed(c) for c in list_commands]
            paginator = pages.Paginator(pages=embeds, timeout=30)
            await paginator.respond(ctx.interaction)

        else:
            command_list = [cmd.qualified_name 
                for cmd in self.bot.walk_application_commands() 
                if isinstance(cmd, SlashCommand)]
            command_fmt = " ".join([f"`{cmd}`" for cmd in command_list])

            embed1 = discord.Embed(
                title="Welcome to Ayesha Help!",
                description=(
                    f"Ayesha is an RPG adventure game bot for Discord "
                    f"designed to keep you occupied in boring voice chats. "
                    f"If you are just starting, please look at the `/tutorial`."
                    f"\n\n"
                    f"If you need help with a command, use this command again "
                    f"followed by the name of the command you need help with.\n"
                    f"Example: `/help start`"
                    f"\n\nIf you need help with something that the command "
                    f"descriptions can't tell you, you can always join the "
                    f"[support server here](https://discord.gg/FRTTARhN44) "
                    f"and ask one of our (very responsive!) developers.\n\n"),
                color=Vars.ABLUE)
            embed1.set_thumbnail(url=self.bot.user.avatar.url)

            embed2 = discord.Embed(
                title="Ayesha Command List",
                description=command_fmt,
                color=Vars.ABLUE)
            embed2.set_footer(text="'/help <command>' for command information!")
            embed2.set_thumbnail(url=self.bot.user.avatar.url)

            embeds = [embed1, embed2]
            paginator = pages.Paginator(pages=embeds, timeout=30)
            await paginator.respond(ctx.interaction)

    @commands.slash_command()
    async def tutorial(self, ctx: discord.ApplicationContext, 
            topic : Option(str,
                description="What you want to read about",
                required=False,
                default="Simple",
                choices=[
                    OptionChoice("Simple"),
                    OptionChoice("Quick-Start Guide"),
                    OptionChoice("Combat"),
                    OptionChoice("Gravitas")])
    ):
        """Learn how to play!"""
        if topic == "Simple":
            path = Path(__file__).parent.parent / "Tutorial/Simple.txt"
            async with aiofiles.open(path, mode='r') as f:
                text = await f.read()
            embed = discord.Embed(
                title="Simple Tutorial",
                description=text,
                color=Vars.ABLUE)
            embed.set_thumbnail(url=self.bot.user.avatar.url)
            return await ctx.respond(embed=embed)
        else:
            embeds = []
            path = path = Path(__file__).parent.parent
            match topic:
                case "Quick-Start Guide":
                    path /= "Tutorial/QuickStart"
                case "Combat":
                    path /= "Tutorial/Combat"

                    rarity_embed = discord.Embed(
                        title="PvE Loot Rarities and Materials",
                        color=Vars.ABLUE)
                    rarity_embed.add_field(
                        name="Weapon Rarity",
                        value=(
                            f"Common: 1-8\nUncommon: 9-14\nRare: 15-24\nEpic: 25-49\n"
                            f"Legendary: 50+"))
                    rarity_embed.add_field(
                        name="Armor Material",
                        value=(
                            f"Cloth: 1\nLeather: 2-4\nGambeson: 5-8\nBearskin: 9\n"
                            f"Wolfskin: 13\n Bronze: [10, 12]U[14]\nCeramic Plate: "
                            f"16-17\nChainmail: 18-20\nIron: 21-24\nSteel: 25-49\n"
                            f"Mysterious: 40+\nDragonscale: 50+"),
                        inline=False)
                    rarity_embed.add_field(
                        name="Armor Material",
                        value=(
                            f"Wood: 1\nGlass: 1-4\nCopper: 1-8\nJade: 2-9\nPearl: "
                            f"[6, 9]U[13]\nAquamarine: 13\nSapphire: 13-24\nAmethyst: "
                            f"15-20\nRuby:18-39\nGarnet: 21-49\nDiamond: 25-49\n"
                            f"Emerald: 40+\nBlack Opal: 50+"),
                        inline=False)
                    embeds.append(rarity_embed)

                case "Gravitas":
                    path /= "Tutorial/Gravitas"
                case DEFAULT:
                    return await ctx.respond("Oof")
                
            paths = await aiofiles.os.listdir(path)
            paths.sort()  # Files follow ordered naming convention
                
            additions = []
            for filepath in paths:
                async with aiofiles.open(path / filepath, mode='r') as f:
                    text = await f.read()
                title = filepath[3:-4]
                # [3:-4] as files are named [x]ACTUALTITLE.txt <- cut off extras
                # Obvious consequence is that we are limited to 10 pages

                embed = discord.Embed(
                    title=title,
                    description=text,
                    color=Vars.ABLUE
                )
                embed.set_thumbnail(url=self.bot.user.avatar.url)
                additions.append(embed)
            embeds = additions + embeds

            paginator = pages.Paginator(pages=embeds, timeout=30)
            await paginator.respond(ctx.interaction)


def setup(bot):
    bot.add_cog(Help(bot))