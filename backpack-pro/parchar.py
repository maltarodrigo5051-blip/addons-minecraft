"""Backpack Pro (@Roudre): mochilas para Minecraft Bedrock, inspiradas en Sophisticated
Backpacks (Java), con un almacenamiento que no pierde objetos.

Parte de un add-on de mochilas para Bedrock que ya existía (scripts-original/, intocable) y le
aplica los cambios de este proyecto:
- Database.js (de esta carpeta) reemplaza a su base de datos, con la misma forma de uso.
- main.js lleva parches mínimos y exactos (viene ofuscado).
- Jugador al día con la 1.26, interfaz arreglada, todo en español y música libre (CC0).
Cada parche exige encontrar su texto exactamente una vez; si no, se detiene sin escribir nada.

Uso:  python parchar.py   ->  Backpack Pro.mcaddon
"""
import json, os, re, shutil, zipfile

AQUI = os.path.dirname(os.path.abspath(__file__))
ORIGINAL = os.path.join(AQUI, "scripts-original")
SCRIPTS = os.path.join(AQUI, "BP", "scripts")
NOMBRE = "Backpack Pro"
FIRMA = "@Roudre - Tus cosas siempre a salvo"
VERSION = [1, 0, 13]  # súbela en cada cambio: si se repite, Minecraft no reemplaza el add-on al importarlo
# UUID del add-on de base -> UUID propios de Backpack Pro (fijos: si cambian, los mundos dejan de
# reconocer el add-on). Los IDs de los ítems (backpack:...) NO se tocan: si cambiaran, las mochilas
# que ya existen desaparecerían.
UUID_PROPIOS = {
    "f8110a4f-7180-4404-8ef9-8a951eef70ac": "5fd82459-adae-53ce-9d58-9cd34a3bf8c7",
    "5cdded47-1d6c-4cb7-8357-10989caf8dd6": "4aa00236-4c14-5301-b9d9-03c43c6a2642",
    "315b8080-e406-4af5-b500-6c247a109d93": "8c023f1a-f68b-5ddc-81ec-0341dc0dd7c7",
    "de208ae7-7f7b-470a-ab5e-3c6cc79541a4": "a5e7780c-06e6-509a-bb2f-e1f82572121f",
    "3741222f-c538-4005-9b42-d7dbc31ea68c": "27bc45e0-5302-5eb4-ac72-ddc79c0d8273",
}

PARCHES_MAIN = [
    (
        "1. La optimización de cada 8 minutos ya no cierra mochilas abiertas ni las que tienen un jugador cerca",
        "if(!_0x5a4d22){const _0x1affd1=",
        "if(!_0x5a4d22&&!_0x458dd5.getTags().includes('open')&&_0x458dd5.dimension.getPlayers({location:_0x458dd5.location,maxDistance:8}).length===0){const _0x1affd1=",
    ),
    (
        "2. Si una mochila no tiene ID, sus objetos caen al suelo en vez de borrarse",
        "else _0x516163['remove'](),console[_0x3ab8e0(0x1cb)](_0x3ab8e0(0x1c1)),world['sendMessage']('§c[Warning]\\x20Backpack\\x20removed:\\x20The\\x20ID\\x20of\\x20some\\x20inactive\\x20backpacks\\x20was\\x20not\\x20correctly\\x20identified\\x20and\\x20the\\x20items\\x20were\\x20not\\x20saved.');}",
        "else{const _inv=_0x516163.getComponent('inventory')?.container;if(_inv)for(let _i=0;_i<_inv.size;_i++){const _it=_inv.getItem(_i);if(_it)_0x516163.dimension.spawnItem(_it,_0x516163.location);}_0x516163['remove']();console.warn('[Backpack Pro] Mochila sin ID: sus objetos se tiraron al suelo para no perderlos.');}}",
    ),
    (
        "2b. Mensaje del chat en español",
        "'§a[Backpack]\\x20Optimizing\\x20Backpack...'",
        "'§a[Backpack\\x20Pro]\\x20Guardando\\x20mochilas...'",
    ),
    # 3. lockMode ya no acepta true/false (las versiones nuevas exigen ItemLockMode): "slot" o "none".
    ("3a. Bloquear la mochila abierta con 'slot'", "_0x4ba42a['lockMode']=!![]", "_0x4ba42a['lockMode']='slot'"),
    ("3b. Desbloquear con 'none'", "_0x4ba42a[_0x5aa8ef(0x215)]=![]", "_0x4ba42a[_0x5aa8ef(0x215)]='none'"),
    ("3c. Desbloquear con 'none'", "_0x33980f['lockMode']=![]", "_0x33980f['lockMode']='none'"),
]


