import requests
import bs4 as bs
from bs4 import BeautifulSoup


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

    images_div = soup.find("div", class_="section images")
    img = images_div.find("img")

    stats_div = soup.find("div", class_="section statistics")

    data = {
        "Name": soup.find("h1", class_="firstHeading").get_text(),
        "ImageSource": img["src"],
    }

    entries = stats_div.find_all("tr")
    for entry in entries:
        if entry.find("th"):
            data[entry.find("th").get_text()] = entry.find("td").get_text()

    return data