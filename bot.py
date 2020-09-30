import random
import requests

from dotenv import load_dotenv
import sys
import os

import bs4 as bs
from bs4 import BeautifulSoup

import discord
from discord.ext import commands

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
    if name is None:
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
        for drop in boss_info['drops']:
            if drop[0] == 'item':
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
    if name is None:
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
        data = get_item_info(all_items[index][1])

        embed = discord.Embed(
            title=data["Name"],
            url="https://terraria.gamepedia.com" + all_items[index][1],
        )

        embed.set_thumbnail(url=data["ImageSource"])

        for k in data:
            if k not in ["Name", "ImageSource"]:
                embed.add_field(name=k, value=data[k])

        await ctx.send(embed=embed)

bot.run(TOKEN)
