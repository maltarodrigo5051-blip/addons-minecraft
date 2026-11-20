import { world, system } from "@minecraft/server";

/**
 * Almacenamiento seguro de Mochilas Mejoradas (@Omare).
 *
 * Reemplaza a "Quick Item Database" con la misma forma de uso (set/get/has/delete/keys/values/
 * clear), así el resto del add-on no cambia. La diferencia está por dentro:
 *
 *  - Cada clave tiene su propio almacén PERMANENTE: una entidad "qidb:storage" que vive en la zona
 *    de guardado (siempre cargada). Ya no se colocan y borran estructuras para cada lectura.
 *  - set() guarda AL INSTANTE. No hay cola que se pierda si el mundo se cierra.
 *  - Si la zona aún no carga (justo al abrir el mundo), get() NO devuelve una mochila vacía que
 *    luego se guardaría encima. Esa clave queda "en duda" y, cuando la zona carga, lo nuevo se
 *    SUMA a lo que ya había en vez de reemplazarlo.
 *  - Las mochilas guardadas con el sistema anterior (estructuras) se pasan solas al almacén nuevo
 *    la primera vez que se leen. La estructura vieja no se borra, por seguridad.
 */
const TIPO = "qidb:storage";
const CASILLAS = 256;

export class QuickItemDatabase {
  #espacio;
  #cache = new Map();      // clave -> valor (lo último leído o guardado)
  #pendientes = new Map(); // clave -> valor que no se pudo guardar todavía
  #dudosas = new Set();    // claves que se leyeron sin la zona cargada

  /** Los demás parámetros del original (saveRate, QAMsize, logs) ya no hacen falta. */
  constructor(namespace = "") {
    if (!/^[a-z0-9_]*$/.test(namespace)) throw new Error(`[Mochilas Mejoradas] Espacio de nombres inválido: <${namespace}>`);
    this.#espacio = namespace;
    world.afterEvents.playerSpawn.subscribe(() => this.#asegurarZona());
    system.runTimeout(() => this.#asegurarZona(), 40);
    system.runInterval(() => this.#reintentar(), 20);
  }

  // --- Zona de guardado ---------------------------------------------------------
  #zona() {
    let z = world.getDynamicProperty("storagelocation");
    if (!z) {
      z = { x: 0, y: 318, z: 0 };
      world.setDynamicProperty("storagelocation", z);
    }
    return { x: Math.floor(z.x), y: 318, z: Math.floor(z.z) };
  }

  #dimension() {
    return world.getDimension("overworld");
  }

  #asegurarZona() {
    const z = this.#zona();
    try {
      this.#dimension().runCommand(`tickingarea add ${z.x} 319 ${z.z} ${z.x} 318 ${z.z} storagearea`);
    } catch {
      // ya existe
    }
  }

