import json
import re
from datetime import datetime
from pathlib import Path

HTML_FILE = "linkedin_raw.html"


def limpiar(texto):
    return " ".join(texto.split()).strip() if texto else ""


def extraer_perfil(soup):
    nombre, titular, ubicacion = "", "", ""

    for h2 in soup.find_all("h2"):
        txt = limpiar(h2.get_text())
        if txt and len(txt) < 60 and nombre == "":
            nombre = txt

    for p in soup.find_all("p"):
        txt = limpiar(p.get_text())
        if not titular and any(k in txt for k in ["Técnico", "Desarrollador", "Engineer", "Developer"]):
            titular = txt
        if not ubicacion and "Barcelona" in txt:
            ubicacion = txt

    return {"nombre": nombre, "titular": titular, "ubicacion": ubicacion}


def extraer_servicios(soup):
    servicios = []
    for section in soup.find_all("section"):
        h2 = section.find("h2")
        if h2 and "Servicios" in h2.get_text():
            for p in section.find_all("p"):
                txt = limpiar(p.get_text())
                if txt and len(txt) > 3 and txt not in ("Solicitar servicios", "Mostrar todo"):
                    servicios.append(txt)
    return servicios


def extraer_experiencia(soup):
    experiencias = []
    for section in soup.find_all("section"):
        h2 = section.find("h2")
        if h2 and "Experiencia" in h2.get_text():
            items = section.find_all("div", attrs={"componentkey": re.compile(r"entity-collection-item")})
            for item in items:
                ps = [limpiar(p.get_text()) for p in item.find_all("p") if limpiar(p.get_text())]
                ps = [t for t in ps if t and "aptitudes" not in t.lower() and len(t) > 2]
                if len(ps) >= 2:
                    experiencias.append({
                        "cargo": ps[0],
                        "empresa_tipo": ps[1] if len(ps) > 1 else "",
                        "fechas": ps[2] if len(ps) > 2 else "",
                    })
    return experiencias


def extraer_educacion(soup):
    educacion = []
    for section in soup.find_all("section"):
        h2 = section.find("h2")
        if h2 and "Educación" in h2.get_text():
            items = section.find_all("div", class_=re.compile(r"_7882edda"))
            for item in items:
                ps = [limpiar(p.get_text()) for p in item.find_all("p") if limpiar(p.get_text())]
                ps = [t for t in ps if t and "aptitudes" not in t.lower() and len(t) > 2]
                if len(ps) >= 2:
                    educacion.append({
                        "centro": ps[0],
                        "titulo": ps[1] if len(ps) > 1 else "",
                        "fechas": ps[2] if len(ps) > 2 else "",
                    })
    return educacion


def extraer_certificaciones(soup):
    certs = []
    for section in soup.find_all("section"):
        h2 = section.find("h2")
        if h2 and ("Licencias" in h2.get_text() or "certificaciones" in h2.get_text().lower()):
            items = section.find_all("div", class_=re.compile(r"_7882edda"))
            for item in items:
                ps = [limpiar(p.get_text()) for p in item.find_all("p") if limpiar(p.get_text())]
                ps = [t for t in ps if t and len(t) > 2]
                if len(ps) >= 2:
                    certs.append({
                        "nombre": ps[0],
                        "emisor": ps[1] if len(ps) > 1 else "",
                        "fecha": ps[2] if len(ps) > 2 else "",
                    })
    return certs


def extraer_proyectos(soup):
    proyectos = []
    for section in soup.find_all("section"):
        h2 = section.find("h2")
        if h2 and "Proyectos" in h2.get_text():
            bloques = section.find_all("div", class_=re.compile(r"_7882edda"))
            for bloque in bloques:
                titulo_el = bloque.find("p", class_=re.compile(r"_5d25ee75"))
                titulo = limpiar(titulo_el.get_text()) if titulo_el else ""
                fechas_el = bloque.find("p", class_=re.compile(r"_4b17a66a"))
                fechas = limpiar(fechas_el.get_text()) if fechas_el else ""
                desc_el = bloque.find("span", attrs={"data-testid": "expandable-text-box"})
                desc = limpiar(desc_el.get_text()) if desc_el else ""
                asociado_el = bloque.find("p", class_=re.compile(r"d71dbced"))
                asociado = limpiar(asociado_el.get_text()) if asociado_el else ""
                if titulo:
                    proyectos.append({
                        "titulo": titulo,
                        "fechas": fechas,
                        "descripcion": desc,
                        "asociado": asociado,
                    })
    return proyectos


def extraer_aptitudes(soup):
    aptitudes = []
    for section in soup.find_all("section"):
        h2 = section.find("h2")
        if h2 and "Aptitudes" in h2.get_text():
            for p in section.find_all("p", class_=re.compile(r"_5d25ee75")):
                txt = limpiar(p.get_text())
                if txt and txt not in aptitudes:
                    aptitudes.append(txt)
    return aptitudes


def main():
    from bs4 import BeautifulSoup

    html_path = Path(HTML_FILE)
    if not html_path.exists():
        print(f"ERROR: No se encuentra '{HTML_FILE}'")
        print("  → Guarda el HTML de tu perfil de LinkedIn en ese archivo y vuelve a ejecutar.")
        raise SystemExit(1)

    print(f"Leyendo {HTML_FILE} ({html_path.stat().st_size // 1024} KB)...")
    soup = BeautifulSoup(html_path.read_text(encoding="utf-8"), "html.parser")

    datos = {
        "perfil":          extraer_perfil(soup),
        "servicios":       extraer_servicios(soup),
        "experiencia":     extraer_experiencia(soup),
        "educacion":       extraer_educacion(soup),
        "certificaciones": extraer_certificaciones(soup),
        "proyectos":       extraer_proyectos(soup),
        "aptitudes":       extraer_aptitudes(soup),
        "meta": {
            "fuente":      "linkedin_raw.html",
            "actualizado": datetime.now().isoformat(),
        },
    }

    with open("portfolio.json", "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=2)

    print("portfolio.json generado:")
    print(f"  Nombre:        {datos['perfil']['nombre']}")
    print(f"  Experiencias:  {len(datos['experiencia'])}")
    print(f"  Proyectos:     {len(datos['proyectos'])}")
    print(f"  Aptitudes:     {len(datos['aptitudes'])}")


if __name__ == "__main__":
    main()
