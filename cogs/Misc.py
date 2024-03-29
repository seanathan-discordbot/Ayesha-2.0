import discord
from discord import Option, OptionChoice

from discord.ext import commands, pages
from discord.ext.commands import BucketType, cooldown

import asyncio
import random
import schedule
import time

from Utilities import Analytics, Checks, PlayerObject, Vars
from Utilities.AyeshaBot import Ayesha

class LeaderboardMenu(discord.ui.Select):
    def __init__(self, author : PlayerObject.Player, embeds : dict):
        self.author = author
        self.embeds = embeds
        # Exclude last entry; its the empty occupation (Name = None)
        options = [
            discord.SelectOption(label="Bot Information", value="Info"),
            discord.SelectOption(label="Most Experienced Players", 
                value="Experience"),
            discord.SelectOption(label="Wealthiest Players", value="Gold"),
            discord.SelectOption(label="Most Bosses Defeated", value="PvE"),
            discord.SelectOption(label="Most PvP Wins", value="PvP"),
            discord.SelectOption(label="Most Influential Players", 
                value="Gravitas")
        ]
        super().__init__(placeholder="View Leaderboards", options=options)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.edit_message(
            embed=self.embeds[self.values[0]])

    async def interaction_check(self, 
            interaction : discord.Interaction) -> bool:
        return interaction.user.id == self.author.disc_id

