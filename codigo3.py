#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Scraper rápido de Marvel Rivals:
- Delay inicial de 10 s
- Extrae K/D/A, daño, curación, MVP, héroe y rol
- Perfil objetivo: player/209656717
"""

import time
import csv
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException

# Diccionario de héroes
HERO_MAP = {
    "1015001": "Storm", "1023001": "Rocket Raccoon", "1040001": "Mister Fantastic",
    "1011001": "Hulk", "1034001": "Iron Man", "1022001": "Captain America",
    "1029001": "Magik", "1042001": "Peni Parker", "1020001": "Mantis",
    "1039001": "Thor", "1016001": "Loki", "1052001": "Iron Fist",
    "1017001": "Human Torch", "1053001": "Emma Frost", "1027001": "Groot",
    "1046001": "Adam Warlock", "1018001": "Doctor Strange", "1024001": "Hela",
    "1036001": "Spider Man", "1051001": "The Thing", "1038001": "Scarlet Witch",
    "1048001": "Psylocke", "1035001": "Venom", "1045001": "Namor",
    "1025001": "Cloak & Dagger", "1026001": "Black Panther", "1043001": "Star Lord",
    "1050001": "Invisible Woman", "1021001": "Hawkeye", "1049001": "Wolverine",
    "1037001": "Magneto", "1014001": "The Punisher", "1030001": "Moon Knight",
    "1032001": "Squirrel Girl", "1031001": "Luna Snow", "1041001": "Winter Soldier",
    "1047001": "Jeff The Land Shark", "1033001": "Black Widow"
}

# Nuevo: asignación de rol (1=Vanguard, 2=Duelist, 3=Strategist)
HERO_ROLE_MAP = {
    "1018001": 1,  # Doctor Strange
    "1011001": 1,  # Hulk
    "1034001": 2,  # Iron Man
    "1036001": 2,  # Spider Man
    "1031001": 3,  # Luna Snow
    "1045001": 2,  # Namor
    "1016001": 3,  # Loki
    "1026001": 2,  # Black Panther
    "1029001": 2,  # Magik
    "1023001": 3,  # Rocket Raccoon
    "1027001": 1,  # Groot
    "1042001": 1,  # Peni Parker
    "1015001": 2,  # Storm
    "1037001": 1,  # Magneto
    "1043001": 2,  # Star Lord
    "1020001": 3,  # Mantis
    "1014001": 2,  # The Punisher
    "1038001": 2,  # Scarlet Witch
    "1024001": 2,  # Hela
    "1035001": 1,  # Venom
    "1046001": 3,  # Adam Warlock
    "1047001": 3,  # Jeff The Land Shark
    "1039001": 1,  # Thor
    "1041001": 2,  # Winter Soldier
    "1022001": 1,  # Captain America
    "1048001": 2,  # Psylocke
    "1030001": 2,  # Moon Knight
    "1021001": 2,  # Hawkeye
    "1032001": 2,  # Squirrel Girl
    "1052001": 2,  # Iron Fist
    "1033001": 2,  # Black Widow
    "1025001": 3,  # Cloak & Dagger
    "1049001": 2,  # Wolverine
    "1040001": 2,  # Mister Fantastic
    "1050001": 3,  # Invisible Woman
    "1017001": 2,  # Human Torch
    "1051001": 1,  # The Thing
    "1053001": 1   # Emma Frost
}

def save_to_csv(data, filename='rivals_data.csv'):
    if not data:
        print("[!] No hay datos para guardar.")
        return
    keys = data[0].keys()
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(data)
    print(f"[+] Guardados {len(data)} registros en '{filename}'.")

def scrape_player(player_id: str):
    all_data = []
    url = f"https://rivalsmeta.com/player/{player_id}"

    opts = uc.ChromeOptions()
    opts.headless = False
    opts.add_argument("--window-size=1200,900")
    driver = uc.Chrome(options=opts)
    wait = WebDriverWait(driver, 12)

    try:
        print("[+] Abriendo página:", url)
        driver.get(url)

        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.matches")))
        print("[+] Contenedor 'matches' cargado.")
        
        print("[*] Esperando 10 s antes de empezar...")
        time.sleep(10)

        idx = 1
        while True:
            matches = driver.find_elements(By.CSS_SELECTOR, "div.matches > div.match-details")
            if idx > len(matches):
                print(f"[*] No hay más partidas ({idx-1} de {len(matches)}).")
                break

            match = matches[idx - 1]
            print(f"\n[►] Partida #{idx} de {len(matches)}")
            driver.execute_script("arguments[0].scrollIntoView(true);", match)
            time.sleep(0.1)

            # Intentar expandir partida
            try:
                btn_expand = match.find_element(By.CSS_SELECTOR, "a.match .link-ind")
                btn_expand.click()
                wait.until(EC.presence_of_element_located((
                    By.CSS_SELECTOR,
                    f"div.matches > div.match-details:nth-child({idx}) tr"
                )))
                time.sleep(0.2)
            except Exception as e:
                print(f"    ! No expandió: {e}")

            rows = match.find_elements(By.CSS_SELECTOR, "tr")
            print(f"    • {len(rows)} filas extraídas")
            for r, row in enumerate(rows, start=1):
                try:
                    raw_kda = row.find_element(By.CSS_SELECTOR, ".kda .avg").text
                    k, d, a = [int(x.strip()) for x in raw_kda.split("/")]

                    dmg       = int(row.find_element(By.CSS_SELECTOR, ".stat-value.damage .text")
                                    .text.replace(",", ""))
                    dmg_taken = int(row.find_element(By.CSS_SELECTOR, ".stat-value.dmg-taken .text")
                                    .text.replace(",", ""))
                    heal      = int(row.find_element(By.CSS_SELECTOR, ".stat-value.heal .text")
                                    .text.replace(",", ""))

                    # MVP/SVP flag
                    try:
                        row.find_element(By.CSS_SELECTOR, ".badges .mvp, .badges .svp")
                        mvp_flag = True
                    except NoSuchElementException:
                        mvp_flag = False

                    # Hero info
                    try:
                        hero_img = row.find_element(By.CSS_SELECTOR, ".hero img")
                        src = hero_img.get_attribute("src")
                        hero_id = src.split("img_selecthero_")[-1].split(".")[0]
                        hero_name = HERO_MAP.get(hero_id, "Desconocido")
                    except Exception:
                        hero_id = None
                        hero_name = "Desconocido"

                    # Nuevo: asignación de rol
                    role_code = HERO_ROLE_MAP.get(hero_id, 0)

                    entry = {
                        "match": idx,
                        "row": r,
                        "kills": k, "deaths": d, "assists": a,
                        "damage": dmg, "dmg_taken": dmg_taken,
                        "healing": heal, "mvp": mvp_flag,
                        "hero_id": hero_id, "hero_name": hero_name,
                        "role": role_code
                    }
                    all_data.append(entry)
                    print(f"      - {entry}")
                except Exception as ex:
                    print(f"      ! Error fila {r}: {ex}")

            idx += 1
            time.sleep(0.1)

    except Exception as gen:
        print(f"[!] Error inesperado: {gen}")

    finally:
        save_to_csv(all_data)
        driver.quit()
        print("[*] Terminado.")

if __name__ == "__main__":
    scrape_player("209656717")
