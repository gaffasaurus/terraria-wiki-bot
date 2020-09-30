import requests
import random
import bs4 as bs
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
                items.append((f.get_text().lower(), f.find("a")["href"]))
    return items


def get_item_info(item_link):
    new_link = "https://terraria.gamepedia.com" + item_link
    item_url = requests.get(new_link)

    soup = BeautifulSoup(item_url.content, "html.parser")

    stats_div = soup.find("div", class_="section statistics")
    if not stats_div:
        return "No information found"

    images_div = soup.find("div", class_="section images")
    if images_div:
        img = images_div.find("img")
    else:
        img = {"src": None}

    data = {
        "Name": soup.find("h1", class_="firstHeading").get_text(),
        "ImageSource": img["src"],
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
    return data


# print(get_item_info("/Minecart_Track"))
