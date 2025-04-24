import csv
import re
import time
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup

# Corrected URL
URL = "https://rivalsmeta.com/characters"

# Setup Chrome
options = uc.ChromeOptions()
# Comment out to see browser window if needed
# options.add_argument("--headless=new")
options.add_argument("--start-maximized")
driver = uc.Chrome(options=options)

# Open site
driver.get(URL)
print("[*] Loading page...")
time.sleep(5)  # let the JS load

# Wait for the table
try:
    WebDriverWait(driver, 30).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "table.characters-table"))
    )
except Exception as e:
    print("[!] Table not found:", e)
    print(driver.page_source[:1000])  # print partial HTML to debug
    driver.quit()
    exit()

# Parse the page
soup = BeautifulSoup(driver.page_source, "html.parser")
rows = soup.select("table.characters-table tbody tr")

# Extract hero_id and name
hero_data = []
for row in rows:
    img = row.select_one("img.img-banner")
    name_div = row.select_one("div.name")
    if img and name_div:
        match = re.search(r"img_hero_skill_banner_(\d+)\.png", img["src"])
        if match:
            hero_id = match.group(1)
            hero_name = name_div.get_text(strip=True)
            hero_data.append({"hero_id": hero_id, "hero_name": hero_name})

# Write to CSV
filename = "marvel_hero_ids.csv"
with open(filename, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=["hero_id", "hero_name"])
    writer.writeheader()
    writer.writerows(hero_data)

print(f"[✓] Extracted {len(hero_data)} heroes to {filename}")
driver.quit()