def leer(ruta):
    with open(ruta, "rb") as f:
        return f.read().decode("utf-8")


def escribir(ruta, texto):
    with open(ruta, "wb") as f:
        f.write(texto.encode("utf-8"))


def cargar_json(ruta):
    """JSON de Minecraft: admite comentarios de línea (//)."""
    return json.loads(re.sub(r"(?m)^\s*//.*$", "", leer(ruta)))


def respaldo(ruta_relativa):
    """Guarda una vez el archivo original en originales/ y devuelve esa ruta."""
    destino = os.path.join(AQUI, "originales", ruta_relativa)
    if not os.path.exists(destino):
        os.makedirs(os.path.dirname(destino), exist_ok=True)
        shutil.copy(os.path.join(AQUI, ruta_relativa), destino)
    return destino


def unir_jugador():
    """El pack original reemplazaba al jugador con archivos de la 1.21.0, a los que les faltan
    animaciones y componentes nuevos (errores de 'can't find animation' y 'melee_spear').
    Se parte del jugador actual de Minecraft (vanilla/, bedrock-samples v1.26.60) y se le agrega
    solo lo que el pack puso para la mochila."""
    # Comportamiento: lo de Minecraft + las propiedades de la mochila
    pack = cargar_json(respaldo(os.path.join("BP", "entities", "player.json")))
    base = cargar_json(os.path.join(AQUI, "vanilla", "player.json"))
    base["minecraft:entity"]["description"]["properties"] = pack["minecraft:entity"]["description"]["properties"]
    escribir(os.path.join(AQUI, "BP", "entities", "player.json"), json.dumps(base, indent=2, ensure_ascii=False))

    # Dibujo: lo de Minecraft + texturas, modelos, animaciones y controladores de la mochila
    pack = cargar_json(respaldo(os.path.join("RP", "entity", "player.entity.json")))["minecraft:client_entity"]["description"]
    base = cargar_json(os.path.join(AQUI, "vanilla", "player.entity.json"))
    d = base["minecraft:client_entity"]["description"]
    for campo in ("textures", "geometry", "animations", "materials"):
        for k, v in pack.get(campo, {}).items():
            d.setdefault(campo, {}).setdefault(k, v)
    d["render_controllers"] += [rc for rc in pack.get("render_controllers", []) if rc not in d["render_controllers"]]
    s, sa = d.setdefault("scripts", {}), pack.get("scripts", {})
    for campo in ("animate", "pre_animation", "initialize"):
        s[campo] = s.get(campo, []) + [x for x in sa.get(campo, []) if x not in s.get(campo, [])]
    escribir(os.path.join(AQUI, "RP", "entity", "player.entity.json"), json.dumps(base, indent=2, ensure_ascii=False))
    print("OK 5. Jugador actualizado a la 1.26 con las partes de la mochila")

    # El bloque de mochila apuntaba a "backpack.json" (ruta inválida). La intención era no soltar
    # nada (el script devuelve la mochila), y eso es la tabla vacía oficial.
    bloque = leer(respaldo(os.path.join("BP", "blocks", "backpack.json")))
    assert bloque.count('"minecraft:loot": "backpack.json"') == 1, "no encontré el botín del bloque"
    escribir(os.path.join(AQUI, "BP", "blocks", "backpack.json"),
             bloque.replace('"minecraft:loot": "backpack.json"', '"minecraft:loot": "loot_tables/empty.json"'))
    print("OK 6. Bloque de mochila con botín válido (vacío)")

    # La barra con la X para cerrar heredaba de "crafting.crafting_root_panel", que cambió en la
    # 1.26 (error "Unknown properties ... toolbar_panel"): la X no aparecía y la mochila no cerraba.
    # Ahora es un panel propio con el mismo botón de cerrar de Minecraft.
    ui = leer(respaldo(os.path.join("RP", "ui", "backpack_screen.json")))
    antes = '"toolbar_panel@crafting.crafting_root_panel": {'
    assert ui.count(antes) == 1, "no encontré la barra de la X"
    escribir(os.path.join(AQUI, "RP", "ui", "backpack_screen.json"), ui.replace(antes, '"toolbar_panel": {\n\t\t"type": "panel",'))
    print("OK 7. Botón X para cerrar la mochila")

    # Créditos del menú de pausa: solo @Roudre y el creador del mod original de Java.
    pausa = leer(respaldo(os.path.join("RP", "ui", "pause_screen.json")))
    creditos = (
        "§lBackpack Pro§r\\npor §b@Roudre§r\\n \\n"
        "Mochilas para Minecraft Bedrock con un almacenamiento nuevo que guarda tus cosas "
        "al instante y no las pierde.\\n \\n"
        "§gInspiración:§r\\nBasado en Sophisticated Backpacks (Java Edition), de §d@P3pp3rF1y§r."
    )
    lineas = pausa.split("\n")
    i = next(k for k, l in enumerate(lineas) if "Créditos:" in l and '"text"' in l)
    lineas[i] = re.sub(r'("text"\s*:\s*)".*"', lambda m: m.group(1) + '"' + creditos + '"', lineas[i], count=1)
    pausa = "\n".join(lineas)
    assert "owner |" not in pausa, "quedaron los créditos viejos"
    escribir(os.path.join(AQUI, "RP", "ui", "pause_screen.json"), pausa)
    print("OK 8. Créditos: @Roudre y @P3pp3rF1y")

    # Portada propia (portada.py) en lugar de la imagen con el nombre del add-on de base
    shutil.copy(os.path.join(AQUI, "portada", "backpack_pro_portada.png"), os.path.join(AQUI, "RP", "textures", "backpack_pro_portada.png"))
    borrar(os.path.join("RP", "textures", "sophisticangel_backpack.png"))
    pausa = leer(os.path.join(AQUI, "RP", "ui", "pause_screen.json"))
    assert pausa.count('"textures/sophisticangel_backpack"') == 1, "no encontré la portada vieja"
    escribir(os.path.join(AQUI, "RP", "ui", "pause_screen.json"), pausa.replace('"textures/sophisticangel_backpack"', '"textures/backpack_pro_portada"'))
    print("OK 8b. Portada Backpack Pro")


