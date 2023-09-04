import discord
from discord import Webhook
from discord.ext import commands

from Utilities import  Checks, config, PlayerObject

import asyncio
import random
import time

import aiohttp
from aiohttp import web

#WEBSOCKET        
class Vote_Handler:
    def __init__(self, bot : discord.Client):
        self.bot = bot
        self.session = aiohttp.ClientSession()
        self.app: web.Application = None
        self.site: web.TCPSite = None

        async def webserver():
            self.app = web.Application(loop = self.bot.loop)
            self.app.router.add_post('/vote', self.post_handler)
            runner = web.AppRunner(self.app)
            await runner.setup()
            self.site = web.TCPSite(runner, '0.0.0.0', 8080)
            await self.bot.wait_until_ready()
            await self.site.start()

        asyncio.ensure_future(webserver())

        self.bot.vote_wbhook = Webhook.from_url(
            url=config.PWBHK, session=self.session)

    async def bot_list_stats(self):
        l = f"https://discordbotlist.com/api/v1/bots/{self.bot.user.id}/stats"
        t = f"https://top.gg/api/bots/{self.bot.user.id}/stats"
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            async with aiohttp.ClientSession() as client:
                async with self.bot.db.acquire() as conn:
                    await client.post(url=l,
                        data = {
                            "guilds" : len(self.bot.guilds),
                            "users" : await PlayerObject.get_player_count(conn)
                        },
                        headers = {"Authorization" : config.DBL_TOKEN}
                        )
                    await client.post(url=t,
                        data = {"server_count" : len(self.bot.guilds)},
                        headers = {"Authorization" : config.TOPGG_TOKEN})
                # print(resp.status)

            await asyncio.sleep(1800)

    async def post_handler(self, request: web.Request):
        auth = request.headers.get('Authorization')
        if f"dbl_{config.WBHKS}" != auth:
            return
        
        data = await request.json()
        self.bot.dispatch('vote', data)
        return web.Response(status=200) 

    async def on_shutdown(self):
        asyncio.ensure_future(self.site.stop())
        self.app.shutdown()
        self.app.cleanup()
        self.session.close()

class Vote(commands.Cog):
    """Small module to reward votes"""
    def __init__(self, client : commands.Bot):
        self.client = client

    #EVENTS
    @commands.Cog.listener() # needed to create event in cog
    async def on_ready(self): # YOU NEED SELF IN COGS
        vote_handling = Vote_Handler(self.client)
        self.update_stats = self.client.loop.create_task(vote_handling.bot_list_stats())
        print('Vote is ready.')

    @commands.Cog.listener()
    async def on_vote(self, data):
        user_id = int(data['user'])
        player = await self.client.fetch_user(user_id)

        async with self.client.db.acquire() as conn:
            try:
                # TODO: Change recent_voters to db table when playerbase is big
                self.client.recent_voters[user_id] = int(time.time() + 1800)
                p = await PlayerObject.get_player_by_id(conn, user_id)
                if random.randint(1, 150) == 1:
                    await p.give_rubidics(conn, 1)
                    r = True
                else:
                    r = False
                await p.give_gold(conn, 7500)
                await player.send(
                    "Thank you for supporting me! You received `7500` gold.\n"
                    f"{'You also received a rubidic!' if r else ''}"
                    "For the next 30 minutes, you will also receive a 20% gold "
                    "and xp boost from PvE.")
            except Checks.PlayerHasNoChar:
                await player.send((
                    "Thank you for voting for the bot! Create a character with "
                    "`/start` to receive rewards the next time you vote!"))

    def cog_unload(self):
        self.update_stats.cancel()

def setup(client):
    client.add_cog(Vote(client))