  #lista() {
    try {
      return this.#dimension().getBlock(this.#zona()) !== undefined;
    } catch {
      return false;
    }
  }

  // --- Almacenes ----------------------------------------------------------------
  #nombre(key) {
    if (!/^[a-z0-9_]*$/.test(key)) throw new Error(`[Mochilas Mejoradas] Clave inválida: <${key}>`);
    return `${this.#espacio}:${key}`;
  }

  #almacen(clave) {
    return this.#dimension().getEntities({ type: TIPO, tags: [`mm:${clave}`] })[0];
  }

  #crearAlmacen(clave) {
    const e = this.#dimension().spawnEntity(TIPO, this.#zona());
    e.addTag(`mm:${clave}`);
    return e;
  }

  #leerContenedor(contenedor) {
    const items = [];
    for (let i = 0; i < Math.min(CASILLAS, contenedor.size); i++) items.push(contenedor.getItem(i));
    while (items.length && !items[items.length - 1]) items.pop();
    return items;
  }

  /** Lee lo guardado con el sistema anterior (estructura) sin borrarla. */
  #leerEstructuraVieja(clave) {
    if (!world.structureManager.get(clave)) return undefined;
    const z = this.#zona();
    const antes = new Set(this.#dimension().getEntities({ type: TIPO, location: z, maxDistance: 1 }).map((e) => e.id));
    world.structureManager.place(clave, this.#dimension(), z, { includeEntities: true, includeBlocks: false });
    const nuevas = this.#dimension().getEntities({ type: TIPO, location: z, maxDistance: 1 }).filter((e) => !antes.has(e.id));
    if (!nuevas.length) return undefined;
    const items = this.#leerContenedor(nuevas[0].getComponent("inventory").container);
    nuevas.forEach((e) => e.remove()); // solo la copia temporal; la estructura sigue guardada
    return items;
  }

  #escribir(clave, valor, sumar) {
    let e = this.#almacen(clave);
    if (!e) {
      const viejo = this.#leerEstructuraVieja(clave);
      e = this.#crearAlmacen(clave);
      if (viejo) viejo.forEach((it, i) => it && e.getComponent("inventory").container.setItem(i, it));
    }
    const caja = e.getComponent("inventory").container;
    const lista = Array.isArray(valor) ? valor : [valor];
    if (sumar) {
      // Lo nuevo se agrega en casillas vacías: nunca reemplaza lo que ya estaba guardado.
      for (const it of lista) {
        if (!it) continue;
        let libre = -1;
        for (let i = 0; i < caja.size; i++) if (!caja.getItem(i)) { libre = i; break; }
        if (libre >= 0) caja.setItem(libre, it);
        else this.#dimension().spawnItem(it, this.#zona());
      }
    } else {
      for (let i = 0; i < caja.size; i++) caja.setItem(i, lista[i] ?? undefined);
    }
    world.setDynamicProperty(clave, Array.isArray(valor));
    if (sumar) this.#cache.set(clave, Array.isArray(valor) ? this.#leerContenedor(caja) : valor);
  }

  #reintentar() {
    if (!this.#pendientes.size || !this.#lista()) return;
    for (const [clave, valor] of this.#pendientes) {
      try {
        this.#escribir(clave, valor, this.#dudosas.has(clave));
        this.#pendientes.delete(clave);
        this.#dudosas.delete(clave);
      } catch (e) {
        console.warn(`[Mochilas Mejoradas] No se pudo guardar <${clave}> todavía: ${e}`);
      }
    }
  }

  // --- API (igual que Quick Item Database) -----------------------------------------
  set(key, value) {
    const clave = this.#nombre(key);
    if (Array.isArray(value) && value.length > CASILLAS) throw new Error(`[Mochilas Mejoradas] <${clave}> tiene más de ${CASILLAS} objetos`);
    this.#cache.set(clave, value);
    world.setDynamicProperty(clave, Array.isArray(value));
    if (this.#lista() && !this.#dudosas.has(clave)) {
      try {
        this.#escribir(clave, value, false);
        this.#pendientes.delete(clave);
        return;
      } catch (e) {
        console.warn(`[Mochilas Mejoradas] Se guardará <${clave}> en un momento: ${e}`);
      }
    }
    this.#pendientes.set(clave, value); // se reintenta sin perderse
  }

  get(key) {
    const clave = this.#nombre(key);
    if (this.#cache.has(clave)) return this.#cache.get(clave);
    if (!this.#lista()) {
      // La zona no carga: no se inventa una mochila vacía.
      if (world.getDynamicProperty(clave) !== undefined) this.#dudosas.add(clave);
      return undefined;
    }
    let e = this.#almacen(clave);
    let items;
    if (e) items = this.#leerContenedor(e.getComponent("inventory").container);
    else {
      items = this.#leerEstructuraVieja(clave);
      if (items === undefined) {
        if (world.getDynamicProperty(clave) === undefined) throw new Error(`[Mochilas Mejoradas] La clave <${clave}> no existe.`);
        items = [];
      }
      e = this.#crearAlmacen(clave); // se pasa al almacén nuevo
      items.forEach((it, i) => it && e.getComponent("inventory").container.setItem(i, it));
    }
    const valor = world.getDynamicProperty(clave) === false ? items[0] : items;
    this.#cache.set(clave, valor);
    return valor;
  }

  has(key) {
    const clave = this.#nombre(key);
    return this.#cache.has(clave) || this.#pendientes.has(clave) || world.getDynamicProperty(clave) !== undefined;
  }

  delete(key) {
    const clave = this.#nombre(key);
    this.#cache.delete(clave);
    this.#pendientes.delete(clave);
    this.#almacen(clave)?.remove();
    if (world.structureManager.get(clave)) world.structureManager.delete(clave);
    world.setDynamicProperty(clave, undefined);
  }

  keys() {
    const prefijo = `${this.#espacio}:`;
    return world.getDynamicPropertyIds().filter((id) => id.startsWith(prefijo)).map((id) => id.slice(prefijo.length));
  }

  values() {
    return this.keys().map((k) => this.get(k));
  }

  clear() {
    for (const k of this.keys()) this.delete(k);
  }
}