SKINS_QUITADAS = ["jaar", "manolo"]  # skins con nombres de personas: se quitaron a pedido


def borrar(ruta_relativa):
    """Respalda en originales/ y borra el archivo del add-on."""
    if os.path.exists(os.path.join(AQUI, ruta_relativa)):
        respaldo(ruta_relativa)
        os.remove(os.path.join(AQUI, ruta_relativa))


def quitar_skins():
    ids = {f"skin:bp_{s}" for s in SKINS_QUITADAS}
    for s in SKINS_QUITADAS:
        borrar(os.path.join("BP", "items", "6_skins_bp", f"{s}.json"))
        borrar(os.path.join("RP", "textures", "atta", "bp_skins", f"{s}.png"))
        borrar(os.path.join("RP", "textures", "items", "skins", f"{s}.png"))

    # Ya no salen en los cofres de la Ciudad Antigua
    ruta = os.path.join("BP", "loot_tables", "chests", "ancient_city.json")
    botin = cargar_json(respaldo(ruta))
    for pool in botin.get("pools", []):
        pool["entries"] = [e for e in pool.get("entries", []) if e.get("name") not in ids]
    escribir(os.path.join(AQUI, ruta), json.dumps(botin, indent=2, ensure_ascii=False))

    # Íconos
    ruta = os.path.join("RP", "textures", "item_texture.json")
    iconos = cargar_json(respaldo(ruta))
    for s in SKINS_QUITADAS:
        iconos["texture_data"].pop(f"bp_skin_{s}", None)
    escribir(os.path.join(AQUI, ruta), json.dumps(iconos, indent=2, ensure_ascii=False))

    # Lista de skins del script
    exp = os.path.join(SCRIPTS, "exports.js")
    texto = leer(exp)
    texto = "\n".join(l for l in texto.split("\n") if not any(f'"{i}"' in l for i in ids))
    escribir(exp, texto)

    # El dibujo usa la posición de cada skin (12 y 13): se dejan apuntando a la base para no
    # correr las demás. Ya nadie puede conseguirlas, así que nunca se usan.
    for ruta in (os.path.join("RP", "entity", "backpack.entity.json"), os.path.join("RP", "entity", "player.entity.json")):
        origen = os.path.join(AQUI, ruta) if ruta.endswith("player.entity.json") else respaldo(ruta)
        datos = cargar_json(origen)
        tex = datos["minecraft:client_entity"]["description"]["textures"]
        for s in SKINS_QUITADAS:
            if f"bps_{s}" in tex:
                tex[f"bps_{s}"] = "textures/atta/bp_base"
        escribir(os.path.join(AQUI, ruta), json.dumps(datos, indent=2, ensure_ascii=False))

    # Ni el nombre interno queda: bps_jaar / bps_manolo pasan a bps_libre_12 / bps_libre_13.
    nuevos = {"bps_jaar": "bps_libre_12", "bps_manolo": "bps_libre_13"}
    for ruta in (os.path.join("RP", "entity", "backpack.entity.json"), os.path.join("RP", "entity", "player.entity.json"),
                 os.path.join("RP", "render_controllers", "backpack_controller.json")):
        origen = respaldo(ruta) if ruta.endswith("backpack_controller.json") else os.path.join(AQUI, ruta)
        texto = leer(origen)
        for viejo, nuevo in nuevos.items():
            texto = texto.replace(viejo, nuevo)
        escribir(os.path.join(AQUI, ruta), texto)
    print("OK 9. Skins de Manolo y Jaar quitadas")


