# 🌅 Sereno: visuales cálidas y tranquilas

Resource pack para Minecraft Bedrock que hace el mundo más bonito **sin Vibrant Visuals ni shaders**. Corre en celulares de gama baja.

| Antes (vanilla) | Con Sereno |
|---|---|
| Cielo azul muy saturado | Azul suave y natural en todos los biomas de superficie |
| Horizonte que se corta de golpe | Bruma cálida que empieza al 70% de la distancia, como en un atardecer |
| Lluvia gris oscura | Lluvia más suave |
| Agua de colores fuertes | Agua turquesa tranquila que conserva el estilo de cada bioma |
| Bajo el agua se ve poco | Se ve un 35% más lejos |
| Sol cuadrado | Sol redondo con un halo cálido |

El Nether, el End y el Jardín Pálido se dejan como están, para que no pierdan su ambiente.

## Instalar
1. Descarga [`Sereno.mcpack`](Sereno.mcpack).
2. Ábrelo con Minecraft: se importa solo.
3. En **Configuración → Recursos globales**, activa **Sereno**.

Funciona en Android, iOS, Windows y consolas, con Minecraft Bedrock 1.21.120 o más nuevo.

## Cómo está hecho
`build.py` baja los biomas y nieblas oficiales de Mojang ([bedrock-samples v1.26.60](https://github.com/Mojang/bedrock-samples)), les aplica la paleta, dibuja el sol y el ícono pixel por pixel (sin librerías) y empaqueta el `.mcpack`. Para cambiar los colores, edita la paleta al inicio del archivo y corre:

```bash
python build.py
```
