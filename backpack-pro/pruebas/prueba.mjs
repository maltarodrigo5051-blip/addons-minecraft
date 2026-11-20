import assert from "node:assert";
import { estado } from "@minecraft/server";
import fs from "node:fs";
// Se prueba el Database.js real del add-on, con un Minecraft simulado (node_modules/@minecraft/server).
fs.copyFileSync(new URL("../Database.js", import.meta.url), new URL("./Database.js", import.meta.url));
const { QuickItemDatabase } = await import("./Database.js");
const it = (t, n = 1) => ({ typeId: t, amount: n });
const tick = () => estado.intervalos.forEach((f) => f());

// 1) Guardar y leer
let db = new QuickItemDatabase("backpack");
db.set("inventory1", [it("diamante", 5), undefined, it("espada")]);
assert.equal(db.get("inventory1")[0].typeId, "diamante");
// Una base nueva (como al reiniciar el mundo) lee del almacén, no de la memoria
db = new QuickItemDatabase("backpack");
assert.deepEqual(db.get("inventory1").map((x) => x?.typeId), ["diamante", undefined, "espada"], "persiste tras reiniciar");

// 2) Mundo recién abierto: la zona no carga -> no inventa una mochila vacía
db = new QuickItemDatabase("backpack");
estado.lista = false;
assert.equal(db.get("inventory1"), undefined, "no devuelve vacío");
db.set("inventory1", [it("tierra", 64)]); // el jugador metió algo mientras tanto
assert.equal(estado.entidades.find((e) => e.tags.has("mm:backpack:inventory1")).caja.getItem(0).typeId, "diamante", "no pisó lo guardado");
estado.lista = true; tick();
const tipos = estado.entidades.find((e) => e.tags.has("mm:backpack:inventory1")).caja.s.filter(Boolean).map((x) => x.typeId).sort();
assert.deepEqual(tipos, ["diamante", "espada", "tierra"], "se sumó sin reemplazar");

// 3) Mochila guardada con el sistema viejo (estructura) se pasa sola
estado.props.set("backpack:inventory9", true);
estado.estructuras.set("backpack:inventory9", [it("oro", 3)]);
db = new QuickItemDatabase("backpack");
assert.equal(db.get("inventory9")[0].typeId, "oro", "migró desde la estructura");
assert.ok(estado.estructuras.has("backpack:inventory9"), "la estructura vieja no se borra");
assert.equal(estado.entidades.filter((e) => e.tags.has("mm:backpack:inventory9")).length, 1, "un solo almacén");

// 4) has/keys como la original
assert.ok(db.has("inventory1") && !db.has("inventory404"));
assert.ok(db.keys().includes("inventory9"));
console.log("todas las pruebas pasaron; objetos tirados:", estado.tirados.length);
