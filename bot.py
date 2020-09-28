import random
import requests
import sys
import bs4 as bs
from bs4 import BeautifulSoup
import discord
# print(soup.prettify())

file = open("tokens.txt")
api_key = file.readline()

client = discord.Client()

prefix = "t!"

difficulty = "normal"

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
    "Stardust Pillar"
]

@client.event
async def on_ready():
    print("Ready")

@client.event
async def on_message(message):
    if message.author == client.user:
        return
    if message.content.lower().startswith(prefix):
        await process_commands(message.content.lower().replace(prefix, ""))

async def process_commands(message):
    message_split = message.split(" ")
    command = message_split[0]
    if command == "difficulty" or command == "mode":
        if len(message_split) == 1:
            await message.channel.send("Enter a difficulty (Normal, Expert, Master) to adjust the information to match that mode (Normal by default).")
        elif len(message_split) >= 2:
            if ["normal", "expert", "master"].includes(message_split[1]):
                difficulty = message_split[1]
                await message.channel.send("Difficulty changed to " + message_split[1])
            else:
                await message.channel.send("Please enter a valid difficulty (Normal, Expert, Master)")
    if command == "boss":
        if len(message_split) == 1:
            await message.channel.send("Specify a boss name to get information on it (Health, Damage, Drops, etc.)")
            return
        elif len(message_split) == 2:
            if [boss.lower() for boss in all_bosses].includes(message_split[1]):
                index = [boss.lower() for boss in all_bosses].index(message_split[1])
                boss_info = get_boss_info(all_bosses[index])
                drops = ""
                for drop in boss_info.drops:
                    if drop[0] == "item":
                        drops += drop[1] + ": " + drop[2] + "\n"
                    else:
                        drops += drop[1] + "\n"
                await message.channel.send("__" + boss_info.name + "__\n**Damage:** " + boss_info.damage + "\n**Max HP:** " + boss_info.max_hp + "\n**Immunities:** " + ", ".join(boss_info.immunities) + "\n**__Drops:__**\n" + boss_info.drops)



def get_boss_drops(boss, url, soup):
    # boss = "Queen Bee"
    boss_drops = []

    drop_sections = soup.find_all(class_='section drops')
    for drop_section in drop_sections:
        items = drop_section.find(class_="drops items")
        event_boss = False
        if items:
            if difficulty == "normal":
                drops = items.find_all(class_=["m-normal", "caption m-normal", "groupend m-normal"], recursive=False)
            elif difficulty == "expert":
                drops = items.find_all(class_=["m-expert-master", "m-expert-master loot", "caption m-expert-master", "groupend m-expert-master loot"], recursive=False)
            elif difficulty == "master":
                drops = items.find_all(class_=["m-expert-master", "m-expert-master loot", "caption m-expert-master", "groupend m-expert-master loot", "m-master"], recursive=False)

            if len(drops) == 0: #Event bosses formatted differently (?)
                event_boss = True
                drops = items.find_all("li")
            elif difficulty == "master":
                counter = 0
                for drop in drops:
                    if drop.has_attr("class") and drop['class'][0] == "m-master":
                        counter += 1
                    else:
                        break
                if counter == len(drops):
                    event_boss = True
                    drops = items.find_all("li")

            for drop in drops:
                if not drop.has_attr("class"):
                    continue
                #Caption
                if (drop['class'] == "caption" or (len(drop['class']) >= 1 and drop['class'][0] == "caption")):
                    caption = drop.find(text=True)
                    boss_drops.append(['caption', caption])
                    continue
                #Separator (ex. One of the following 2 items will drop, separates after 2 items)
                if len(drop['class']) > 1:
                    if drop['class'][0] == "groupend" or drop['class'][0] == "group_end":
                        if drop.find(text=True):
                            boss_drops.append(['separator', drop.find(text=True)])
                        else:
                            boss_drops.append(['separator', ""])
                        continue
                #Tag with title=item name
                drop_info = drop.find("a")
                #Divs inside, location of drop rate varies
                drop_rate = drop.find_all("div")
                try:
                    if not event_boss:
                        boss_drops.append(['item', drop_info['title'], drop_rate[1].get_text()])
                    else:
                        if difficulty == "normal":
                            rate = drop_rate[len(drop_rate)-1].find(class_="m-normal").get_text()
                        else:
                            if len(drop['class']) == 0 or (drop['class'][0] and drop['class'][0] != "m-master"):
                                rate = drop_rate[len(drop_rate)-1].find(class_="expert").get_text()
                            else:
                                if difficulty == "expert":
                                    continue
                                else:
                                    rate = drop_rate[len(drop_rate)-1].find(class_="master").get_text()
                        boss_drops.append(['item', drop_info['title'], rate])
                except:
                    print(sys.exc_info()[0])
                    raise
            # [0]: type of info (caption, separator, item), [1] main content (caption, separator, name of item), [2] rate of item, empty string for other types
            return boss_drops
    return -1

def get_boss_info(boss):
    try:
        url = requests.get("https://terraria.gamepedia.com/" + "_".join(boss.split(" ")))
    except:
        return "invalid url"
    soup = BeautifulSoup(url.content, 'html.parser')
    print(soup.prettify())
    drops = get_boss_drops(boss, url, soup)
    if drops == -1:
        return "Error: Something went wrong when getting that boss's information."
    name = soup.find("h1", class_="firstHeading").get_text()
    stats_div = soup.find("div", class_="section statistics")
    entries = stats_div.find_all("tr")
    damage = ""
    max_hp = ""
    immunities = []
    for entry in entries:
        if entry.find("th").get_text() and entry.find("th").get_text() == "Damage":
            damage = entry.find("td").find("span", class_="m-" + difficulty + " " + difficulty).find("span", class_="s").get_text()
        elif entry.find("th").get_text() and entry.find("th").get_text() == "Max Life":
            try:
                max_hp = entry.find("td").find("span", class_="m-" + difficulty + " " + difficulty).find("span", class_="s").get_text()
            except:
                try:
                    max_hp = entry.find("td").find("span", class_="m-" + difficulty).find(class_=difficulty).get_text()
                except:
                    print(sys.exc_info()[0])
                    raise
        elif entry.find("th").get_text() and entry.find("th").get_text() == "Immune to":
            try:
                immunities_list = entry.find("td").find_all("span", class_="i")
                for immunity in immunities_list:
                    immunities.push(immunity.find("a")['title'])
            except:
                try:
                    if entry.find("a")['title'] and entry.find("a")['title'] == "Debuffs":
                        immunities = "all debuffs"
                except:
                    print(sys.exc_info()[0])
                    raise
    return {
        'drops': drops,
        'damage': damage,
        'max_hp': max_hp,
        'immunities': immunities
    }


client.run(api_key)
