import requests
import random
from bs4 import BeautifulSoup

rarity_levels = {
    "-1": ("Grey (-1)", 0x6B6B69),
    "0": ("White (0)", 0xF2F2F2),
    "1": ("Blue (1)", 0x8689DF),
    "2": ("Green (2)", 0xABF59E),
    "3": ("Orange (3)", 0xDCB58D),
    "4": ("Light Red (4)", 0xE29593),
    "5": ("Pink (5)", 0xEA9AF3),
    "6": ("Light Purple (6)", 0xAD8DD1),
    "7": ("Lime (7)", 0x9AD84C),
    "8": ("Yellow (8)", 0xFAF853),
    "9": ("Cyan (9)", 0x56BFF0),
    "10": ("Red (10)", 0xBF3147),
    "11": ("Purple (11)", 0xA13FED),
    "Rainbow": ("Rainbow", "rainbow"),
    "Fiery red": ("Fiery Red", 0xFF4600),
    "Amber": ("Amber", 0xE0A63E),
}


def gen_item_list():
    url = requests.get("https://terraria.gamepedia.com/Item_IDs")
    items = []

    soup = BeautifulSoup(url.content, "html.parser")
    item_table = soup.find_all("table")[1]

    entries = item_table.find_all("tr")
    for entry in entries:
        fields = entry.find_all("td")
        for i, f in enumerate(fields):
            if i == 1:
                if "n/a" not in f.get_text():
                    items.append((f.get_text().lower(), f.find("a")["href"]))
    return items


def get_craft_info(div, craft_data):
    entries = div.find_all("tr")
    valid_cnt = 0

    for entry in entries:
        if entry.get_text() == "ResultIngredientsCrafting station":
            continue
        valid_cnt += 1

        result_div = entry.find("td", class_="result")
        if result_div:
            split = result_div.text.split("Internal Item ID:")
            res_str = split[0]
            if len(split) > 1:
                p = split[1].find("(")
                if p != -1:
                    res_str += " " + split[1][p:]

            found_empty = False
            empty_loc, new_str = None, res_str
            for i, c in enumerate(res_str):
                if c == "(":
                    found_empty = True
                    empty_loc = i
                elif c == ")" and found_empty:
                    break
                elif c.isalnum() and found_empty:
                    found_empty = False
                elif found_empty:
                    new_str = new_str.replace(c, "")

            if found_empty:

                versions = [
                    i["alt"].split("version")[0].strip()[0]
                    for i in result_div.find_all("img")
                ]

                v = ",".join([ver for ver in versions if ver in set("DMCO3")])

                empty_loc += 1
                new_str = new_str[:empty_loc] + v + new_str[empty_loc:]

            craft_data["Result"].append([new_str])

        ingredients = entry.find("td", class_="ingredients")
        if ingredients:
            items = ingredients.find_all("li")
            crafting_items = [(i.get_text(), i.find("a")["href"]) for i in items]
            craft_data["Ingredients"].append(crafting_items)

        station_div = entry.find("td", class_="station")
        if station_div:
            stations = set([(s["title"], s["href"]) for s in station_div.find_all("a")])
            craft_data["Stations"].append(stations)

        if len(craft_data["Result"]) < valid_cnt:
            craft_data["Result"].append(["prev"])

        if len(craft_data["Stations"]) < valid_cnt:
            craft_data["Stations"].append(["prev"])

    return craft_data


def get_item_info(item_name, item_link):
    new_link = "https://terraria.gamepedia.com" + item_link
    item_url = requests.get(new_link)

    soup = BeautifulSoup(item_url.content, "html.parser")

    stats_div_all = soup.find_all("div", class_="section statistics")
    if not stats_div_all:
        return "No information found"

    raw_item = "".join([i.lower() for i in item_name if i.isalpha()])
    stats_div = None
    img_src = None

    for s in stats_div_all:
        for sib in s.previous_siblings:
            if " ".join(sib["class"]) == "section images":
                curr_image = sib.find("img")
            if "".join([i.lower() for i in sib.text if i.isalpha()]) == raw_item:
                stats_div = s
                img_src = curr_image["src"]
        if stats_div is not None:
            break

    if stats_div is None:
        stats_div = stats_div_all[0]
        images_div = soup.find("div", class_="section images")
        if images_div:
            img_src = images_div.find("img")["src"]

    data = {
        "Name": soup.find("h1", class_="firstHeading").get_text(),
        "ImageSource": img_src,
    }

    entries = stats_div.find_all("tr")
    for entry in entries:
        if entry.find("th"):
            for br in entry.find_all("br"):
                br.replace_with("\n")

            field_name = entry.find("th").get_text()
            field_value = entry.find("td").get_text()

            if field_name == "Type":
                field_value = ""
                for item_type in entry.find_all("a"):
                    field_value += item_type.get_text() + "\n"
            elif field_name in ["Buy", "Sell"]:
                field_value = entry.find("td").find("span", class_="coin")["title"]
            elif field_name == "Rarity":
                title = entry.find("td").find("a")["title"]
                rarity = title.split(":")[-1].strip()
                field_value = rarity_levels[rarity][0]

                rarity_color = rarity_levels[rarity][1]
                if rarity_color == "rainbow":
                    r = lambda: random.randint(0, 255)
                    rarity_color = int("0x{:02x}{:02x}{:02x}".format(r(), r(), r()), 16)

                data["RarityColor"] = rarity_color
            elif field_name == "Placeable" and field_value.strip() == "":
                field_value = "Size varies"

            data[field_name] = field_value

    if "RarityColor" not in data:
        data["RarityColor"] = rarity_levels["0"][1]

    all_crafts_div = soup.find_all("div", class_="crafts")
    crafts_div = None
    used_in_div = None

    try:
        for c in all_crafts_div:
            if "Recipes" in c.find_previous("h3").text and crafts_div is None:
                crafts_div = c
            elif "Used in" in c.find_previous("h3").text and used_in_div is None:
                used_in_div = c
    except:
        crafts_div = all_crafts_div[0]

    craft_data = {
        "Result": [],
        "Ingredients": [],
        "Stations": [],
    }

    uses_data = {
        "Result": [],
        "Ingredients": [],
        "Stations": [],
    }

    if crafts_div:
        craft_data = get_craft_info(crafts_div, craft_data)

    if used_in_div:
        uses_data = get_craft_info(used_in_div, uses_data)

    return [data, craft_data, uses_data]


# print(get_item_info("iron bar", "/Iron_Bar"))
