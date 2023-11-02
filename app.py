import sys
import json

from discord import Intents

from main import Client


def main(config: dict[str, bool|str|int], client: Client) -> None:


    if config["debug"]:
        client.run(config["devtoken"])
    else:
        client.run(config["prodtoken"])
    return


if __name__ == "__main__":
    try:
        with open("config.json", "r") as config_file:
            config: dict[str, bool|str|int] = json.load(config_file)
    except FileNotFoundError:
        sys.exit(1)
    intents = Intents.all()
    intents.members = True
    intents.presences = True
    main(config, Client(intents=intents, config=config))