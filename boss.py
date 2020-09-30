import bs4 as bs
import requests
from bs4 import BeautifulSoup
import sys

def get_boss_drops(boss, url, soup, difficulty):
    # boss = "Queen Bee"
    boss_drops = []

    drop_sections = soup.find_all(class_="section drops")
    for drop_section in drop_sections:
        items = drop_section.find(class_="drops items")
        event_boss = False
        if items:
            if difficulty == "normal":
                drops = items.find_all(
                    class_=["m-normal", "caption m-normal", "groupend m-normal"],
                    recursive=False,
                )
            elif difficulty == "expert":
                drops = items.find_all(
                    class_=[
                        "m-expert-master",
                        "m-expert-master loot",
                        "caption m-expert-master",
                        "groupend m-expert-master loot",
                    ],
                    recursive=False,
                )
            elif difficulty == "master":
                drops = items.find_all(
                    class_=[
                        "m-expert-master",
                        "m-expert-master loot",
                        "caption m-expert-master",
                        "groupend m-expert-master loot",
                        "m-master",
                    ],
                    recursive=False,
                )

            if len(drops) == 0:  # Event bosses formatted differently (?)
                event_boss = True
                drops = items.find_all("li")
            elif difficulty == "master":
                counter = 0
                for drop in drops:
                    if drop.has_attr("class") and drop["class"][0] == "m-master":
                        counter += 1
                    else:
                        break
                if counter == len(drops):
                    event_boss = True
                    drops = items.find_all("li")

            for drop in drops:
                if not drop.has_attr("class"):
                    continue
                # Caption
                if drop["class"] == "caption" or (
                    len(drop["class"]) >= 1 and drop["class"][0] == "caption"
                ):
                    caption = drop.find(text=True)
                    boss_drops.append(["caption", caption])
                    continue
                # Separator (ex. One of the following 2 items will drop, separates after 2 items)
                if len(drop["class"]) > 1:
                    if (
                        drop["class"][0] == "groupend"
                        or drop["class"][0] == "group_end"
                    ):
                        if drop.find(text=True):
                            boss_drops.append(["separator", drop.find(text=True)])
                        else:
                            boss_drops.append(["separator", ""])
                        continue
                # Tag with title=item name
                drop_info = drop.find("a")
                # Divs inside, location of drop rate varies
                drop_rate = drop.find_all("div")
                try:
                    if not event_boss:
                        boss_drops.append(
                            ["item", drop_info["title"], drop_rate[1].get_text()]
                        )
                    else:
                        if difficulty == "normal":
                            rate = (
                                drop_rate[len(drop_rate) - 1]
                                # .find(class_="m-normal")
                                .get_text()
                            )
                        else:
                            if len(drop["class"]) == 0 or (
                                drop["class"][0] and drop["class"][0] != "m-master"
                            ):
                                rate = (
                                    drop_rate[len(drop_rate) - 1]
                                    .find(class_="expert")
                                    .get_text()
                                )
                            else:
                                if difficulty == "expert":
                                    continue
                                else:
                                    rate = (
                                        drop_rate[len(drop_rate) - 1]
                                        .find(class_="master")
                                        .get_text()
                                    )
                        boss_drops.append(["item", drop_info["title"], rate])
                except:
                    boss_drops.append(["error", "Error"])
                    print(sys.exc_info()[0])
                    raise
            # [0]: type of info (caption, separator, item), [1] main content (caption, separator, name of item), [2] rate of item, empty string for other types
            return boss_drops
    return -1


def get_boss_info(boss, difficulty):
    try:
        url = requests.get(
            "https://terraria.gamepedia.com/" + "_".join(boss.split(" "))
        )
    except:
        return "invalid url"
    soup = BeautifulSoup(url.content, "html.parser")
    # print(soup.prettify())
    drops = get_boss_drops(boss, url, soup, difficulty)
    if drops == -1:
        return "Error: Something went wrong when getting that boss's information."
    name = soup.find("h1", class_="firstHeading").get_text()
    stats_div = soup.find("div", class_="section statistics")
    entries = stats_div.find_all("tr")
    damage = ""
    max_hp = ""
    immunities = []
    for entry in entries:
        # print(entry.prettify())
        # print("————————————————————————————————————————————————————————————————————")
        if entry.find("th").get_text() and entry.find("th").get_text() == "Damage":
            try:
                if difficulty == "normal":
                    damage = (
                        entry.find("td")
                        .find("span", class_="m-normal")
                        .get_text()
                    )
                else:
                    damage = (
                        entry.find("td")
                        .find("span", class_="m-" + difficulty + " " + difficulty)
                        .find("span", class_="s")
                        .get_text()
                    )
            except Exception as e:
                print(e)
                damage = "Error"
        elif entry.find("th").get_text() and entry.find("th").get_text() == "Max Life":
            try:
                if difficulty == "normal":
                    max_hp = (
                        entry.find("td")
                        .find("span", class_="m-normal")
                        .get_text()
                    )
                else:
                    max_hp = (
                        entry.find("td")
                        .find("span", class_="m-" + difficulty + " " + difficulty)
                        .find("span", class_="s")
                        .get_text()
                    )
            except Exception as e:
                print(e)
                try:
                    max_hp = (
                        entry.find("td")
                        .find("span", class_="m-" + difficulty)
                        .find(class_=difficulty)
                        .get_text()
                    )
                except:
                    max_hp = "Error"
                    print(sys.exc_info()[0])
                    raise
        elif entry.find("th").get_text() and entry.find("th").get_text() == "Immune to":
            try:
                immunities_list = entry.find("td").find_all(class_="i")
                print(immunities_list)
                print()
                for immunity in immunities_list:
                    print(immunity.find("a")['title'])
                    print()
                    immunities.append(immunity.find("a")["title"])
            except:
                try:
                    if (
                        entry.find("a")["title"]
                        and entry.find("a")["title"] == "Debuffs"
                    ):
                        immunities = ["All debuffs"]
                except:
                    immunities = ["Error"]
                    print(sys.exc_info()[0])
                    raise
    print(immunities)
    return {
        "name": name,
        "drops": drops,
        "damage": damage,
        "max_hp": max_hp,
        "immunities": immunities
    }
