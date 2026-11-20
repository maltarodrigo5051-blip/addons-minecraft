"""Saca el player.entity.json del propio Minecraft instalado (paquete .brarchive) y lo guarda en
vanilla/. Es la base que usa parchar.py para el jugador, así queda igual que el juego real.

Uso:  python extraer_jugador.py "<ruta al entity.brarchive>"
"""
import json, os, sys

AQUI = os.path.dirname(os.path.abspath(__file__))
texto = open(sys.argv[1], "rb").read().decode("utf-8", "replace")
marca = '"identifier":"minecraft:player"'
i = texto.find(marca)
assert i > 0, "no encontré al jugador en el paquete"
inicio = texto.rfind('{"format_version"', 0, i)

profundidad, fin, en_texto, escape = 0, None, False, False
for k in range(inicio, len(texto)):
    c = texto[k]
    if en_texto:
        if escape:
            escape = False
        elif c == "\\":
            escape = True
        elif c == '"':
            en_texto = False
    elif c == '"':
        en_texto = True
    elif c == "{":
        profundidad += 1
    elif c == "}":
        profundidad -= 1
        if profundidad == 0:
            fin = k + 1
            break

datos = json.loads(texto[inicio:fin])
d = datos["minecraft:client_entity"]["description"]
assert d["identifier"] == "minecraft:player"
define_lanza = any("melee_spear_equipped" in x for x in d["scripts"].get("pre_animation", []) if isinstance(x, str))
print("format", datos["format_version"], "| animaciones", len(d["animations"]), "| define la variable de la lanza:", define_lanza)
with open(os.path.join(AQUI, "vanilla", "player.entity.json"), "w", encoding="utf-8") as f:
    json.dump(datos, f, indent=2, ensure_ascii=False)
print("guardado vanilla/player.entity.json")
