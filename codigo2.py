#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Scraper de Marvel Rivals que permite presionar 'Show More' manualmente.
Incluye delay de 10 segundos antes de comenzar.
Requiere: undetected-chromedriver, selenium
Instalación: pip install undetected-chromedriver selenium
"""

import time
import csv
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException

def save_to_csv(data, filename='rivals_data.csv'):
    """Guarda la lista de diccionarios en un CSV."""
    if not data:
        print("[!] No hay datos para guardar.")
        return
    keys = list(data[0].keys())
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(data)
    print(f"[+] Guardados {len(data)} registros en '{filename}'.")

def scrape_player(player_id: str):
    all_data = []
    url = f"https://rivalsmeta.com/player/{player_id}"

    # 1) Lanzar Chrome en modo visible
    opts = uc.ChromeOptions()
    opts.headless = False
    opts.add_argument("--window-size=1200,900")
    driver = uc.Chrome(options=opts)
    wait = WebDriverWait(driver, 15)

    try:
        print("[+] Abriendo página:", url)
        driver.get(url)

        # 2) Esperar el contenedor principal
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.matches")))
        print("[+] Contenedor 'matches' cargado.")
        
        # --- Delay antes de empezar ---
        print("[*] Esperando 10 segundos antes de iniciar el scraping...")
        time.sleep(10)

        print("[+] Ahora comienza el escaneo de partidas. Puedes pulsar manualmente 'Show More' si lo deseas.")

        # 3) Iterar dinámicamente sobre cada partida, refrescando la lista
        idx = 1
        while True:
            matches = driver.find_elements(By.CSS_SELECTOR, "div.matches > div.match-details")
            if idx > len(matches):
                print(f"[*] No hay más partidas cargadas (indice {idx} de {len(matches)}).")
                break

            match = matches[idx - 1]
            print(f"\n[►] Procesando partida #{idx} (total cargadas: {len(matches)})")
            driver.execute_script("arguments[0].scrollIntoView(true);", match)
            time.sleep(0.5)

            # 4) Expandir la partida
            try:
                btn_expand = match.find_element(By.CSS_SELECTOR, "a.match .link-ind")
                btn_expand.click()
                print("    • Click en icono para expandir")
                wait.until(EC.presence_of_element_located((
                    By.CSS_SELECTOR,
                    f"div.matches > div.match-details:nth-child({idx}) tr"
                )))
                time.sleep(1)
            except Exception as e:
                print(f"    ! No se pudo expandir: {e}")

            # 5) Extraer cada fila <tr>
            rows = match.find_elements(By.CSS_SELECTOR, "tr")
            print(f"    • Filas encontradas: {len(rows)}")
            for r, row in enumerate(rows, start=1):
                try:
                    raw_kda = row.find_element(By.CSS_SELECTOR, ".kda .avg").text
                    k, d, a = [int(x.strip()) for x in raw_kda.split("/")]

                    dmg       = int(row.find_element(By.CSS_SELECTOR, ".stat-value.damage .text")
                                    .text.replace(",", "").strip())
                    dmg_taken = int(row.find_element(By.CSS_SELECTOR, ".stat-value.dmg-taken .text")
                                    .text.replace(",", "").strip())
                    heal      = int(row.find_element(By.CSS_SELECTOR, ".stat-value.heal .text")
                                    .text.replace(",", "").strip())

                    try:
                        row.find_element(By.CSS_SELECTOR, ".badges .mvp, .badges .svp")
                        mvp_flag = True
                    except NoSuchElementException:
                        mvp_flag = False

                    entry = {
                        "match": idx,
                        "row": r,
                        "kills": k,
                        "deaths": d,
                        "assists": a,
                        "damage": dmg,
                        "dmg_taken": dmg_taken,
                        "healing": heal,
                        "mvp": mvp_flag
                    }
                    all_data.append(entry)
                    print(f"      - {entry}")
                except Exception as e:
                    print(f"      ! Error fila {r}: {e}")

            idx += 1
            time.sleep(0.5)

    except Exception as general_e:
        print(f"[!] Ocurrió un error inesperado: {general_e}")

    finally:
        # Siempre guarda lo que lleve hasta ahora
        save_to_csv(all_data)
        driver.quit()
        print("[*] Script finalizado.")

if __name__ == "__main__":
    scrape_player("209656717")
