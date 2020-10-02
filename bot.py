import random
import requests

from dotenv import load_dotenv
import sys
import os

import bs4 as bs
from bs4 import BeautifulSoup

import discord
from discord.ext import commands
from discord.ext import menus

from collections import defaultdict
import pickle

from fuzzywuzzy import process

from boss import *
from items import *

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

bot = commands.Bot(command_prefix="t!")


class GuildSetting:
    def __init__(self):
        self.difficulty = "normal"


def dd():
    return GuildSetting()


if not os.path.isfile("data.txt") or os.path.getsize("data.txt") == 0:
    guild_settings = defaultdict(dd)
else:
    data_file = open("data.txt", "rb")
    guild_settings = pickle.load(data_file)

all_bosses = [
    "King Slime",
    "Eye of Cthulhu",
    "Eater of Worlds",
    "Brain of Cthulhu",
    "Queen Bee",
    "Skeletron",
    "Wall of Flesh",
    "Queen Slime",
    "The Twins",
    "The Destroyer",
    "Skeletron Prime",
    "Plantera",
    "Golem",
    "Empress of Light",
    "Duke Fishron",
    "Lunatic Cultist",
    "Moon Lord",
    "Dark Mage",
    "Ogre",
    "Betsy",
    "Flying Dutchman",
    "Mourning Wood",
    "Pumpking",
    "Everscream",
    "Santa-NK1",
    "Ice Queen",
    "Martian Saucer",
    "Solar Pillar",
    "Nebula Pillar",
    "Vortex Pillar",
    "Stardust Pillar",
]

all_items = gen_item_list()


class EmbedPageMenu(menus.Menu):
    def __init__(self, embeds):
        super().__init__()
        self.embeds = embeds
        self.page_number = 0

    async def send_initial_message(self, ctx, channel):
        return await channel.send(embed=self.embeds[self.page_number])

    @menus.button("⬅️")
    async def decrease_page(self, payload):
        self.page_number -= 1
        return await self.message.edit(embed=self.embeds[self.page_number])

    @menus.button("➡️")
    async def increase_page(self, payload):
        self.page_number += 1
        self.page_number %= len(self.embeds)
        return await self.message.edit(embed=self.embeds[self.page_number])


@bot.event
async def on_ready():
    print(f"{bot.user.name} has connected to Discord!")


@bot.command(name="difficulty", help="Choose a difficulty mode.", aliases=["mode"])
async def set_difficulty(ctx, mode=None):
    global guild_settings

    if mode is None:
        await ctx.send(
            f"The current difficulty is **{guild_settings[ctx.guild.id].difficulty}**."
        )
        return

    mode = mode.lower()
    if mode in ["normal", "expert", "master"]:
        guild_settings[ctx.guild.id].difficulty = mode

        data_file = open("data.txt", "wb")
        pickle.dump(guild_settings, data_file)

        await ctx.send(f"Difficulty has been set to **{mode}**.")
    else:
        await ctx.send(
            "Enter a valid difficulty (Normal, Expert, Master) to adjust the information to match that mode."
        )


@bot.command(
    name="boss",
    help="Specify a boss name to get information on it (Health, Damage, Drops, etc.)",
)
async def boss_info(ctx, *args):
    name = " ".join(args)
    if name == "":
        await ctx.send(
            "Specify a boss name to get information on it (Health, Damage, Drops, etc.)"
        )
        return

    boss_lower = [boss.lower() for boss in all_bosses]
    if name.lower() not in boss_lower:
        ratios = process.extract(name.lower(), boss_lower)
        close = [r for r in ratios if r[1] >= 75]
        close_str = ", ".join([r[0] for r in close])

        if len(close) > 0:
            await ctx.send(
                f"No boss exists with that name. Did you mean one of the following: {close_str}?"
            )
        else:
            await ctx.send("No boss exists with that name. No close matches found.")
    else:
        index = boss_lower.index(name.lower())
        boss_info = get_boss_info(
            all_bosses[index], guild_settings[ctx.guild.id].difficulty
        )
        drops = ""
        for drop in boss_info["drops"]:
            if drop[0] == "item":
                drops += drop[1] + ": " + drop[2] + "\n"
            else:
                drops += drop[1] + "\n"
        await ctx.send(
            "__"
            + boss_info["name"]
            + "__\n**Damage:** "
            + boss_info["damage"]
            + "\n**Max HP:** "
            + boss_info["max_hp"]
            + "\n**Immunities:** "
            + ", ".join(boss_info["immunities"])
            + "\n**__Drops:__**\n"
            # + ", ".join(str(drop) for drop in boss_info['drops'])
            + drops
        )


@bot.command(
    name="item",
    help="Specify an item name to get information on it.",
)
async def item_info(ctx, *args):
    name = " ".join(args)
    if name == "":
        await ctx.send("Specify an item name to get information on it.")
        return

    item_list = [i[0] for i in all_items]
    if name.lower() not in item_list:
        ratios = process.extract(name.lower(), item_list)
        close = [r for r in ratios if r[1] >= 75]
        close_str = ", ".join([r[0] for r in close])

        if len(close) > 0:
            await ctx.send(
                f"No item exists with that name. Did you mean one of the following: {close_str}?"
            )
        else:
            await ctx.send("No item exists with that name. No close matches found.")
    else:
        index = item_list.index(name.lower())
        all_data = get_item_info(*all_items[index])

        if all_data == "No information found":
            await ctx.send(
                f"This item led to <https://terraria.gamepedia.com{all_items[index][1]}> which had no specific item data available."
            )
            return

        data, craft_data = all_data

        embed = discord.Embed(
            title=data["Name"],
            url="https://terraria.gamepedia.com" + all_items[index][1],
            color=discord.Color(data["RarityColor"]),
        )

        if data["ImageSource"] is not None:
            embed.set_thumbnail(url=data["ImageSource"])

        if "Tooltip" in data:
            embed.description = data["Tooltip"]

        embed2 = embed.copy()

        for k in data:
            if k not in ["Name", "ImageSource", "Tooltip", "RarityColor", "Max stack"]:
                embed.add_field(name=k, value=data[k], inline=True)

        # seperate the categories
        for k, v in craft_data.items():
            full = []
            # seperate the rows
            for ind, e in enumerate(v):
                craft_str = ""
                max_height = max([len(i[ind]) for i in craft_data.values()])
                if e == ["prev"]:
                    full[-1] = (
                        "\u200b"
                        + "\n" * (int(max_height / 2) + 1)
                        + full[-1]
                        + "\n" * (int(max_height / 2))
                    )

                    print(full)

                else:
                    # seperate the items
                    for i in e:
                        if k == "Result":
                            craft_str += i + "\n"
                        else:
                            craft_str += (
                                f"[{i[0]}](https://terraria.gamepedia.com{i[1]})\n"
                            )

                if craft_str:
                    full.append(craft_str + "\n" * (max_height - len(e)))
            embed2.add_field(name=k, value="---------\n".join(full), inline=True)

        m = EmbedPageMenu([embed, embed2])
        await m.start(ctx)


bot.run(TOKEN)
