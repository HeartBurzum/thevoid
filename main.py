from typing import Any, Optional

import asyncio
import logging
import sys
import traceback
import weakref

from datetime import datetime, timedelta
from uuid import uuid4

import discord
from discord import app_commands

from embed import Embed
from messages.models import Users, Messages, db


logger = logging.getLogger('discord')
logger.name = "discord.main"
logger.setLevel(logging.INFO)

class Client(discord.Client):
    _instances = set()

    def __init__(self, **options) -> None:
        self.__bot_config: dict[str, Any] = options["config"]
        super().__init__(**options)

        self.message_queue: list[dict[str, Users|Messages|discord.Message]] = list()
        self._current_loop: Optional[asyncio.AbstractEventLoop] = None
        self._runner: Optional[asyncio.Task] = None
        self.server: Optional[discord.Guild] = None
        self.channel: Optional[discord.abc.GuildChannel] = None
        self.db = db
        self.db.bind([Users, Messages])
        self.db.create_tables([Users, Messages])
        self.tree = app_commands.CommandTree(self)
        self._instances.add(weakref.ref(self))

    @property
    def bot_config(self) -> dict[str, Any]:
        return self.__bot_config
    
    @bot_config.setter
    def bot_config(self) -> None:
        raise NotImplementedError
    
    async def setup_hook(self) -> None:
        from admin_commands import CommandGroupAdmin
        mygroupadmin = CommandGroupAdmin(name="voidadmin", description="admin tools")
        self.tree.add_command(mygroupadmin)
        self.tree.copy_global_to(guild=discord.Object(self.__bot_config["activeserver"]))
        await self.tree.sync(guild=discord.Object(self.__bot_config["activeserver"]))

    async def on_message(self, message: discord.Message) -> None:
        if message.guild is None and not message.author.bot:
            if self.server.get_member(message.author.id) is not None:
                try:
                    user: Users = Users.get(Users.discord_id == message.author.id)
                except Users.DoesNotExist:
                    user: Users = Users.create(discord_id=message.author.id)
                messagedb: Messages = Messages.create(uuid=str(uuid4())[:8], post_time=datetime.now(), user=user)
                self.message_queue.append({"user": user, "messagedb": messagedb, "message": message})

    async def on_connect(self) -> None:
        await self.wait_until_ready()

        try:
            self.channel = self.get_channel(self.__bot_config["activechannel"])
        except KeyError:
            logger.critical("Failed to find activechannel in config. Exiting.")
            sys.exit(1)
        if not self.channel:
            logger.critical(f"Failed to capture a channel. Exiting.")
            sys.exit(1)
        logger.info("got channel")

        try:
            self.server = self.get_guild(self.__bot_config["activeserver"])
        except KeyError:
            logger.critical("Failed to find activeserver in config. Exiting.")
            sys.exit(1)
        if not self.server:
            logger.critical(f"Failed to capture a server. Exiting.")
            sys.exit(1)
        logger.info("got server")

        if not self._current_loop:
            self._current_loop = asyncio.get_running_loop()
            logger.info("got loop")
        if not self._runner:
            self._runner = self._current_loop.create_task(self.__run_churn())
            logger.info("running churn")

        await self.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name="Direct messages to send to the void."))

    async def __run_churn(self) -> None:
        backoff: float = 1.0
        while True:
            # delete message associations after 3 days - we assume the content
            # is fine if it hasn't been moderated
            dt = datetime.now() - timedelta(days=3)
            q = Messages.delete().where(Messages.post_time < dt)
            q.execute()
            await asyncio.sleep(backoff)
            if self.message_queue:
                try:
                    message = self.message_queue.pop()
                    reply_to_msg = None
                    if message['message'].clean_content.startswith(f"@https://discord.com/channels/{self.server.id}/{self.channel.id}/"):
                        reply_to_msg = await self.channel.fetch_message(message['message'].clean_content.split(' ', 1)[0].rsplit('/', 1)[-1])
                        send_text = message['message'].clean_content.split(' ', 1)[1]
                        if not reply_to_msg:
                            message['message'].reply("Invalid message link for reply")
                            return

                    embed = Embed(uuid=message['messagedb'].uuid)
                    if reply_to_msg:
                        embed.description = f"{send_text}"
                        sent = await reply_to_msg.reply(embed=embed)
                    else:
                        embed.description = f"{message['message'].clean_content}"
                        sent = await self.channel.send(embed=embed)
                    message["messagedb"].discord_message_id = sent.id
                    message["messagedb"].save()
                    if backoff > 0.5:
                        backoff = backoff - 0.5


                except Exception as e:
                    logger.info(e)
                    logger.info(f"{traceback.format_exc()}")
                    self.message_queue.insert(0, message)
                    backoff = backoff + 0.5

    @classmethod
    def get_instances(cls) -> "Client":
        dead = set()
        for ref in cls._instances:
            obj = ref()
            if obj is not None:
                yield obj
            else:
                dead.add(ref)
        cls._instances -= dead
