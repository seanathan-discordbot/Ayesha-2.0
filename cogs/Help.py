import discord
from discord import Option, OptionChoice

from discord.commands.core import SlashCommand, SlashCommandGroup
from discord.ext import commands, pages

from typing import List

from Utilities import CombatObject, Vars, config
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

    @commands.slash_command()
    async def tutorial(self, ctx, topic : Option(str,
            description="What you want to read about",
            required=False,
            default="Quick-Start Guide",
            choices=[
                OptionChoice("Quick-Start Guide"),
                OptionChoice("Combat"),
                OptionChoice("Gravitas"),
                OptionChoice("Work")])):
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
                f"you equipped your weapon. You can get some types of armor "
                f"for gold by buying them in the `/shop`, but accessories "
                f"are attainable only through PvE."
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

        elif topic == "Combat":
            page1 = (
                f"Welcome to the Ayesha Combat Tutorial! In the next few "
                f"pages, I will be divulging into some technical information "
                f"about the combat system, so if you know nothing about combat "
                f"or the bot, I suggest you look at the `Quick-Start Guide` "
                f"instead.\n\n"
                f"__Some Quick History__\n"
                f"Ayesha was a fairly rushed bot written during the creators' "
                f"winter break of 2020-2021. Like most of the individual "
                f"modules, PvE was written in 2 days, but you are not playing "
                f"that version now ;). When 1.0 was released later that year, "
                f"Aramythia had written a more robust system that properly "
                f"integrated acolyte and boss effects, although it was still "
                f"largely a copy-paste job (and thus poorly integrated next to "
                f"PvP). A year later, the PvE was rewritten with the rest of "
                f"the bot into Ayesha 2.0. It is a vast improvement, running "
                f"on the same foundations as PvP and brotherhood attack, "
                f"although it was made by a random college student so y'know. "
                f"Anyway, what this means is that the real tutorial is really "
                f"in the "
                f"[code](https://github.com/seanathan-discordbot/Ayesha-2.0), "
                f"and its details will be found on the next page."
            )
            page2 = (
                f"If you look at the code, in `Utilities/CombatObject.py`, "
                f"under `ACTION_COMBOS`, you will find the dictionary that "
                f"determines how damage is calculated. It covers every "
                f"possible combination of attacks two players can perform. "
                f"The first dictionary is the agent's action (the attacker), "
                f"the second is the object's (the defender), meaning that "
                f"your damage is based not only what you do, but also what "
                f"your opponent does.\n\n"
                f"Let's say you attack, and your opponent blocks. You look "
                f"at the first dictionary for attack, then go to block, where "
                f"you find the number "
                f"`{CombatObject.ACTION_COMBOS['Attack']['Block']}`, or if "
                f"you can read Python, "
                f"`CombatObject.ACTION_COMBOS['Attack']['Block']`. "
                f"Your flat damage is a random number, somewhere around your "
                f"base ATK as found at the top of the PvE or PvP embed. "
                f"This damage amount is then multiplied by the amount given by "
                f"the dictionary. You attack, they block, you deal only "
                f"a small percentage of that initial damage. Your opponent's "
                f"damage is the converse, Block->Attack = "
                f"{CombatObject.ACTION_COMBOS['Block']['Attack']}, and their "
                f"own randomly calculated amount of damage is this amount.\n\n"
                f"Then, these damage numbers are changed depending on "
                f"your acolyte and accessory effects.\n\n"
                f"DEF is a percentage of damage reduction and is applied "
                f"to the calculated damage last.\n\n"
                f"When the turn is registered and damage is actually applied, "
                f"it occurs simultaneously from a gameplay perspective. "
                f"But there are no ties, so what happens? In PvE, you win. "
                f"In PvP, there are ties. In `/brotherhood attack`, "
                f"the defender wins."
            )
            page3 = (
                f"Another historical tidbit: before the days of slash "
                f"commands, menus, and buttons, bot devs were forced to using "
                f"reactions to get a player's input. But Discord limited "
                f"adding reactions to messages, and so the interactive PvE "
                f"of today was once a boring, automatic PvE, like PvP.\n\n"
                f"The fact above brings the question of how attacks are "
                f"determined. In the past, there existed a `%strategy` command "
                f"in which you set the proportion of each action. Now, bosses "
                f"and PvP still have to choose actions based off some "
                f"proportion. And here it is:\n"
                f"Attack: 50%\nBlock: 20%\nParry: 20%\nHeal: 3%\nBide: 7%\n\n"
                f"Each turn an action is randomly chosen based off these "
                f"weights, and you can note that in your PvE battle log, "
                f"you are even told what the boss will do on the next turn! "
                f"You may have also wisely deduced that the I, Ayesha, am also "
                f"a liar. You can find in `cogs/PvE.py`, the  "
                f"[calculation](https://github.com/seanathan-discordbot/Ayesha-2.0/blob/main/cogs/PvE.py) "
                f"that only 60% of the time I am telling the truth. In the "
                f"rest of the cases, I select another random action to "
                f"display, but since that random choice can also be the "
                f"correct once, the real probability is a little above 60%."
            )
            page4 = (
                f"Did you ever see one of the higher levelled players get "
                f"over 100,000 xp from beating a boss? Did you ever wonder why "
                f"you got 10,000 xp from beating a boss one time, but only "
                f"2,000 when you beat them a second time? The calculation for "
                f"xp is as follows:\n`f(x, y) = 2^(x/10) * (x+10)^2 * "
                f"((y + 750) + .02)`, where x = the level of the boss, and y = "
                f"the *HP you have remaining* upon victory. So the stronger "
                f"the boss, the more xp you gain on an *exponential* level, "
                f"and wider the margin you win by, the more xp you gain. "
                f"I beg you to appreciate the complex and equitable "
                f"reward calculation Ayesha has in comparison to other games "
                f"lol.\n\n"
                f"Gold calculation is rather unimaginative though, although "
                f"(history lesson!) it was based off the cosine function in "
                f"Ayesha 1.0.\n\n"
                f"Upon victory, you also have a flat...\n"
                f"10% chance to gain a weapon\n"
                f"6.67% (1/15) chance to get a piece of armor\n"
                f"5% chance to get an accessory\n"
                f"You can gain none, one, or multiple of these items on any "
                f"given victory. The [code](https://github.com/seanathan-discordbot/Ayesha-2.0/blob/main/cogs/PvE.py) "
                f"does not lie. The code is probably bugged, because for "
                f"some reason, I (Aramythia) never get any armor! >:( "
                f"The last few pages will give the exact rarities of "
                f"the drops you may potentially gain."
            )

            messages = [
                ("Combat Tutorial: Overview", page1),
                ("Damage Calculation", page2),
                ("Action Determination", page3),
                ("Rewards Chances", page4)
            ]
            embeds = []
            for page in messages:
                embed = discord.Embed(
                    title=page[0],
                    description=page[1],
                    color=Vars.ABLUE)
                embed.set_thumbnail(url=self.bot.user.avatar.url)
                embeds.append(embed)
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

            paginator = pages.Paginator(pages=embeds, timeout=30)
            await paginator.respond(ctx.interaction)

        elif topic == "Gravitas":
            page1 = (
                f"Something which was not expanded on in the initial tutorial "
                f"was the gravitas system. It is very simple and exists to "
                f"bring another dimension of gameplay beyond simply getting "
                f"physically stronger and/or wealthier. Gravitas, a Roman "
                f"ideal, is exactly what it sounds like: it is your weight "
                f"within the world. When you have more gravitas, people care "
                f"more for what you have to say. In that vein is the "
                f"officeholding feature. Every Wednesday at 12 p.m. EST, the "
                f"player with the most gravitas is elected the mayor of "
                f"Aramithea. The mayor has control over the taxation system, "
                f"and they have the power to set the tax rate to whatever they "
                f"please, influencing players' decisions to make sales or "
                f"purchases. You can view the current mayor using the "
                f"`/offices` command.\n\n"
                f"On the next page I will share how to attain gravitas."
            )
            page2 = (
                f"Gravitas is gained passively. Every day at 12 a.m. EST, "
                f"every player's gravitas is adjusted somewhat. Gravitas "
                f"decays over time. If your character resides in an outlying "
                f"area of the map (i.e. not in a city), this decay is "
                f"stronger than if they were in a city. Likewise the more "
                f"gravitas you have, the more will be lost every night. "
                f"The smallest change is a 10% loss for players residing "
                f"in a city with less than 500 gravitas (the largest actually "
                f"follows one of those complex formulae Ayesha is famous for: "
                f"`f(x) = x + 500 - (4x/5)`, where x is your current gravitas)."
                f" But just remember to stay in a city and you will be "
                f"golden.\n\n"
                f"The passive gain of gravitas follows.\nFarmers gain 4 "
                f"gravitas daily; soldiers and scribes gain 1; the rest none.\n"
                f"Aramithean born-and-raised also gain 5 gravitas, those from "
                f"Riverburn or Thenuille gain 3, and players from the Mythic "
                f"Forest, Lunaris, or Crumidia gain 1.\nMembers of a college "
                f"(the association type) gain 7.\nThe acolytes Ajar and "
                f"Duchess also give gravitas as their passive effects.\n\n"
                f"The expedition system (`/travel`) system also rewards those "
                f"who undertake a campaign throughout the cities to gain a "
                f"reputation. Those who go on long trips into the middle of "
                f"the jungle, however, may discover that they have been "
                f"forgotten about upon their return to civilization. Farmers, "
                f"fortunately, upon their return, will see that their gravitas "
                f"income is better than those of other occupations. They get "
                f"an addition 20% gravitas from urban expeditions, and their "
                f"decay is halved on wilderness ones."
            )
            page3 = (
                f"A tenure as mayor is the highest duty that a man of low-rank "
                f"(random adventurers in Aramythia) can hope to attain. "
                f"Once elected, they gain access to the `/tax` command, which "
                f"allows them to set the tax rate throughout the world. They "
                f"can also broadcast announcements to players via `/dictate`. "
                f"At the end of the week, they gain 3% of the tax collected "
                f"over their mayorship. This may motivate them to set the tax "
                f"high, but they may also keep it low to keep the favor of "
                f"their peers. \n\n"
                f"Fortunately, the people can cast away the tyranny of high "
                f"taxes by using the `/influence` command. There they can "
                f"spend their gravitas to praise or insult another player. "
                f"The mayor who sets their tax rate to 10% may be a target "
                f"of mass insult, tanking their gravitas, and he who promises "
                f"to lower it may be praised by others, receiving a boost to "
                f"their own reputation. The attacks of one person have the "
                f"possibility to fall flat on their face, but in aggregate, "
                f"the population wields tremendous power over the reputation "
                f"of the few.\n\n"
                f"Thank you for reading! The gravitas system may not be as "
                f"fleshed out or focused on as other parts of the game, but "
                f"we are always open to suggestions on expanding it and making "
                f"it a more integral part of gameplay."
            )

            messages = [
                ("Gravitas Overview", page1),
                ("How to Become Famous", page2),
                ("The Officeholder System", page3)
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

        elif topic == "Work":
            page1 = (
                f"`/work` is meant to be a faster way to gain gold and "
                f"resources essential for upgrading weapons and acolytes. Once "
                f"invoked, you have 5 options as to how what type of work "
                f"you wish to do. In the past, these options were actually "
                f"separate commands, but they have been condensed to comply "
                f"with Discord's command limits.\n\n"
                f"Why this one command merits its own tutorial is because "
                f"you can get bonuses on your yields from this command "
                f"from two sources: having a weapon of a certain weapontype "
                f"equipped, and being in a brotherhood that controls the "
                f"location that you are working in. The brotherhood bonus "
                f"is a flat 50% and applies to hunting, mining, and foraging. "
                f"Each work type and the weapons which buff your profits are "
                f"listed on the following pages:"
            )
            page2 = (
                f"**Smalltown Gig** started out as the original `%work` "
                f"command, and is available everywhere. It gives you between "
                f"80 and 800 gold.\n\n"
                f"**Hunting Trip**, once the `%hunt` command is only possible "
                f"in regions which are grasslands, forests, and taigas. On "
                f"average, the yield is about 55 fur and 40 bone.\nEquip a "
                f"bow to double this amount, a sling to increase it by 50%, or "
                f"a javelin for a 25% boost. Gauntlets, however, make for a "
                f"poor hunter's item, and will halve your yield. Hunters also "
                f"gain a 100% bonus.\n\n"
                f"**Mining Shift**, once `%mine` is pretty much only "
                f"worth-while in the badlands of Crumidia. There you will get "
                f"hundreds of pieces of iron, and some silver, too. A "
                f"trebuchet really packs a punch to collecting ore, with a "
                f"100% yield increase. Greatswords, axes, and maces also give "
                f"a 25% boost. But don't try to mine with a dagger, bow, or "
                f"sling :/. Blacksmiths also get double yields."
            )
            page3 = (
                f"**Foraging Party**: Forage for the others types of "
                f"resources listed in your pack (3rd page of `/profile`). "
                f"Amounts vary, because getting oat in a grassland is easier "
                f"than finding cacao in the jungle. Daggers, however, are your "
                f"tools of choice, giving you a 10% bonus. Travelers (or are "
                f"they travellers?) get double the amount as well.\n\n"
                f"**Fishing Getaway**: Find a nice small pond and relax with "
                f"your fishing rod, or undertake a commercial fishing trip "
                f"in Thenuille (that means fish in Thenuille if you want more "
                f"money). An alternate way to get gold."
            )

            messages = [
                ("Working", page1),
                ("Working", page2),
                ("Working", page3)
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