from discord import Embed as DiscordEmbed

class Embed(DiscordEmbed):
    def __init__(self, uuid: str, **kwargs):
        super().__init__(**kwargs)
        self.set_footer(text=f"TheVoid\n{uuid}")
        self.color = 2303786
