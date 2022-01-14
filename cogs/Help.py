import discord
from discord import Option, OptionChoice

from discord.commands.core import SlashCommand, SlashCommandGroup
from discord.ext import commands, pages

from typing import List

from Utilities import Vars, config

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

    @commands.slash_command(guild_ids=[762118688567984151])
    async def tutorial(self, ctx, topic : Option(str,
            description="What you want to read about",
            required=False,
            default="Quick-Start Guide",
            choices=[
                OptionChoice("Quick-Start Guide"),
                OptionChoice("Combat"),
                OptionChoice("Acolytes"),
                OptionChoice("Items"),
                OptionChoice("Travel")])):
        """Learn how to play!"""
        if topic == "Quick-Start Guide":
            page1 = (
                f"Welcome to Ayesha! Read the next few pages for a general "
                f"overview of how to play the game.\n\n"
                f"If you haven't already, use the `/start` command to create a "
                f"character. The `/profile` command displays more-or-less "
                f"everything important about yourself. Below is a quick "
                f"run-down of what each page means: "
                f"The 'Experience' tab shows your character's progress. Gain "
                f"EXP to level up. Next to this tab is your 'Wealth', divided "
                f"into three parts. **Gold** is the general currency of the "
                f"game, used for everything from buying items to selling them. "
                f"**Gravitas** is like a measure of reputation in the world. "
                f"Gravitas is not as important early game and will be covered "
                f"later. **Rubidics** are the gacha currency, and you will use "
                f"them to get rare acolytes and weapons!\n\n"
                f"The next command to use is `/lore`, which allows you "
                f"to set your occupation and origin. There are 10 occupations "
                f"and 9 origins, each giving you a specific bonus based on "
                f"how you want to play the game."
            )
            page2 = (
                f"The second page of your profile shows more combat-related "
                f"information. You have 4 stats, ATK, CRIT, HP, and DEF, "
                f"which are increased by things such as your level, equipped "
                f"weapons, armor, accessories and acolytes (you'll see soon!), "
                f"and your occupation and origin. You can see these equipped "
                f"items below in the 'Equips' section. Use `/inventory` to "
                f"see the list of weapons you own, and get the ID of the "
                f"your 'Wooden Spear' (a number like this: `50000`). Then "
                f"do `/equip`, select 'Equip a Weapon', select the id option, "
                f"and type your weapon's ID there. You have equipped your "
                f"first weapon! When you get armor and accessories in the "
                f"future, you can find your owned items with the `/armory` "
                f"and `/wardrobe` commands, then equip them in the same way "
                f"you equipped your weapon. "
            )
            page3 = (
                f"Finally you can get to the fun parts! You have 10 rubidics "
                f"right now, so use the `/summon` command to spend them. "
                f"For each summon, you will gain either a weapon or an acolyte."
                f"If you summoned multiple times at once, browse the dropdown "
                f"menu to see each of your summons. Then check your "
                f"`/inventory`, you likely got a better weapon and you should "
                f"equip it!\n\n"
                f"If you got an acolyte, the `/tavern` command will "
                f"list them out to you. Equipping an acolyte is just like "
                f"equipping a weapon: you take the ID (eg `215`), but this "
                f"time use the `/recruit` command. Since you can have 2 "
                f"acolytes in your party, you select 'Slot 1' or 'Slot 2', "
                f"then select the 'instance_id' and put your acolyte's ID "
                f" there.\n\n"
                f"You may have noticed that 'instance_id' (and 'id' in "
                f"`/inventory`) are optional. If you don't give an ID, that "
                f"will *unequip* whatever you already have equipped.\n\n"
            )
            page4 = (
                f"And now the **REAL** fun part! You have set up your "
                f"character to the best of your abilities so far, hopefully "
                f"have a ragtag team of acolytes and a sturdy weapon of your "
                f"own! The `/pve` command is the core of Ayesha gameplay, "
                f"the fastest way to gain gold and xp (and hence more "
                f"rubidics), and the source of armor and accessories.\n\n"
                f"I suggest you start off with `/pve` level 1 and progress "
                f"as you beat each level, although you can technically "
                f"shoot for level 25 right now (I dare you)! Once you beat "
                f"level 25, you can progress onwards ad infinitum. Each level "
                f"gets progressively harder, gives more gold and xp, and "
                f"weapons, armor, and accessories of greater rarity and "
                f"strength.\n\n"
                f"When you start, you'll notice 5 buttons:\n"
                f"🗡️: Attack - hit the enemy with all you've got!\n"
                f"\N{SHIELD}: Block - a worthy counter to an attack, but "
                f"will leave you vulnerable to...\n"
                f"\N{CROSSED SWORDS}: Parry - a defensive attack; you'll deal "
                f"less damage but also take less damage.\n"
                f"\u2764: Heal - Regain 20% of your max HP\n"
                f"\u23F1: Bide - Give yourself a 15% ATK boost\n\n"
                f"Against each enemy, you'll need to develop a strategy "
                f"using these five moves to counter their own strengths. "
                f"Have fun with Ayesha!"
            )
            page5 = (
                f"Thank you for reading this far! The final core part of the "
                f"bot is adventuring, the secondary source of gold and xp, but "
                f"an integral part of levelling up your weapons and acolytes "
                f"(if you've discovered that PvE is a slow way to level your "
                f"acolytes up). Note that on the first page of your profile "
                f"is the 'Location' setting, and you're most likely in "
                f"Aramithea, the capital city of Ayesha (use `/offices` "
                f"or `/territories` to view the cool, original map:TM: I made)."
                f" You may have also discovered the 'Backpack', or the third "
                f"page of `/profile` listing even more stuff you need to get. "
                f"If you have grown attached to one of your acolytes, you can "
                f"use the `/acolyte` command to get detailed information "
                f"about a specific acolyte, which will list the **resource** "
                f"they need to level up.\n\n"
                f"`/travel` is the command in question. You can choose to "
                f"travel to another location of the map, giving you a hint as "
                f"to what resource you can collect there. Travelling takes "
                f"some time, so once you select a place, set a reminder "
                f"for when to come back. Once done, you can use `/arrive` to "
                f"formally set your location to wherever you travelled to. "
                f"When not travelling, I suggest picking the 'Go on an "
                f"Expedition' option, which will net you a lot more resources, "
                f"gold, and xp over time (also end using `/arrive`).\n\n"
                f"At your location, use the `/work` command and select the "
                f"'Forage' option, and you will receive a bunch of resources "
                f"depending on where you are. Then use the `/train` command "
                f"to spend these resources (and gold) to give your acolyte "
                f"a flat 5000 xp."
            )
            page6 = (
                f"Thanks for reading this tutorial! I described a handful of "
                f"important commands to you, but Ayesha has over 50 commands "
                f"and so much more available for you to do! So get some "
                f"friends and learn the intricate secrets of the bot "
                f"together!\n\nFor some more in-depth details, you can read "
                f"the other tutorials, although they are by no means "
                f"necessary. They just expand on what is written here.\n\n"
                f"Need help with something? Check out the `/help` command!\n\n"
                f"Suggestions? Bugs? Want to meet more players? Join the "
                f"[support server]({config.SUPPORT_INVITE}).\n\n"
                f"Support us by voting on "
                f"[top.gg](https://top.gg/bot/767234703161294858)!"
            )

            messages = [
                ("Welcome to Ayesha!", page1),
                ("Combat Information", page2),
                ("Gacha and Acolytes", page3),
                ("The REAL Fun Part!", page4),
                ("Travel, Expeditions, Training", page5),
                ("Conclusion", page6)
            ]
            embeds = []
            for page in messages:
                embed = discord.Embed(
                    title=page[0],
                    description=page[1],
                    color=Vars.ABLUE)
                embed.set_thumbnail(url=self.bot.user.avatar.url)
                embeds.append(embed)

            paginator = pages.Paginator(pages=embeds, timeout=30)
            await paginator.respond(ctx.interaction)

        else:
            await ctx.respond("Oof")


def setup(bot):
    bot.add_cog(Help(bot))