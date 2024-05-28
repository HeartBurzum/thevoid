from typing import Literal, Optional

import discord

from discord import app_commands

from main import Client
from messages.models import Messages


class CommandGroupAdmin(app_commands.Group):
    @app_commands.command(name="moderateuser")
    async def admin_moderate(
        self,
        interaction: discord.Interaction,
        action: Literal["Warn", "Kick", "Ban"],
        uuid: str,
        reason: Optional[str],
    ) -> None:
        msg_db = Messages.get_or_none(uuid=uuid)
        for client in Client.get_instances():
            pass
        if msg_db is None:
            await interaction.response.send_message(
                f"No message found with uuid {uuid}", ephemeral=True
            )
            return
        msg = await client.channel.fetch_message(int(msg_db.discord_message_id))
        await msg.delete()
        user = client.get_user(int(msg_db.user.discord_id))

        try:
            if not reason:
                reason = "No reason given."

            match action:
                case "Warn":
                    await user.send(
                        f"A post of yours has been removed. This is only a warning. Reason given - {reason}"
                    )
                    status = "user successfully warned"
                case "Kick":
                    await client.server.kick(reason=reason)
                    status = "user successfully kicked"
                case "Ban":
                    await client.server.ban(user, reason=reason)
                    status = "user successfully banned"

        except (discord.NotFound, discord.Forbidden, discord.HTTPException) as e:
            status = f"{e}"
            pass
        except Exception as e:
            status = f"{e}"
            pass

        finally:
            await interaction.response.send_message(f"{status}", ephemeral=True)
