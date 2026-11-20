"""Dibuja la portada de Backpack Pro (fondo del menú de pausa) en pixel art, sin librerías.

Uso:  python portada.py   ->  portada/backpack_pro_portada.png
"""
import os, struct, zlib

AQUI = os.path.dirname(os.path.abspath(__file__))
ANCHO, ALTO = 640, 360

# Letras de 5x7 (estilo Minecraft)
FUENTE = {
    "A": ["01110", "10001", "10001", "11111", "10001", "10001", "10001"],
    "B": ["11110", "10001", "10001", "11110", "10001", "10001", "11110"],
    "C": ["01111", "10000", "10000", "10000", "10000", "10000", "01111"],
    "D": ["11110", "10001", "10001", "10001", "10001", "10001", "11110"],
    "E": ["11111", "10000", "10000", "11110", "10000", "10000", "11111"],
    "K": ["10001", "10010", "10100", "11000", "10100", "10010", "10001"],
    "O": ["01110", "10001", "10001", "10001", "10001", "10001", "01110"],
    "P": ["11110", "10001", "10001", "11110", "10000", "10000", "10000"],
    "R": ["11110", "10001", "10001", "11110", "10100", "10010", "10001"],
    "U": ["10001", "10001", "10001", "10001", "10001", "10001", "01110"],
    "@": ["01110", "10001", "10111", "10101", "10111", "10000", "01111"],
    " ": ["00000"] * 7,
}

MOCHILA = [  # 16x16
    "....RRRRRRRR....",
    "...R########R...",
    "....RRRRRRRR....",
    "...##########...",
    "..#CCCCCCCCCC#..",
    "..#CddCCCCddC#..",
    "..#CddCCCCddC#..",
    "..#CddCCCCddC#..",
    "..#Cdd####ddC#..",
    "..#Cdd#gg#ddC#..",
    "..#Cdd#gg#ddC#..",
    "..#Cdd####ddC#..",
    "..#CddCCCCddC#..",
    "..#CCCCCCCCCC#..",
    "...##########...",
    "................",
]
COLORES = {"#": (40, 24, 18), "C": (232, 120, 82), "d": (150, 70, 45), "R": (120, 80, 48), "g": (230, 190, 70)}


def nuevo():
    px = []
    for y in range(ALTO):
        t = y / (ALTO - 1)
        arriba, abajo = (34, 22, 30), (120, 52, 38)
        px.append([tuple(round(a + (b - a) * t) for a, b in zip(arriba, abajo)) for _ in range(ANCHO)])
    return px


def rect(px, x, y, w, h, color):
    for j in range(max(0, y), min(ALTO, y + h)):
        for i in range(max(0, x), min(ANCHO, x + w)):
            px[j][i] = color


def texto(px, s, x, y, escala, color, sombra=(20, 12, 10)):
    for desplazamiento, c in ((escala // 2 or 1, sombra), (0, color)):
        cx = x + desplazamiento
        for letra in s:
            for fila, bits in enumerate(FUENTE[letra]):
                for col, b in enumerate(bits):
                    if b == "1":
                        rect(px, cx + col * escala, y + desplazamiento + fila * escala, escala, escala, c)
            cx += 6 * escala


def ancho_texto(s, escala):
    return len(s) * 6 * escala - escala


def png(px):
    datos = b"".join(b"\x00" + bytes(c for p in fila for c in p) for fila in px)
    def bloque(t, d):
        return struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d))
    return (b"\x89PNG\r\n\x1a\n" + bloque(b"IHDR", struct.pack(">IIBBBBB", ANCHO, ALTO, 8, 2, 0, 0, 0))
            + bloque(b"IDAT", zlib.compress(datos, 9)) + bloque(b"IEND", b""))


def main():
    px = nuevo()
    # Mochila grande a la izquierda
    escala = 12
    ox, oy = 40, (ALTO - 16 * escala) // 2
    for j, fila in enumerate(MOCHILA):
        for i, c in enumerate(fila):
            if c in COLORES:
                rect(px, ox + i * escala, oy + j * escala, escala, escala, COLORES[c])
    # Título y firma a la derecha
    x0 = 260
    texto(px, "BACKPACK", x0, 110, 7, (255, 214, 120))
    texto(px, "PRO", x0 + (ancho_texto("BACKPACK", 7) - ancho_texto("PRO", 7)) // 2, 175, 7, (255, 150, 100))
    texto(px, "@ROUDRE", x0 + (ancho_texto("BACKPACK", 7) - ancho_texto("@ROUDRE", 4)) // 2, 250, 4, (245, 235, 220))
    os.makedirs(os.path.join(AQUI, "portada"), exist_ok=True)
    with open(os.path.join(AQUI, "portada", "backpack_pro_portada.png"), "wb") as f:
        f.write(png(px))
    print("Listo: portada/backpack_pro_portada.png")


assert all(len(f) == 16 for f in MOCHILA) and all(len(r) == 5 for l in FUENTE.values() for r in l)

if __name__ == "__main__":
    main()
