from selenium import webdriver
from pathlib import Path
import re

driver = webdriver.Firefox()


def get_id_from_url(url):
    return int(re.search("\\d+$", url).group())


limit = 100
ids = []
for page in range(50, limit + 1):
    url = f"https://www.ultimate-guitar.com/explore?order=hitstotal_desc&type[]=Chords&page={page}"
    driver.get(url)
    all_links = driver.execute_script(
        'return document.querySelectorAll(".LRSRs header a")'
    )
    all_links = [link.get_attribute("href") for link in all_links]
    ids.extend(map(get_id_from_url, all_links))
    with open(
        Path(__file__).parent.parent.parent.parent / "out/ultimate_guitar_top_song_ids.txt", "w"
    ) as f:
        for id in ids:
            f.write(str(id) + "\n")

    print(f"Progress: {page}/{limit}")

driver.quit()