class Misc(commands.Cog):
    """General, non-cog-related commands"""

    def __init__(self, bot : Ayesha):
        self.bot = bot

    # EVENTS
    @commands.Cog.listener()
    async def on_ready(self):
        print("Misc is ready.")

    # AUXILIARY FUNCTIONS
    def format_leaderboard(self, lb, author_name : str, author_rank : int, 
            author_val : int) -> str:
        """Returns a formatted block of text showing the leaderboard.
        lb must be an asyncpg.Record or list. 
        The first column must be the names of the people on the leaderboard.
        The second column must be the value being ranked.
        """
        # Make all the names equal width
        names = [record[0] for record in lb]
        names.append(author_name)
        name_length = len(max(names, key=len))
        names = [name + " "*(name_length - len(name)) for name in names]

        ranks = []
        for i, record in enumerate(lb):
            if i+1 < 10: # Make all ranks equal width
                j = "0"+str(i+1)
            else:
                j = "10"
            ranks.append(f"{j} | {names[i]} | {record[1]}")
            
        if author_rank < 10:
            author_rank = "0" + str(author_rank)

        return "```" + "\n".join(ranks) + (
            f"\n{'-'*len(max(ranks, key=len))}\n"
            f"{author_rank} | {names[-1]} | {author_val}```")

    def calc_daily_rewards(self, player : PlayerObject.Player):
        # Separate possible rewards into different tiers
        if player.daily_streak < 3:
            tier = 5
        elif player.daily_streak < 7:
            tier = 4
        elif player.daily_streak < 14:
            tier = 3
        elif player.daily_streak < 30:
            tier = 2
        else:
            tier = 1

        # Calculate tier rewards
        match tier:
            case 5:
                gold = player.daily_streak * 80
                iron = 0
                gravitas = 0
                rubidics = 0
            case 4:
                gold = player.daily_streak * 100
                iron = player.daily_streak * 40
                gravitas = 0
                rubidics = 0
            case 3:
                gold = player.daily_streak * 130
                iron = player.daily_streak * 45
                gravitas = 1
                rubidics = 0
            case 2:
                gold = player.daily_streak * 150
                iron = player.daily_streak * 55
                gravitas = 3
                rubidics = 0
            case 1:
                gold = player.daily_streak * 180
                iron = player.daily_streak * 70
                gravitas = 5
                rubidics = 1 if random.randint(1, 100) == 1 else 0
        rubidics = 1 if player.daily_streak % 30 == 0 else rubidics

        return { 
            "Tier" : tier,
            "Gold" : gold,
            "Iron" : iron,
            "Gravitas" : gravitas,
            "Rubidics" : rubidics
        }


    # COMMANDS
    @commands.slash_command()
    @commands.check(Checks.is_player)
    async def daily(self, ctx : discord.ApplicationContext):
        """Get a daily bonus! Resets everyday at 12 a.m. GMT."""
        refresh_str = lambda x : f"You can claim your daily again in `{x}`."

        async with self.bot.db.acquire() as conn:
            player = await PlayerObject.get_player_by_id(conn, ctx.author.id)

            try:
                refresh_time = await player.collect_daily(conn)
            except Checks.AlreadyClaimedDaily as e:
                title = "You already claimed your daily today."
                e_message = ""
                refresh_msg = refresh_str(e.time_to_midnight)
            else:
                title = "You claimed your daily bonus!"
                refresh_msg = refresh_str(refresh_time)

                # Calculate and distribute rewards
                rewards = self.calc_daily_rewards(player)
                gold_bonus, iron_bonus, gravitas_bonus = [], [], []
                e_message = "From your bonus, you received:\n"

                if player.assc.type == "Guild":
                    bonus = player.assc.get_level() * 30
                    rewards["Gold"] += bonus
                    gold_bonus.append((bonus, "Guild")) 
                await player.give_gold(conn, rewards["Gold"])
                e_message += Analytics.stringify_gains("gold", 
                        rewards["Gold"], gold_bonus) + "\n"

                if rewards["Iron"] > 0:
                    if player.assc.type == "Brotherhood":
                        bonus = player.assc.get_level() * 20
                        rewards["Iron"] += bonus
                        iron_bonus.append((bonus, "Brotherhood"))
                    await player.give_resource(conn, "iron", rewards["Iron"])
                    e_message += Analytics.stringify_gains("iron", 
                            rewards["Iron"], iron_bonus) + "\n"

                if rewards["Gravitas"] > 0:
                    if player.assc.type == "College":
                        bonus = int(player.assc.get_level() / 2)
                        rewards["Gravitas"] += bonus
                        gravitas_bonus.append((bonus, "College"))
                    await player.give_gravitas(conn, rewards["Gravitas"])
                    e_message += Analytics.stringify_gains("gravitas", 
                            rewards["Gravitas"], gravitas_bonus) + "\n"
                
                if rewards["Rubidics"] > 0:
                    e_message += Analytics.stringify_gains("rubidic",
                        rewards["Rubidics"], [])
                    await player.give_rubidics(conn, rewards["Rubidics"])

        # Create and send embed
        embed = discord.Embed(title=title, description=e_message, 
            color=Vars.ABLUE)
        embed.add_field(
            name=refresh_msg,
            value=(
                f"You have claimed your `/daily` for `{player.daily_streak}` "
                f"{'days' if player.daily_streak > 1 else 'day'} in a row. "
                "Maintain a longer streak to receive even larger rewards in "
                "the future!"),
            inline=False)
        embed.add_field(
            name="Vote for the bot on top.gg to receive a short boost!",
            value=(
                "[**CLICK HERE**](https://top.gg/bot/767234703161294858/vote) "
                "to vote for the bot for EXTRA REWARDS!\n\n"
                "Any questions? Join the "
                "[**support server**](https://discord.gg/FRTTARhN44)!"),
            inline=False)
        embed.set_thumbnail(url="https://i.imgur.com/LPxc3zI.jpeg")

        await ctx.respond(embed=embed)

    @commands.slash_command()
    @commands.check(Checks.is_player)
    async def cooldowns(self, ctx : discord.ApplicationContext):
        """View any of your active cooldowns."""
        # Iterate through commands to get cooldowns
        cooldowns = [] # Player's list of cooldowns
        counter = 0 # Get amount of commands in bot
        for command in self.bot.walk_application_commands():
            if isinstance(command, discord.SlashCommandGroup):
                continue

            if command.parent is not None:
                name = f"/{command.parent.name} {command.name}"
            else:
                name = "/" + command.name

            if command.is_on_cooldown(ctx):
                seconds = time.gmtime(command.get_cooldown_retry_after(ctx))
                if command.get_cooldown_retry_after(ctx) >= 3600: 
                    cd = f"`{name}`: {time.strftime('%H:%M:%S', seconds)}"
                else:
                    cd = f"`{name}`: {time.strftime('%M:%S', seconds)}"
                cooldowns.append(cd)

            counter += 1

        async with self.bot.db.acquire() as conn:
            player = await PlayerObject.get_player_by_id(conn, ctx.author.id)

        # Get player's adventure status
        if player.destination == "EXPEDITION":
            elapsed = int(time.time() - player.adventure)
            subday = elapsed % 86400
            subday_str = time.strftime("%H:%M:%S", time.gmtime(subday))
            days = str(int(elapsed / 86400))
            days = "0"+days if len(days) == 1 else days
            adv_status = (
                f"You have been on an expedition for `{days}:{subday_str}`."
            )
        elif player.adventure is None:
            adv_status = "You are not currently on an adventure."
        elif player.adventure > int(time.time()): # TRAVEL not done
            time_left = player.adventure - int(time.time())
            str_time = time.strftime('%H:%M:%S', time.gmtime(time_left))
            adv_status = (
                f"You will arrive at **{player.destination}** in "
                f"`{str_time}`.")
        else:
            adv_status = (
                f"Your adventure is completed and you can safely `/arrive` "
                f"at **{player.destination}**.")

        # Check if player has claimed daily today
        if not player.eligible_to_claim_daily():
            to_reset = PlayerObject.Player.get_time_to_midnight()
            daily = f"You can claim your daily again in `{to_reset}`."
        else:
            daily = (
                "You can claim your daily rewards with the `/daily` command.")

        # Create an embed
        embed = discord.Embed(
            title=f"{ctx.author.display_name}'s Cooldowns",
            description="\n".join(cooldowns),
            color=Vars.ABLUE)
        embed.set_thumbnail(url=ctx.author.display_avatar.url)
        embed.add_field(
            name="Adventure Status",
            value=adv_status)
        embed.add_field(
            name="Daily Status",
            value=daily,
            inline=False)
        embed.set_footer(text=f"Ayesha has {counter} commands!")

        await ctx.respond(embed=embed)

    @commands.slash_command()
    @commands.check(Checks.is_player)
    async def leaderboard(self, ctx):
        """See the leaderboards and other cool information."""
        async with self.bot.db.acquire() as conn:
            author = await PlayerObject.get_player_by_id(conn, ctx.author.id)
            # Meta information
            servers = len(ctx.bot.guilds)
            players = await PlayerObject.get_player_count(conn)
            econ_info = await Analytics.get_econ_info(conn)
            acolyte_info = await Analytics.get_acolyte_info(conn)
            combat_info = await Analytics.get_combat_info(conn)
            # Top xp
            top_xp = await Analytics.get_top_xp(conn)
            player_xp = await Analytics.get_xp_rank(conn, ctx.author.id)
            # Top Gold
            top_gold = await Analytics.get_top_gold(conn)
            player_gold = await Analytics.get_gold_rank(conn, ctx.author.id)
            # Top PvE
            top_pve = await Analytics.get_top_pve(conn)
            player_pve = await Analytics.get_bosswins_rank(conn, ctx.author.id)
            # Top PvP
            top_pvp = await Analytics.get_top_pvp(conn)
            player_pvp = await Analytics.get_pvpwins_rank(conn, ctx.author.id)
            # Top Gravitas
            top_grav = await Analytics.get_top_gravitas(conn)
            player_grav = await Analytics.get_gravitas_rank(conn, ctx.author.id)

        # Meta Embed
        information = discord.Embed(
            title="Ayesha Bot Information",
            color=Vars.ABLUE)
        information.add_field(
            name="Meta Stats",
            value=(
                f"**Servers:** {servers}\n"
                f"**Players:** {players}"))
        information.add_field(
            name="Economy Stats",
            value=(
                f"**Gold:** {econ_info['g']}\n"
                f"**Rubidics:** {econ_info['r']}\n"))
        information.add_field(
            name="Gameplay Stats",
            value=(
                f"**Bosses Defeated:** {combat_info['b']}\n"
                f"**PvP Fights:** {combat_info['p']}"),
            inline=False)
        information.add_field(
            name="Most Used Acolytes",
            value=(
                f"```1 | {acolyte_info[0]['acolyte_name']}: "
                f"{acolyte_info[0]['c']}\n"
                f"2 | {acolyte_info[1]['acolyte_name']}: "
                f"{acolyte_info[1]['c']}\n"
                f"3 | {acolyte_info[2]['acolyte_name']}: "
                f"{acolyte_info[2]['c']}```"),
            inline=False)
        information.set_thumbnail(url=self.bot.user.avatar.url)

        # EXP Rank Embed
        lb_text = self.format_leaderboard(
            top_xp, author.char_name, player_xp, author.xp)
        xp_lb = discord.Embed(
            title="Ayesha Leaderboards: Experience",
            description=lb_text,
            color=Vars.ABLUE)
        xp_lb.set_thumbnail(url=self.bot.user.avatar.url)

        # Gold Rank Embed
        gold_text = self.format_leaderboard(
            top_gold, author.char_name, player_gold, author.gold)
        gold_lb = discord.Embed(
            title="Ayesha Leaderboards: Gold",
            description=gold_text,
            color=Vars.ABLUE)
        gold_lb.set_thumbnail(url=self.bot.user.avatar.url)

        # PvE Rank Embed
        pve_text = self.format_leaderboard(
            top_pve, author.char_name, player_pve, author.boss_wins)
        pve_lb = discord.Embed(
            title="Ayesha Leaderboards: Bosses Defeated",
            description=pve_text,
            color=Vars.ABLUE)
        pve_lb.set_thumbnail(url=self.bot.user.avatar.url)

        # PvP Rank Embed
        pvp_text = self.format_leaderboard(
            top_pvp, author.char_name, player_pvp, author.pvp_wins)
        pvp_lb = discord.Embed(
            title="Ayesha Leaderboards: PvP Wins",
            description=pvp_text,
            color=Vars.ABLUE)
        pvp_lb.set_thumbnail(url=self.bot.user.avatar.url)

        # Gravitas Rank Embed
        grav_text = self.format_leaderboard(
            top_grav, author.char_name, player_grav, author.gravitas)
        grav_lb = discord.Embed(
            title="Ayesha Leaderboards: Gravitas",
            description=grav_text,
            color=Vars.ABLUE)
        grav_lb.set_thumbnail(url=self.bot.user.avatar.url)

        embeds = {
            "Info" : information,
            "Experience" : xp_lb,
            "Gold" : gold_lb,
            "PvE" : pve_lb,
            "PvP" : pvp_lb,
            "Gravitas" : grav_lb
        }
        view = discord.ui.View(timeout=30.0)
        view.add_item(LeaderboardMenu(author, embeds))
        await ctx.respond(embed=information, view=view)

    @commands.slash_command()
    @commands.check(Checks.is_player)
    @cooldown(1, 21600, BucketType.user)
    async def influence(self, ctx,
            action : Option(str,
                description="Praise or insult another player",
                choices=[
                    OptionChoice(name="Praise a Friend", value="Praise"),
                    OptionChoice(name="Insult an Enemy", value="Insult")]),
            target : Option(discord.Member,
                description="The person you want to influence",
                converter=commands.MemberConverter()),
            gravitas : Option(int,
                description="The amount of gravitas you are sacrificing",
                min_value=20,
                max_value=1000)):
        """Praise or insult another player to affect their gravitas."""
        async with self.bot.db.acquire() as conn:
            agent = await PlayerObject.get_player_by_id(conn, ctx.author.id)
            if agent.gravitas < gravitas:
                raise Checks.NotEnoughResources(
                    "gravitas", gravitas, agent.gravitas)

            object = await PlayerObject.get_player_by_id(conn, target.id)
            if agent.disc_id == object.disc_id:
                return await ctx.respond("Don't do that.")
            success = random.randint(1, 10)

            if action == "Praise":
                # Gravitas spending should have about 80% efficiency on average
                if success <= 6: # Regular success (60-80% efficiency)
                    gain = int(gravitas * (random.randint(60, 80) / 100))
                    message = (
                        f"Your attempts to assist {target.mention} went well "
                        f"and they gained `{gain}` gravitas.")
                elif success <= 8: # Major success (90-120% efficiency)
                    gain = int(gravitas * (random.randint(90, 120) / 100))
                    message = (
                        f"Everyone stopped to here your praise for "
                        f"{target.mention}, and they gained `{gain}` gravitas. "
                        f"They owe you one now.")
                elif success == 9: # Failure (20-50% efficiency)
                    gain = int(gravitas * (random.randint(20, 50) / 100))
                    message = (
                        f"Few people turned their heads to what you had to "
                        f"say about {target.mention}. They gained `{gain}` "
                        f"gravitas.")
                else: # Critical Failure (-10-20% efficiency)
                    gain = int(gravitas * (random.randint(10, 20) / 100) * -1)
                    message = (
                        f"Anyone who had you as their public speaking "
                        f"instructor is probably in jail now, as your praise "
                        f"actually resulted in {target.mention} *losing* "
                        f"`{gain*-1}` gravitas. Yikes.")
                await object.give_gravitas(conn, gain)

            else:
                if success <= 6: # Regular success (50-65% efficiency)
                    loss = int(gravitas * (random.randint(50, 65) / 100))
                    message = (
                        f"When you spoke to the crowd at the detriment of "
                        f"{target.mention}, they began to murmur in "
                        f"agreement. {target.mention} has lost `{loss}` "
                        f"gravitas.")
                elif success <= 8: # Critical success (75-90% efficiency)
                    loss = int(gravitas * (random.randint(75, 90) / 100))
                    message = (
                        f"You shared your hate for {target.mention} and "
                        f"everyone agreed. They lost `{loss}` gravitas.")
                elif success == 9: # Failure (25-40% efficiency)
                    loss = int(gravitas * (random.randint(25, 40) / 100))
                    message = (
                        f"No one cares about your negativity, and no one cares "
                        f"about what you think about {target.mention}. They "
                        f"lost `{loss}` gravitas.")
                else: # Critical Failure (-10-20% efficiency)
                    loss = int(gravitas * (random.randint(10, 20) / 100) * -1)
                    message = (
                        f"You are so unpopular that insulting {target.mention} "
                        f"netted them {loss*-1} gravitas. Nice going.")
                await object.give_gravitas(conn, loss * -1)

            await agent.give_gravitas(conn, gravitas * -1)
            await ctx.respond(message)

    @commands.slash_command()
    @commands.check(Checks.is_player)
    @cooldown(1, 7200, BucketType.user)
    async def crime(self, ctx):
        """We do a little trolling. Organize a heist."""
        result = random.choices(
            ["critical success", "success", "failure"], 
            [5, 55, 40])[0]
        if result == "critical success":
            gain = random.randint(5, 8) / 100
        elif result == "success":
            gain = random.randint(2, 4) / 100
        else:
            gain = random.randint(10, 15) / 100 * -1

        place = random.choice(
            ("bank", "guild", "blacksmith", "quarry", "farmer", "merchant", 
            "store", "passerby", "prison", "foreign trader", "church"))

        async with self.bot.db.acquire() as conn:
            player = await PlayerObject.get_player_by_id(conn, ctx.author.id)
            gold_delta = int(player.gold * gain) + 1
            await player.give_gold(conn, gold_delta)

        if result == "failure":
            await ctx.respond(
                f"Your heist at {place} was a {result}! You were fined "
                f"`{gold_delta*-1}` gold.")
        else:
            await ctx.respond(
                f"Your heist at {place} was a {result}! You ran off with "
                f"`{gold_delta}` gold.")


def setup(bot):
    bot.add_cog(Misc(bot))