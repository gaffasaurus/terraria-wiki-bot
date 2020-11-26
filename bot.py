import random
import math
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
    def __init__(self, embeds, sections):
        super().__init__()
        self.embeds = embeds
        self.page_number = 0
        self.sections = sections

    async def send_initial_message(self, ctx, channel):
        return await channel.send(embed=self.embeds[self.page_number])

    @menus.button("⏪")
    async def decrease_section(self, payload):
        prev_page = None
        rev_sections = self.sections[::-1]
        for i, v in enumerate(rev_sections[:-1]):
            if self.page_number <= v and self.page_number > rev_sections[i + 1]:
                prev_page = rev_sections[i + 1]

        if prev_page is None:
            prev_page = rev_sections[0]

        self.page_number = prev_page

        return await self.message.edit(embed=self.embeds[self.page_number])

    @menus.button("⬅️")
    async def decrease_page(self, payload):
        self.page_number -= 1
        return await self.message.edit(embed=self.embeds[self.page_number])

    @menus.button("➡️")
    async def increase_page(self, payload):
        self.page_number += 1
        self.page_number %= len(self.embeds)
        return await self.message.edit(embed=self.embeds[self.page_number])

    @menus.button("⏩")
    async def increase_section(self, payload):
        next_page = None
        for i, v in enumerate(self.sections[:-1]):
            if self.page_number >= v and self.page_number < self.sections[i + 1]:
                next_page = self.sections[i + 1]

        if next_page is None:
            next_page = self.sections[0]

        self.page_number = next_page

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


def create_craft_embed(base_embed, craft_data, is_craft):
    embeds = [base_embed.copy()]
    embed_data = defaultdict(lambda: [])
    if not craft_data["Result"]:
        embeds[0].add_field(
            name="Crafting" if is_craft else "Used in",
            value="No crafting recipes found."
            if is_craft
            else "This item is not used in any crafting recipes.",
            inline=True,
        )
    else:
        # seperate the categories
        page_breaks = []
        for k in ["Ingredients", "Result", "Stations"]:
            v = craft_data[k]
            full = []
            curr_embed_idx = 0

            # seperate the rows
            for ind, e in enumerate(v):
                craft_str = ""
                start_full_state = full.copy()

                max_height = max([len(i[ind]) for i in craft_data.values()])
                avg = (max_height - len(e)) / 2
                if e == ["prev"]:
                    if ind % 2 == 1:
                        full[-1] = (
                            "\u200b"
                            + "\n" * math.ceil((max_height + 1) / 2)
                            + full[-1]
                            + "\n" * math.floor((max_height + 1) / 2)
                        )
                    else:
                        full[-1] = (
                            "\u200b"
                            + "\n" * math.floor((max_height + 1) / 2)
                            + full[-1]
                            + "\n" * math.ceil((max_height + 1) / 2)
                        )
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
                    full.append(
                        "\u200b"
                        + "\n" * math.floor(avg)
                        + craft_str
                        + "\n" * math.ceil(avg)
                    )

                if len("—————————\n".join(full)) >= 1024 and k == "Ingredients":
                    page_breaks.append(ind)
                    embed_data[k].append(start_full_state)

                    full = [
                        "\n" * math.floor(avg)
                        + full[-1].strip("\n\u200b")
                        + "\n" * math.ceil(avg + 1)
                    ]

                    embeds.append(base_embed.copy())
                    embeds[-1].description = (
                        "Crafting recipes (cont.)"
                        if is_craft
                        else "Item use recipes (cont.)"
                    )

                if ind in page_breaks and k != "Ingredients":
                    embed_data[k].append(start_full_state)

                    full = [
                        "\u200b"
                        + "\n" * math.floor(avg)
                        + full[-1].strip("\n\u200b")
                        + "\n" * math.ceil(avg + 1)
                    ]

                    curr_embed_idx += 1

            embed_data[k].append(full)

        for k in ["Result", "Ingredients", "Stations"]:
            for i, v in enumerate(embed_data[k]):
                embeds[i].add_field(name=k, value="—————————\n".join(v), inline=True)

    return embeds


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

        data, craft_data, uses_data = all_data

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
        embed2.description = "Crafting recipes"

        embed3 = embed.copy()
        embed3.description = "Item use recipes"

        for k in data:
            if k not in ["Name", "ImageSource", "Tooltip", "RarityColor", "Max stack"]:
                embed.add_field(name=k, value=data[k], inline=True)

        craft_embeds = create_craft_embed(embed2, craft_data, True)
        uses_embeds = create_craft_embed(embed3, uses_data, False)

        m = EmbedPageMenu(
            [embed, *craft_embeds, *uses_embeds], [0, 1, len(craft_embeds) + 1]
        )
        await m.start(ctx)


bot.run(TOKEN)
