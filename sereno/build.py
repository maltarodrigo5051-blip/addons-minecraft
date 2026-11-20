"""Genera el resource pack "Sereno" para Minecraft Bedrock.

Baja los biomas y nieblas oficiales de Mojang (bedrock-samples), les aplica un estilo
realista, cálido y tranquilo, dibuja el sol y el ícono, y empaqueta Sereno.mcpack.
No usa Vibrant Visuals ni shaders: corre en celulares de gama baja.

Uso:  python build.py
"""
import json, os, struct, urllib.request, uuid, zipfile, zlib, math

VANILLA = "https://raw.githubusercontent.com/Mojang/bedrock-samples/v1.26.60.5/resource_pack/"
TREE = "https://api.github.com/repos/Mojang/bedrock-samples/git/trees/v1.26.60.5?recursive=1"
AQUI = os.path.dirname(os.path.abspath(__file__))
PACK = os.path.join(AQUI, "Sereno")
VERSION = [1, 0, 0]

# --- Paleta -------------------------------------------------------------------
NEBLINA = "#D9D2C4"       # bruma cálida del horizonte (de día)
CIELO = "#8DB3DA"         # azul suave, menos saturado que el vanilla
LLUVIA = "#77797D"        # niebla de lluvia más suave
AGUA = "#3A90B2"          # agua turquesa tranquila
FOG_INICIO = 0.70         # la bruma empieza al 70% de la distancia de renderizado
AGUA_MAS_CLARA = 1.35     # se ve 35% más lejos bajo el agua

NO_SUPERFICIE = ("nether", "hell", "crimson", "warped", "soulsand", "basalt", "the_end", "pale_garden")


def hex_a_rgb(h):
    h = h.lstrip("#")
    return [int(h[i:i + 2], 16) for i in (0, 2, 4)]


def mezclar(color, hacia, t):
    """Mezcla dos colores #rrggbb; t=0 deja el original, t=1 da 'hacia'."""
    a, b = hex_a_rgb(color), hex_a_rgb(hacia)
    return "#" + "".join(f"{round(x + (y - x) * t):02X}" for x, y in zip(a, b))


def bajar(ruta):
    with urllib.request.urlopen(VANILLA + ruta) as r:
        return json.loads(r.read().decode("utf-8"))


def lista_vanilla():
    with urllib.request.urlopen(TREE) as r:
        arbol = json.loads(r.read())["tree"]
    rutas = [x["path"].removeprefix("resource_pack/") for x in arbol if x["type"] == "blob"]
    return ([p for p in rutas if p.startswith("biomes/")], [p for p in rutas if p.startswith("fogs/")])


# --- Nieblas -------------------------------------------------------------------
def ajustar_niebla(j):
    d = j["minecraft:fog_settings"].get("distance", {})
    aire = d.get("air")
    # Solo nieblas de superficie normales (las del Nether usan "fixed" y colores propios).
    if aire and aire.get("render_distance_type") == "render" and aire.get("fog_color", "").upper() == "#ABD2FF":
        aire.update(fog_start=FOG_INICIO, fog_end=1.0, fog_color=NEBLINA)
        if "weather" in d:
            d["weather"].update(fog_start=0.15, fog_end=0.6, fog_color=LLUVIA)
    agua = d.get("water")
    if agua:
        agua["fog_end"] = round(agua["fog_end"] * AGUA_MAS_CLARA, 1)
        agua["fog_color"] = mezclar(agua["fog_color"], AGUA, 0.25)
        inicio = agua.get("transition_fog", {}).get("init_fog")
        if inicio:
            inicio["fog_color"] = agua["fog_color"]
    return j


# --- Biomas --------------------------------------------------------------------
def ajustar_bioma(j):
    b = j["minecraft:client_biome"]
    ident, comp = b["description"]["identifier"], b["components"]
    agua = comp.get("minecraft:water_appearance")
    if agua and "surface_color" in agua:
        agua["surface_color"] = mezclar(agua["surface_color"], AGUA, 0.30)
    if not any(n in ident for n in NO_SUPERFICIE):
        comp["minecraft:sky_color"] = {"sky_color": CIELO}
    return j


# --- PNG sin librerías ---------------------------------------------------------
def guardar_png(ruta, ancho, alto, pixel):
    """pixel(x, y) -> (r, g, b, a) con valores 0-255."""
    filas = b"".join(
        b"\x00" + bytes(c for x in range(ancho) for c in pixel(x, y)) for y in range(alto)
    )
    def bloque(tipo, datos):
        return struct.pack(">I", len(datos)) + tipo + datos + struct.pack(">I", zlib.crc32(tipo + datos))
    png = b"\x89PNG\r\n\x1a\n" + bloque(b"IHDR", struct.pack(">IIBBBBB", ancho, alto, 8, 6, 0, 0, 0))
    png += bloque(b"IDAT", zlib.compress(filas, 9)) + bloque(b"IEND", b"")
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    with open(ruta, "wb") as f:
        f.write(png)