# Música libre (CC0, opengameart.org) en lugar de las canciones con derechos de autor del original.
# Cada canción se identifica por su NOMBRE en tres lugares que tienen que coincidir: el sonido
# (sound_definitions.json), el nombre del disco (BP/items) y la pantalla ($sound_event).
DISCOS = [  # (nombre original, nombre nuevo) para music_1 ... music_8 (archivos en musica/)
    ("I have no enemies", "Snowfall"),
    ("The Rare Occasions - Notion", "Desert Theme"),
    ("Roi", "Breves Dies Hominis"),
    ("Call Me", "Boss Battle Theme"),
    ("Heart to heart", "Night Prowler"),
    ("Tek it", "Prepare Your Swords"),
    ("Metro Boomin - Space Cadet", "Cave Theme"),
    ("Undertale OST 085 - Fallen Down", "Nevada (bucle)"),  # en el original este archivo no existía
]


def musica_libre():
    carpeta = os.path.join("RP", "sounds", "music_backpack")
    for i in range(1, len(DISCOS) + 1):
        borrar(os.path.join(carpeta, f"music_{i}.ogg"))  # respalda la canción original (no va a GitHub)
        shutil.copy(os.path.join(AQUI, "musica", f"music_{i}.ogg"), os.path.join(AQUI, carpeta, f"music_{i}.ogg"))

    def renombrar(texto):
        for viejo, nuevo in DISCOS:
            texto = texto.replace(f'"{viejo}"', f'"{nuevo}"').replace(f'§9{viejo}"', f'§9{nuevo}"')
        return texto

    ruta = os.path.join("RP", "sounds", "sound_definitions.json")
    escribir(os.path.join(AQUI, ruta), renombrar(leer(respaldo(ruta))))
    escribir(os.path.join(AQUI, "RP", "ui", "backpack_screen.json"), renombrar(leer(os.path.join(AQUI, "RP", "ui", "backpack_screen.json"))))
    for i in range(1, len(DISCOS) + 1):
        ruta = os.path.join("BP", "items", "4_music", f"music{i}.json")
        if os.path.exists(os.path.join(AQUI, ruta)):
            escribir(os.path.join(AQUI, ruta), renombrar(leer(os.path.join(AQUI, ruta))))
    print("OK 11. Música libre (CC0) en los 8 discos")


