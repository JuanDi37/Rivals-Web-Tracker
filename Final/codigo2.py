#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Scraper rápido de Marvel Rivals con delay inicial de 10 s y 
optimizado para recorrer partidas sin pausas demasiado largas.
Usa el jugador 1044438082 por defecto.
"""

import time
import csv
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException

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
        print("[+] Iniciando scraping rápido. Pulsa 'Show More' si lo necesitas.")

        idx = 1
        while True:
            matches = driver.find_elements(By.CSS_SELECTOR, "div.matches > div.match-details")
            if idx > len(matches):
                print(f"[*] No hay más partidas ({idx} de {len(matches)}).")
                break

            match = matches[idx - 1]
            print(f"\n[►] Partida #{idx} de {len(matches)}")
            driver.execute_script("arguments[0].scrollIntoView(true);", match)
            time.sleep(0.1)

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
            print(f"    • {len(rows)} filas")
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

                    try:
                        row.find_element(By.CSS_SELECTOR, ".badges .mvp, .badges .svp")
                        mvp_flag = True
                    except NoSuchElementException:
                        mvp_flag = False

                    entry = {
                        "match": idx,
                        "row": r,
                        "kills": k, "deaths": d, "assists": a,
                        "damage": dmg, "dmg_taken": dmg_taken,
                        "healing": heal, "mvp": mvp_flag
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
    scrape_player("1044438082")
