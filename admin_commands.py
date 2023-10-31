import discord
from discord import app_commands

from main import Client
from messages.models import Users, Messages, db

class CommandGroupAdmin(app_commands.Group):
    @app_commands.command(name="warnuser")
    async def admin_warn(self, interaction: discord.Interaction, uuid: str) -> None:
        msg_db = Messages.get_or_none(uuid=uuid)
        for client in Client.get_instances():
            pass
        msg = await client.channel.fetch_message(int(msg_db.discord_message_id))
        await msg.delete()
        user = client.get_user(int(msg_db.user.discord_id))
        await user.send(f"A post of yours has been removed. This is only a warning.")
        await interaction.response.send_message(f"k", ephemeral=True)