NOMBRES_ES = [  # (texto original, en español) dentro de los nombres de los ítems
    ("Aditamento Base Backpack", "Base de mejora para mochila"),
    ("Aditamento Backpack\\n§r§7addition: §9", "Mejora de mochila\\n§r§7Mejora: §9"),
    ("Aquatic Breathing", "Respiración acuática"), ("AutoTransfer Items", "Transferencia automática"),
    ("Container Liquid", "Tanque de líquidos"), ("Dynamic Torch", "Antorcha dinámica"),
    ("Extra Hearts", "Corazones extra"), ("Food Auto", "Comida automática"),
    ("Item Magnet level 2", "Imán de objetos nivel 2"), ("Item Magnet", "Imán de objetos"),
    ("Mining Speed", "Minería rápida"), ("More Strength", "Más fuerza"),
    ("Portable Farming", "Cultivo portátil"), ("Portable Furnace level 2", "Horno portátil nivel 2"),
    ("Portable Furnace", "Horno portátil"), ("Portable Jukebox", "Tocadiscos portátil"),
    ("insert backpacks", "Guardar mochilas y shulkers"),
    ("Backpack Upgrade", "BACKPACK_UPGRADE"),  # se arma abajo: "Mejora a mochila de ..."
    ("Disc Music Backpack", "Disco de música"),
    ("Skin Backpack", "Skin de mochila"), ("Snow Golem", "Gólem de nieve"), ("Iron Golem", "Gólem de hierro"),
    ("Bear", "Oso"), ("Fox", "Zorro"), ("Pig", "Cerdo"), ("Axolotl", "Ajolote"),
    ("§1C§2u§3s§4t§5o§6m §qC§eo§rl§to§ur§ps", "§6Colores personalizados"),
    ("Lava Liquid", "Lava"), ("Water Liquid", "Agua"),
]
MATERIALES_ES = {"Copper": "cobre", "Iron": "hierro", "Gold": "oro", "Diamond": "diamante", "Netherite": "netherite"}

UI_ES = {'"Config"': '"Configuración"', '"Craft [BETA]"': '"Crafteo [BETA]"', '"Crafting Backpacks"': '"Recetas de mochilas"',
         '"Credits Proyect Backpack"': '"Créditos"', '"Disc and Skins Backpacks"': '"Discos y skins"', '"JukeBox"': '"Tocadiscos"',
         '"farming"': '"cultivo"', '"food"': '"comida"', '"furnace"': '"horno"', '"magnet"': '"imán"'}


# La pantalla muestra la pestaña de cada mejora si el NOMBRE de un ítem contiene este texto.
# Tiene que coincidir con los nombres traducidos (si no, las pestañas desaparecen).
# La mesa de crafteo es la de Minecraft: en el juego en español se llama "Mesa de trabajo".
CONDICIONES_ES = {
    "Portable Furnace level 2": "Horno portátil nivel 2", "Portable Furnace": "Horno portátil",
    "Crafting Table": "Mesa de trabajo", "Container Liquid": "Tanque de líquidos",
    "Portable Jukebox": "Tocadiscos portátil", "Food Auto": "Comida automática",
    "Portable Farming": "Cultivo portátil", "Item Magnet level 2": "Imán de objetos nivel 2",
    "§1C§2u§3s§4t§5o§6m §qC§eo§rl§to§ur§ps": "Colores personalizados",  # skin de tintes
}


