import discord
from discord import Option, OptionChoice

from discord.commands.core import SlashCommand, SlashCommandGroup
from discord.ext import commands, pages

from typing import List

from Utilities import Vars

class Help(commands.Cog):
    """Get help with the bot!"""

    def __init__(self, bot : commands.Bot):
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
    @commands.slash_command(guild_ids=[762118688567984151])
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
            embed = discord.Embed(
                title="Welcome to Ayesha Help!",
                description=(
                    f"Ayesha is an RPG adventure game bot for Discord (and "
                    f"one of the earliest adopters of slash commands), "
                    f"designed to keep you occupied in boring voice chats. "
                    f"If you are just starting, please look at the `/tutorial`."
                    f" I know its long, but you don't have to read everything."
                    f"\n\n"
                    f"Ayesha has unfortunately been subject to many complaints "
                    f"that the gameplay is too complex, when it really isn't. "
                    f"If you need help with a command, use this command again "
                    f"followed by the name of the command you need help with."
                    f"\n\nIf you need help with something that the command "
                    f"descriptions can't tell you, you can always join the "
                    f"[support server here](https://discord.gg/FRTTARhN44) "
                    f"and ask one of our (very responsive!) developers.\n\n"
                    f"Thanks and have fun,\n"
                    f"Aramythia"),
                color=Vars.ABLUE)
            embed.set_thumbnail(url=self.bot.user.avatar.url)
            await ctx.respond(embed=embed)


def setup(bot):
    bot.add_cog(Help(bot))