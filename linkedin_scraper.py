import requests
from bs4 import BeautifulSoup
import json
import re
from datetime import datetime

PROFILE_URL = "https://www.linkedin.com/in/nil-blanch/"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


def limpiar(texto):
    return " ".join(texto.split()).strip() if texto else ""


def extraer_perfil(soup):
    nombre = limpiar(soup.select_one("h2._8f366b44._5846d695") and
                     soup.select_one("h2._8f366b44._5846d695").get_text())
    if not nombre:
        # Fallback: buscar por aria-label del enlace del perfil
        a = soup.find("a", href=re.compile(r"/in/nil-blanch"))
        if a:
            h2 = a.find("h2")
            nombre = limpiar(h2.get_text()) if h2 else ""

    titular = ""
    for p in soup.find_all("p"):
        txt = limpiar(p.get_text())
        if "Técnico Superior" in txt or "Desarrollador" in txt:
            titular = txt
            break

    ubicacion = ""
    for p in soup.find_all("p"):
        txt = limpiar(p.get_text())
        if "Barcelona" in txt and ("España" in txt or "Cataluña" in txt):
            ubicacion = txt
            break

    return {"nombre": nombre, "titular": titular, "ubicacion": ubicacion}


def extraer_servicios(soup):
    servicios = []
    # Buscar la sección "Servicios"
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
            # Cada entrada tiene cargo + empresa + fechas
            items = section.find_all("div", attrs={"componentkey": re.compile(r"entity-collection-item")})
            for item in items:
                ps = [limpiar(p.get_text()) for p in item.find_all("p") if limpiar(p.get_text())]
                ps = [t for t in ps if t and "aptitudes" not in t.lower() and len(t) > 2]
                if len(ps) >= 2:
                    cargo = ps[0]
                    empresa_tipo = ps[1] if len(ps) > 1 else ""
                    fechas = ps[2] if len(ps) > 2 else ""
                    experiencias.append({
                        "cargo": cargo,
                        "empresa_tipo": empresa_tipo,
                        "fechas": fechas,
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
                    centro = ps[0]
                    titulo = ps[1] if len(ps) > 1 else ""
                    fechas = ps[2] if len(ps) > 2 else ""
                    educacion.append({
                        "centro": centro,
                        "titulo": titulo,
                        "fechas": fechas,
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
    print(f"[{datetime.now().isoformat()}] Iniciando scraping de LinkedIn...")

    try:
        r = requests.get(PROFILE_URL, headers=HEADERS, timeout=20)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        fuente = "live"
        print("  → Perfil descargado correctamente")
    except Exception as e:
        print(f"  → Error al descargar el perfil: {e}")
        print("  → Usando datos hardcodeados del perfil")
        soup = None
        fuente = "hardcoded"

    if soup:
        perfil = extraer_perfil(soup)
        servicios = extraer_servicios(soup)
        experiencia = extraer_experiencia(soup)
        educacion = extraer_educacion(soup)
        certificaciones = extraer_certificaciones(soup)
        proyectos = extraer_proyectos(soup)
        aptitudes = extraer_aptitudes(soup)
    else:
        # Datos hardcodeados extraídos del HTML (fallback fiable)
        perfil = {
            "nombre": "Nil Blanch",
            "titular": "Técnico Superior en Desarrollo de Aplicaciones Multiplataforma",
            "ubicacion": "Barcelona, Cataluña, España",
        }
        servicios = [
            "Desarrollo web",
            "Desarrollo de aplicaciones en la nube",
            "Desarrollo de aplicaciones móviles",
            "Desarrollo de software personalizado",
            "Reparación de equipos informáticos",
            "Redes domésticas",
            "Consultoría de TI",
        ]
        experiencia = [
            {
                "cargo": "Desarrollador Full-Stack",
                "empresa_tipo": "Blau360 · Contrato de formación",
                "fechas": "mar. 2026 - actualidad · 4 meses",
            },
            {
                "cargo": "Personal de equipo",
                "empresa_tipo": "Food Arenys 118 SL · Jornada parcial",
                "fechas": "jul. 2025 - actualidad · 1 año",
            },
            {
                "cargo": "Reparación de equipos informáticos",
                "empresa_tipo": "Merkia · Contrato de formación",
                "fechas": "mar. 2025 - jun. 2025 · 4 meses",
            },
            {
                "cargo": "Técnico de radio",
                "empresa_tipo": "Maresmejant",
                "fechas": "sept. 2023 - nov. 2024 · 1 año 3 meses",
            },
            {
                "cargo": "Diseñador de páginas web ERASMUS+",
                "empresa_tipo": "PAPHOS STUDIO OF ART & DESIGN · Contrato de formación",
                "fechas": "may. 2024 - jun. 2024 · 2 meses",
            },
        ]
        educacion = [
            {
                "centro": "Institut Carles Vallbona",
                "titulo": "Ciclo Formativo de Grado Superior, Desarrollo de Aplicaciones Multiplataforma",
                "fechas": "sept. 2025 – Actualidad",
            },
            {
                "centro": "Escola Pia Mataró - Formació Professional",
                "titulo": "Ciclo Formativo de Grado Medio, Sistemas Microinformáticos y Redes",
                "fechas": "sept. 2023 – jun. 2025",
            },
        ]
        certificaciones = [
            {
                "nombre": "Linux Essentials",
                "emisor": "Cisco Networking Academy",
                "fecha": "Expedición: jun. 2026",
            }
        ]
        proyectos = [
            {
                "titulo": "Desarrollo Web para Blau360: WordPress + Facturación Digital y Firma Electrónica",
                "fechas": "mar. 2026 – Actualidad",
                "descripcion": (
                    "Creación de la web corporativa de Blau360 en WordPress, con sistema de "
                    "facturación digital, firma electrónica y envío automático de correos. "
                    "La plataforma está preparada para integrar eCommerce y Verifactu en el futuro."
                ),
                "asociado": "Asociado con Blau360",
            },
            {
                "titulo": "Desarrollo Web Personalizado para Restaurant Instint Granollers: Vite + Tailwind CSS",
                "fechas": "may. 2026 – jun. 2026",
                "descripcion": (
                    "Creación de la web oficial del Restaurant Instint Granollers desde cero, "
                    "utilizando Vite y Tailwind CSS. Diseño moderno, rápido y adaptado a las "
                    "necesidades del negocio, con un enfoque en la experiencia de usuario."
                ),
                "asociado": "Asociado con Blau360",
            },
        ]
        aptitudes = [
            "Desarrollo front end",
            "JavaScript",
            "Tailwind CSS",
            "Desarrollo web",
            "Desarrollo de aplicaciones web",
            "Sistemas de facturación",
            "Java",
            "Desarrollo de Android",
            "Administración de sistemas Linux",
            "Python",
            "Reparación de equipos informáticos",
            "Diagnóstico de ordenadores",
            "Edición de audio",
            "Diseño web",
            "Manipulación de alimentos",
            "WordPress",
            "Verifactu",
            "Firma electrónica",
        ]

    datos = {
        "perfil": perfil,
        "servicios": servicios,
        "experiencia": experiencia,
        "educacion": educacion,
        "certificaciones": certificaciones,
        "proyectos": proyectos,
        "aptitudes": aptitudes,
        "meta": {
            "fuente": fuente,
            "actualizado": datetime.now().isoformat(),
            "url": PROFILE_URL,
        },
    }

    with open("portfolio.json", "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=2)

    print(f"  → portfolio.json generado ({fuente})")
    print(f"    Perfil: {datos['perfil']['nombre']}")
    print(f"    Experiencias: {len(datos['experiencia'])}")
    print(f"    Proyectos: {len(datos['proyectos'])}")
    print(f"    Aptitudes: {len(datos['aptitudes'])}")


if __name__ == "__main__":
    main()