def nombre_es(valor):
    """Traduce un nombre de ítem como los muestra el add-on (mochilas, mejoras, skins...)."""
    for en, es in NOMBRES_ES + [("Fell Wood Auto", "Tala automática")]:
        valor = valor.replace(en, es)
    valor = re.sub(r"^(§7)?(Copper|Iron|Gold|Diamond|Netherite) BACKPACK_UPGRADE$",
                   lambda x: f"{x.group(1) or ''}Mejora a mochila de {MATERIALES_ES[x.group(2)]}", valor)
    valor = re.sub(r"^Backpack (copper|iron|gold|diamond|netherite)$",
                   lambda x: f"Mochila de {MATERIALES_ES[x.group(1).capitalize()]}", valor, flags=re.I)
    if valor in ("Backpack", "Backpack leather"):
        valor = "Mochila de cuero"
    return valor


def traducir():
    """Todo en español: nombres de ítems, botones de la pantalla, textos del juego y descripciones."""
    # Nombres de los ítems
    for carpeta, _, archivos in os.walk(os.path.join(AQUI, "BP", "items")):
        for a in archivos:
            ruta = os.path.relpath(os.path.join(carpeta, a), AQUI)
            texto = leer(respaldo(ruta))
            m = re.search(r'("value"\s*:\s*")([^"]*)(")', texto)
            if not m:
                continue
            valor = m.group(2)
            for en, es in NOMBRES_ES:
                valor = valor.replace(en, es)
            valor = re.sub(r"^(§7)?(Copper|Iron|Gold|Diamond|Netherite) BACKPACK_UPGRADE$",
                           lambda x: f"{x.group(1) or ''}Mejora a mochila de {MATERIALES_ES[x.group(2)]}", valor)
            valor = re.sub(r"^Backpack (Copper|Iron|Gold|Diamond|Netherite)$", lambda x: f"Mochila de {MATERIALES_ES[x.group(1)]}", valor)
            if valor == "Backpack":
                valor = "Mochila de cuero"
            escribir(os.path.join(AQUI, ruta), texto[:m.start(2)] + valor + texto[m.end(2):])

    # Botones de la pantalla de la mochila y del menú de pausa
    for a in os.listdir(os.path.join(AQUI, "RP", "ui")):
        ruta = os.path.join("RP", "ui", a)
        texto = leer(os.path.join(AQUI, ruta))  # ya parchado antes (X y créditos) o el original
        for en, es in UI_ES.items():
            texto = texto.replace(f'"text": {en}', f'"text": {es}')
        # Títulos de la mochila y nombres del menú de recetas (solo se muestran)
        texto = re.sub(r'("\$(?:text_backpack|hover_text_item)"\s*:\s*")([^"]*)(")',
                       lambda m: m.group(1) + nombre_es(m.group(2)) + m.group(3), texto)
        texto = texto.replace("' > Settings'", "' > Configuración'")
        for en, es in CONDICIONES_ES.items():
            texto = re.sub(rf'("\$container_source"\s*:\s*)"{re.escape(en)}"', lambda m: m.group(1) + f'"{es}"', texto)
            texto = texto.replace(f"'{en}'", f"'{es}'")
        escribir(os.path.join(AQUI, ruta), texto)

    # Textos del juego
    for idioma in ("es_MX", "es_ES"):
        ruta = os.path.join("RP", "texts", f"{idioma}.lang")
        texto = leer(respaldo(ruta)).replace("item.record.name=Music Disc", "item.record.name=Disco de música")
        texto = texto.replace("abrir la backpack", "abrir la mochila")
        escribir(os.path.join(AQUI, ruta), texto)

    # Descripciones de las mejoras: siempre las de español (antes dependían de un "subpack" que
    # pedía mucha memoria, y en equipos con poca salían en inglés o portugués).
    fuente = os.path.join(AQUI, "BP", "subpacks", "es_ES", "scripts", "lores.js")
    if not os.path.exists(fuente):
        fuente = os.path.join(AQUI, "originales", "BP", "subpacks", "es_ES", "scripts", "lores.js")
    shutil.copy(fuente, os.path.join(SCRIPTS, "lores.js"))
    if os.path.isdir(os.path.join(AQUI, "BP", "subpacks")):
        if not os.path.isdir(os.path.join(AQUI, "originales", "BP", "subpacks")):
            shutil.copytree(os.path.join(AQUI, "BP", "subpacks"), os.path.join(AQUI, "originales", "BP", "subpacks"))
        # OneDrive a veces bloquea la carpeta; si no se puede borrar, igual queda fuera del paquete.
        shutil.rmtree(os.path.join(AQUI, "BP", "subpacks"), ignore_errors=True)
    print("OK 10. Todo en español")


