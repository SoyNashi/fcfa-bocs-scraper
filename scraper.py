import requests
from bs4 import BeautifulSoup
import json

URLS = {
    "Lliga Senior": "https://www.fcfa.cat/lliga-catalana-de-futbol-america-25-26/",
    "Lliga Junior": "https://www.fcfa.cat/lliga-catalana-de-futbol-america-junior-25-26/",
    "Lliga Cadet":  "https://www.fcfa.cat/lliga-catalana-de-futbol-america-cadet-25-26/",
    "Copa Senior":  "https://www.fcfa.cat/copa-catalana-de-futbol-america-senior-25-26/",
    "Copa Cadet":   "https://www.fcfa.cat/copa-catalana-de-futbol-america-cadet-25-26/",
}

def es_nuestro(texto, categoria):
    t = texto.lower()
    if "senior" in categoria.lower():
        return "bocs" in t
    return "bocs" in t or "argentona" in t

def main():
    partidos = []
    headers = {"User-Agent": "Mozilla/5.0 (compatible; FCFA-Bocs/1.0)"}

    for categoria, url in URLS.items():
        r = requests.get(url, headers=headers, timeout=20)
        soup = BeautifulSoup(r.text, "html.parser")

        for block in soup.find_all(["div", "p", "li"]):
            text = " ".join(block.get_text(" ", strip=True).split())
            if len(text) < 40:
                continue
            if not es_nuestro(text, categoria):
                continue
            partidos.append({"categoria": categoria, "texto": text})

    with open("partidos.json", "w", encoding="utf-8") as f:
        json.dump(partidos, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()
