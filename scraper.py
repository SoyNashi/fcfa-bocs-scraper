import requests
from bs4 import BeautifulSoup
import json
import re

URLS = {
    "Lliga Senior": "https://www.fcfa.cat/lliga-catalana-de-futbol-america-25-26/",
    "Lliga Junior": "https://www.fcfa.cat/lliga-catalana-de-futbol-america-junior-25-26/",
    "Lliga Cadet":  "https://www.fcfa.cat/lliga-catalana-de-futbol-america-cadet-25-26/",
}

RECORTE_IZQ = 30
RECORTE_DER = 65

def es_nuestro(texto, categoria):
    t = texto.lower()
    if "senior" in categoria.lower():
        return "bocs" in t
    return "bocs" in t or "argentona" in t

def extraer_segmentos(texto, palabra="bocs", izq=80, der=80):
    segmentos = []
    for m in re.finditer(palabra, texto, re.IGNORECASE):
        start = max(0, m.start() - izq)
        end = min(len(texto), m.end() + der)
        segmentos.append(texto[start:end])
    return segmentos

def main():
    partidos = []
    vistos = set()  # anti-duplicados
    headers = {"User-Agent": "Mozilla/5.0 (compatible; FCFA-Bocs/1.0)"}

    for categoria, url in URLS.items():
        r = requests.get(url, headers=headers, timeout=20)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")

        for block in soup.find_all(["div", "p", "li"]):
            text = " ".join(block.get_text(" ", strip=True).split())
            if len(text) < 40:
                continue
            if not es_nuestro(text, categoria):
                continue

            for seg in extraer_segmentos(text):
                clave = seg.lower()  # normalizamos para evitar duplicados por mayúsculas
                if clave in vistos:
                    continue
                vistos.add(clave)

                partidos.append({
                    "categoria": categoria,
                    "texto": seg
                })

    with open("partidos.json", "w", encoding="utf-8") as f:
        json.dump(partidos, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()
