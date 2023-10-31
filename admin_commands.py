from typing import Literal, Optional

import discord

from discord import app_commands

from main import Client
from messages.models import Users, Messages, db

class CommandGroupAdmin(app_commands.Group):
    @app_commands.command(name="moderateuser")
    async def admin_moderate(self, interaction: discord.Interaction, action: Literal["Warn", "Kick", "Ban"], uuid: str, reason: Optional[str]) -> None:
        msg_db = Messages.get_or_none(uuid=uuid)
        for client in Client.get_instances():
            pass
        msg = await client.channel.fetch_message(int(msg_db.discord_message_id))
        await msg.delete()
        user = client.get_user(int(msg_db.user.discord_id))

        try:
            if not reason:
                reason = "No reason given."
            if action == "Warn":
                await user.send(f"A post of yours has been removed. This is only a warning. Reason given - {reason}")
            elif action == "Kick":
                await user.kick(reason=reason)
            elif action == "Ban":
                await user.ban(reason=reason)

        except Exception:
            pass

        finally:
            await interaction.response.send_message(f"k", ephemeral=True)