def main():
    unir_jugador()
    texto = leer(os.path.join(ORIGINAL, "main.js"))
    for nombre, antes, despues in PARCHES_MAIN:
        veces = texto.count(antes)
        assert veces == 1, f"main.js: el parche '{nombre}' encontró su texto {veces} veces (debe ser 1)"
        texto = texto.replace(antes, despues)
        print("OK", nombre)

    shutil.rmtree(SCRIPTS, ignore_errors=True)
    shutil.copytree(ORIGINAL, SCRIPTS, dirs_exist_ok=True)
    escribir(os.path.join(SCRIPTS, "main.js"), texto)
    shutil.copy(os.path.join(AQUI, "Database.js"), os.path.join(SCRIPTS, "API", "Database.js"))
    print("OK 4. Base de datos nueva sin pérdidas (Database.js)")
    quitar_skins()
    traducir()
    musica_libre()

    etiqueta = ".".join(map(str, VERSION))
    for pack in ("BP", "RP"):
        ruta = os.path.join(AQUI, pack, "manifest.json")
        m = leer(ruta)
        # Quita el comentario de broma del original (una línea con un link para adultos).
        m = "\n".join(linea for linea in m.split("\n") if "pornhub" not in linea)
        m = re.sub(r'"name":\s*"[^"]*v1\.0\.\d+ (?:BP|RP)"', f'"name": "{NOMBRE} v{etiqueta} {pack}"', m)
        m = re.sub(r'"description":\s*"@[^"]*"', f'"description": "{FIRMA}"', m)
        m = re.sub(r'"version":\s*\[\s*1,\s*0,\s*\d+\s*\]', f'"version": [ {VERSION[0]}, {VERSION[1]}, {VERSION[2]} ]', m)
        for viejo, nuevo in UUID_PROPIOS.items():
            m = m.replace(viejo, nuevo)
        # Solo español: sin selector de idioma (subpacks) ni sus textos en inglés y portugués.
        datos = json.loads(re.sub(r"(?m)^\s*//.*$", "", m))
        datos.pop("subpacks", None)
        datos.pop("settings", None)
        m = json.dumps(datos, indent=2, ensure_ascii=False)
        escribir(ruta, m)

    for viejo in os.listdir(AQUI):
        if viejo.endswith(".mcaddon"):
            os.remove(os.path.join(AQUI, viejo))
    salida = os.path.join(AQUI, f"{NOMBRE}.mcaddon")
    with zipfile.ZipFile(salida, "w", zipfile.ZIP_DEFLATED) as z:
        for pack in ("BP", "RP"):
            raiz = os.path.join(AQUI, pack)
            for carpeta, _, archivos in os.walk(raiz):
                if "subpacks" in os.path.relpath(carpeta, raiz).split(os.sep):
                    continue  # el selector de idioma ya no se usa: solo español
                for a in archivos:
                    completo = os.path.join(carpeta, a)
                    z.write(completo, os.path.join(f"{NOMBRE} {pack}", os.path.relpath(completo, raiz)))
    print("Listo:", salida)


if __name__ == "__main__":
    main()
