import discord
from discord.commands.errors import ApplicationCommandInvokeError
from discord.ext import commands

import sys
import time
import traceback

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

        # --- COMMAND ERRORS ---
        if isinstance(error, ApplicationCommandInvokeError):
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

            # --- OWNERSHIP ---
            if isinstance(error.original, Checks.NotWeaponOwner):
                message = f"You do not own a weapon with this ID."
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