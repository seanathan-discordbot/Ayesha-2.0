import discord
from discord.commands.context import ApplicationContext
from discord.commands.errors import ApplicationCommandInvokeError
from discord.ext import commands

import sys
import time
import traceback
from discord.ext.commands.errors import CommandOnCooldown

from discord.ui.item import Item

from Utilities import Checks

class Error_Handler(commands.Cog):
    """Bot error handler."""

    def __init__(self, bot):
        self.bot = bot

    # EVENTS
    @commands.Cog.listener()
    async def on_ready(self):
        print("Error Handling activated.")

    # --- ERROR HANDLER ---
    @commands.Cog.listener()
    async def on_application_command_error(self, ctx, error):
        """The error handler for the bot.
        
        Apparently any errors raised during the actual command body will
        result in an ApplicationCommandInvokeError, hence the nested-if.
        Check failures can go straight into the handler body much like the
        Ayesha-1.0 error handler.
        """
        print_traceback = True

        # --- CHARACTER RELATED ---
        if isinstance(error, Checks.HasChar):
            message = (f"You already have a character.\nFor help, read the "
                       f"`/tutorial` or go to the `/support` server.")
            await ctx.respond(message)
            print_traceback = False

        if isinstance(error, Checks.PlayerHasNoChar):
            message = ("This player does not have a character. "
                        "Use the `/start` command to make one :)")
            await ctx.respond(message)
            print_traceback = False

        if isinstance(error, Checks.CurrentlyTraveling):
            if error.dest == "EXPEDITION":
                diff = int(time.time() - error.adv)
                days = int(diff / 86400)
                days = f"0{days}" if days < 10 else str(days)
                less_than_day = diff % 86400
                duration = time.strftime("%H:%M:%S", time.gmtime(less_than_day))
                message = (
                    f"You are currently on an expedition. You have been on "
                    f"this expedition for `{days}:{duration}`. To return "
                    f"from your expedition, use the `/arrive` command.")
            else:
                message = (f"You are currently traveling to {error.dest}.")
            await ctx.respond(message)
            print_traceback = False

        if isinstance(error, Checks.NotCurrentlyTraveling):
            message = ("You are not travelling at the moment. "
                        "Begin one with `/travel`!")
            await ctx.respond(message)
            print_traceback = False

        # --- CONCURRENCY ERROR ---
        if isinstance(error, commands.MaxConcurrencyReached):
            await ctx.respond(
                "You can only have 1 instance of this command running at once.")
            print_traceback = False

        if isinstance(error, CommandOnCooldown):
            if error.retry_after >= 3600:
                cd_length = time.strftime(
                    "%H:%M:%S", time.gmtime(error.retry_after))
            else:
                cd_length = time.strftime(
                    "%M:%S", time.gmtime(error.retry_after))
            message = (f"You are on cooldown for `{cd_length}`.")
            await ctx.respond(message)
            print_traceback = False

        # --- COMMAND ERRORS ---
        if isinstance(error, ApplicationCommandInvokeError):
            # --- COOLDOWN ERRORS ---
            if isinstance(error.original, CommandOnCooldown):
                if error.original.retry_after >= 3600:
                    cd_length = time.strftime(
                        "%H:%M:%S", time.gmtime(error.original.retry_after))
                else:
                    cd_length = time.strftime(
                        "%M:%S", time.gmtime(error.original.retry_after))
                message = (f"You are on cooldown for `{cd_length}`.")
                await ctx.respond(message)
                print_traceback = False
            else: # Reset the cooldown on other errors
                ctx.command.reset_cooldown(ctx)

            # --- ARGUMENT ERRORS ---
            if isinstance(error.original, Checks.PlayerHasNoChar):
                message = ("This player does not have a character. "
                           "Use the `/start` command to make one :)")
                await ctx.respond(message)
                print_traceback = False

            if isinstance(error.original, Checks.ExcessiveCharacterCount):
                message = (f"Your response exceeded the character limit.\n"
                            f"Please keep your response under `"
                            f"{error.original.limit}` characters.")
                await ctx.respond(message)
                print_traceback = False

            if isinstance(error.original, Checks.NotEnoughResources):
                message = (
                    f"You do not have enough **{error.original.resource}** to "
                    f"complete this transaction. You need "
                    f"`{error.original.diff}` more "
                    f"**{error.original.resource}** to do so."
                )
                await ctx.respond(message)
                print_traceback = False

            if isinstance(error.original, Checks.NotEnoughGold):
                message = (
                    f"You do not have enough gold to complete "
                    f"this transaction. You need `{error.original.diff}` "
                    f"more gold to do so."
                )
                await ctx.respond(message)
                print_traceback = False

            if isinstance(error.original, Checks.InvalidResource):
                await ctx.respond("Ping Aramythia for this error lol")
                print(f"Resource {error.original.resource} DNE.")

            if isinstance(error.original, Checks.NameTaken):
                message = f"Name {error.original.name} is already in use."
                await ctx.respond(message)
                print_traceback = False

            # --- OWNERSHIP ---
            if isinstance(error.original, Checks.NotWeaponOwner):
                message = f"You do not own a weapon with this ID."
                await ctx.respond(message)
                print_traceback = False

            if isinstance(error.original, Checks.NotArmorOwner):
                message = f"You do not own the armor with this ID."
                await ctx.respond(message)
                print_traceback = False

            if isinstance(error.original, Checks.NotAdmin):
                message = f"This command is reserved for admins."
                await ctx.respond(message, ephemeral=True)
                print_traceback = False

            # --- ASSOCIATIONS ---
            if isinstance(error.original, Checks.NotInAssociation):
                if error.original.req is None:
                    message = (
                        "You need to be in an association to use this "
                        "command!\n Ask for an invitation to one or found your "
                        "own with `/association create`!")
                else:
                    message = (
                        f"You need to be in a {error.original.req} to use this "
                        f"command!\n Ask for an invitation to one or found "
                        f"your own with `/association create`!")
                await ctx.respond(message)
                print_traceback = False

            if isinstance(error.original, Checks.InAssociation):
                message = "You are already in an association!"
                await ctx.respond(message)
                print_traceback = False

            if isinstance(error.original, Checks.IncorrectAssociationRank):
                message = (
                    f"You need to be an Association {error.original.rank} "
                    f"to use this command.")
                await ctx.respond(message)
                print_traceback = False

            if isinstance(error.original, Checks.PlayerAlreadyChampion):
                message = (
                    f"The player you have specified is already oen of your "
                    f"brotherhood's champions.")
                await ctx.respond(message)
                print_traceback = False

            if isinstance(
                    error.original, Checks.PlayerNotInSpecifiedAssociation):
                message = (
                    f"This player is not in your {error.original.type}.")
                await ctx.respond(message)
                print_traceback = False

        # --- OFFICES ---
        if isinstance(error, Checks.NotMayor):
            message = (
                "This command is reserved to the mayor only. Join a "
                "college and get a lot of gravitas to become elected one.")
            await ctx.respond(message)
            print_traceback = False

        if isinstance(error, Checks.NotComptroller):
            message = (
                "This command is reserved to the comptroller only. Join a "
                "guild and become the richest player to become one.")
            await ctx.respond(message)
            print_traceback = False

        # --- ARGUMENT ERRORS ---
        if isinstance(error, Checks.ExcessiveCharacterCount):
            message = (f"Your response exceeded the character limit.\nPlease "
                       f"keep your response under `{error.limit}` characters.")
            await ctx.respond(message)
            print_traceback = False

        if print_traceback:
            traceback.print_exception(
                error.__class__, error, error.__traceback__, file=sys.stderr)

def setup(bot):
    bot.add_cog(Error_Handler(bot))