def sol(x, y, n=64):
    """Disco cálido con un halo suave.

    El sol de Bedrock se dibuja sumando luz: el negro es invisible, así que el halo
    se desvanece hacia negro (alfa siempre 255), igual que el sun.png original.
    """
    r = math.hypot(x + 0.5 - n / 2, y + 0.5 - n / 2) / (n / 2)
    if r < 0.32:
        return (255, 240, 205, 255)
    brillo = max(0.0, 1 - (r - 0.32) / 0.68) ** 2.2
    return (round(255 * brillo), round(205 * brillo), round(140 * brillo), 255)


def icono(x, y, n=128):
    """Atardecer: cielo azul suave que baja a naranja, con el sol en el horizonte."""
    t = y / (n - 1)
    arriba, abajo = hex_a_rgb(CIELO), hex_a_rgb("#F2B27A")
    c = [round(a + (b - a) * t) for a, b in zip(arriba, abajo)]
    d = math.hypot(x - n / 2, y - n * 0.68) / n
    if d < 0.16:
        luz = 1 - d / 0.16
        c = [round(v + (w - v) * luz) for v, w in zip(c, (255, 236, 200))]
    if y > n * 0.78:  # suelo
        c = hex_a_rgb("#5A7A3E")
    return (*c, 255)


def manifest():
    # UUID fijos (derivados del nombre) para que al actualizar el pack no se duplique.
    base = uuid.uuid5(uuid.NAMESPACE_URL, "github.com/maltarodrigo5051-blip/addons-minecraft/sereno")
    return {
        "format_version": 2,
        "header": {
            "name": "Sereno",
            "description": "Visuales realistas, cálidas y tranquilas. Sin Vibrant Visuals.",
            "uuid": str(uuid.uuid5(base, "header")),
            "version": VERSION,
            "min_engine_version": [1, 21, 120],
        },
        "modules": [{"type": "resources", "uuid": str(uuid.uuid5(base, "resources")), "version": VERSION}],
    }


def main():
    # Se sobrescribe en vez de borrar la carpeta: OneDrive a veces la bloquea.
    biomas, nieblas = lista_vanilla()
    assert len(biomas) > 50 and len(nieblas) > 50, "no se pudo leer el pack oficial"

    for ruta, ajustar in [(p, ajustar_bioma) for p in biomas] + [(p, ajustar_niebla) for p in nieblas]:
        destino = os.path.join(PACK, ruta)
        os.makedirs(os.path.dirname(destino), exist_ok=True)
        with open(destino, "w", encoding="utf-8") as f:
            json.dump(ajustar(bajar(ruta)), f, indent=2, ensure_ascii=False)

    guardar_png(os.path.join(PACK, "textures/environment/sun.png"), 64, 64, sol)
    guardar_png(os.path.join(PACK, "pack_icon.png"), 128, 128, icono)
    with open(os.path.join(PACK, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest(), f, indent=2, ensure_ascii=False)

    salida = os.path.join(AQUI, "Sereno.mcpack")
    with zipfile.ZipFile(salida, "w", zipfile.ZIP_DEFLATED) as z:
        for raiz, _, archivos in os.walk(PACK):
            for a in archivos:
                completo = os.path.join(raiz, a)
                z.write(completo, os.path.relpath(completo, PACK))
    print(f"Listo: {salida} ({len(biomas)} biomas, {len(nieblas)} nieblas)")


def autoprueba():
    assert mezclar("#000000", "#FFFFFF", 0.5) == "#808080"
    assert mezclar("#123456", "#ABCDEF", 0) == "#123456"
    j = {"minecraft:fog_settings": {"distance": {"air": {"fog_start": 0.92, "fog_end": 1.0, "fog_color": "#ABD2FF", "render_distance_type": "render"}}}}
    assert ajustar_niebla(j)["minecraft:fog_settings"]["distance"]["air"]["fog_color"] == NEBLINA
    nether = {"minecraft:fog_settings": {"distance": {"air": {"fog_start": 10.0, "fog_end": 96.0, "fog_color": "#330808", "render_distance_type": "fixed"}}}}
    assert ajustar_niebla(nether)["minecraft:fog_settings"]["distance"]["air"]["fog_color"] == "#330808"
    b = {"minecraft:client_biome": {"description": {"identifier": "minecraft:hell"}, "components": {}}}
    assert "minecraft:sky_color" not in ajustar_bioma(b)["minecraft:client_biome"]["components"]
    assert sol(0, 0) == (0, 0, 0, 255), "las esquinas del sol deben ser negras (invisibles)"


if __name__ == "__main__":
    autoprueba()
    main()
