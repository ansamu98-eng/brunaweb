"""Agrega a stock/stock.json lo que Salomon Costa Rica tiene disponible (XT-6 y XT-6 GTX).

Se guarda en la lista "s": [modelo, talla, color, precio, promo], con el nombre de color
y el precio de Bruna (pestaña Precios de la hoja). La pagina lo muestra como entrega
inmediata; en modo equipo (?equipo=1) se marca en naranja como "Salomon CR".
"""
import csv, json, re, subprocess, sys, unicodedata, urllib.request

MODELOS = {"XT-6": "Salomon XT-6", "XT-6 GORE-TEX": "Salomon XT-6 GTX"}
# Colores de Salomon CR que se confunden con otro nombre del catalogo de Bruna
NOMBRE_FIJO = {
    "stormy weather/mustang/blue curacao": "Stormy Weather / Mustang",  # no es el Blue Curacao
    "lunar rock/ftw silver/white": "Lunar Rock",  # no es el White Lunar Rock
}
SINON = {"vanilla": "vainilla", "grey": "gray", "milleau": "milieu", "choco": "chocolate", "asparagus": "aspargus"}


def palabras(txt):
    t = unicodedata.normalize("NFD", str(txt).lower())
    t = "".join(c for c in t if unicodedata.category(c) != "Mn")
    return {SINON.get(w, w) for w in re.findall(r"[a-z0-9]+", t)}


def num(x):
    try:
        return int(float(str(x).replace(",", "").strip() or 0))
    except ValueError:
        return 0


def anterior():
    try:
        return json.loads(subprocess.check_output(["git", "show", "HEAD:stock/stock.json"])).get("s")
    except Exception:
        return None


def bajar_productos():
    prods, pag = [], 1
    while pag <= 10:
        req = urllib.request.Request(f"https://salomon.co.cr/products.json?limit=250&page={pag}",
                                     headers={"User-Agent": "Mozilla/5.0 (BrunaStock)"})
        lote = json.load(urllib.request.urlopen(req, timeout=30)).get("products", [])
        if not lote:
            break
        prods += lote
        pag += 1
    return prods


def main():
    out = json.load(open("stock/stock.json", encoding="utf-8"))
    precios = {}
    try:
        for r in csv.DictReader(open("precios.csv", encoding="utf-8")):
            m, c = (r.get("Modelo") or "").strip(), (r.get("Color") or "").strip()
            if m and c and num(r.get("Precio")):
                precios.setdefault(m, []).append((c, palabras(c), num(r.get("Precio")), num(r.get("Promo"))))
    except Exception as e:
        print("No se pudo leer Precios:", e)
    try:
        prods = bajar_productos()
    except Exception as e:
        print("Salomon CR no respondio:", e)
        prods = None
    if not prods or not precios:
        viejo = anterior()
        if viejo:
            out["s"] = viejo
            json.dump(out, open("stock/stock.json", "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
        print("Se deja la lista de Salomon CR anterior.")
        return
    filas, sin_match = [], set()
    fotos_cr = {}  # (modelo, color de Salomon CR) -> url de la foto
    nombres_cr = {}  # (modelo, color de Salomon CR) -> nombre de Bruna
    for p in prods:
        modelo = MODELOS.get((p.get("title") or "").strip().upper())
        if not modelo:
            continue
        nombres = [str(o.get("name", "")).lower() for o in p.get("options", [])]
        ic = next((k for k, n in enumerate(nombres) if "color" in n), 0)
        it = next((k for k, n in enumerate(nombres) if "talla" in n or "size" in n), 1)
        lista = precios.get(modelo, [])
        tipico = sorted(x[2] for x in lista)[len(lista) // 2] if lista else 0
        imgs_por_variante = {vid: im.get("src") for im in p.get("images", []) for vid in (im.get("variant_ids") or [])}
        for v in p.get("variants", []):
            color_cr = v.get(f"option{ic + 1}") or ""
            src = (v.get("featured_image") or {}).get("src") or imgs_por_variante.get(v.get("id"))
            if src and color_cr:
                fotos_cr.setdefault((modelo, color_cr), src)
            if not v.get("available"):
                continue
            m = re.search(r"\d+(?:\.\d+)?", str(v.get(f"option{it + 1}") or ""))
            if not color_cr or not m:
                continue
            talla = f"{float(m.group()):g} US Men"
            w = palabras(color_cr)
            nombre_fijo = NOMBRE_FIJO.get(re.sub(r"\s*/\s*", "/", color_cr.strip().lower()))
            if nombre_fijo:
                w = palabras(nombre_fijo)
                cand = [x for x in lista if x[1] == w]
            else:
                cand = [x for x in lista if len(x[1]) >= 2 and x[1] <= w]
            if cand:
                c, _, precio, promo = max(cand, key=lambda x: (len(x[1]), -abs(len(w) - len(x[1]))))
            elif nombre_fijo:
                c, precio, promo = nombre_fijo, tipico, 0
                sin_match.add(f"{modelo} | {color_cr}")
            else:
                partes = []
                for pz in re.split(r"\s*/\s*", color_cr.title()):
                    if pz not in partes:
                        partes.append(pz)
                c, precio, promo = " / ".join(partes), tipico, 0
                sin_match.add(f"{modelo} | {color_cr}")
            filas.append([modelo, talla, c, precio, promo])
            nombres_cr[(modelo, color_cr)] = c
    # Ajustes desde el ERP (pestaña "Ajustes web"): colores que no se muestran y tallas agregadas a mano
    ocultar, extras = set(), []
    try:
        for r in csv.DictReader(open("ajustes.csv", encoding="utf-8")):
            tipo, m, c, t = [(r.get(k) or "").strip() for k in ("Tipo", "Modelo", "Color", "Talla")]
            if not m or not c:
                continue
            if tipo.lower().startswith("no"):
                ocultar.add((m, frozenset(palabras(c))))
            elif tipo.lower().startswith("agreg") and t:
                pr = next(((x[2], x[3]) for x in precios.get(m, []) if x[1] == palabras(c)), None)
                if pr:
                    nt = re.search(r"\d+(?:\.\d+)?", t)
                    talla = f"{float(nt.group()):g} US " + ("Women" if re.search(r"wom|muj|\bw\b", t, re.I) else "Men")
                    extras.append([m, talla, c, pr[0], pr[1], 1])
    except Exception as e:
        print("Sin ajustes:", e)
    filas = [f for f in filas if (f[0], frozenset(palabras(f[2]))) not in ocultar] + extras
    vistos, s = set(), []
    for f in filas:
        k = (f[0], f[1], f[2].lower())
        if k not in vistos:
            vistos.add(k)
            s.append(f)
    s.sort(key=lambda f: (f[0], f[2], float(f[1].split()[0])))
    out["s"] = [f[:5] for f in s]
    json.dump(out, open("stock/stock.json", "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    # Lista para el ERP (seccion Compras ocultas): la hoja la importa con IMPORTDATA
    with open("stock/ocultas.csv", "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["Modelo", "Color", "Talla", "Precio", "Promo", "Origen"])
        for f in s:
            w.writerow([f[0], f[2], f[1], f[3], f[4] or "", "Agregada" if len(f) > 5 else "Salomon CR"])
    print("Salomon CR:", len(s), "tallas disponibles")
    try:
        fotos_alta(fotos_cr, nombres_cr)
    except Exception as e:
        print("No se pudieron revisar las fotos:", e)
    for x in sorted(sin_match):
        print("  sin nombre en Precios:", x)


def norm_color(c):
    t = unicodedata.normalize("NFD", str(c).lower())
    t = "".join(ch for ch in t if unicodedata.category(ch) != "Mn")
    t = t.replace("vanilla", "vainilla").replace("grey", "gray")
    t = re.sub(r"\s*/\s*", " / ", t)
    return re.sub(r"\s+", " ", t).strip()


def ancho_local(ruta):
    try:
        from PIL import Image
        return Image.open(ruta).size[0]
    except Exception:
        return 0


# Tiendas oficiales de Salomon con catalogo abierto (Shopify). Salomon USA y Espana bloquean
# el acceso automatico, asi que se usan estas, que tienen las mismas fotos oficiales.
FUENTES = ["salomon.com.au", "salomon.co.nz", "salomon.com.tw", "salomon.com.mx", "salomon.cl"]
SINON_FOTO = {"toast": "roast", "milleau": "milieu", "vanilla": "vainilla", "grey": "gray", "choco": "chocolate", "asparagus": "aspargus"}


def pal_foto(txt):
    t = unicodedata.normalize("NFD", str(txt).lower())
    t = "".join(c for c in t if unicodedata.category(c) != "Mn")
    return {SINON_FOTO.get(w, w) for w in re.findall(r"[a-z0-9]+", t)} - {"ftw", "and"}


def tipo_modelo(txt):
    t = str(txt).lower()
    if "expanse" in t:
        return "xt-6 expanse"
    if "gore" in t or "gtx" in t:
        return "xt-6 gtx"
    return "xt-6"


def bajar_tienda(dom):
    prods = []
    for pag in range(1, 8):
        req = urllib.request.Request(f"https://{dom}/products.json?limit=250&page={pag}", headers={"User-Agent": "Mozilla/5.0 (BrunaFotos)"})
        lote = json.load(urllib.request.urlopen(req, timeout=30)).get("products", [])
        if not lote:
            break
        prods += lote
    return prods


def candidatos_fuentes():
    """Lista de (tipo, segmentos de color, palabras, url) de las tiendas oficiales."""
    out = []
    for dom in FUENTES:
        try:
            prods = bajar_tienda(dom)
        except Exception as e:
            print("  no respondio", dom, e)
            continue
        for p in prods:
            titulo = p.get("title") or ""
            if not re.match(r"\s*(salomon\s+)?xt-6\b", titulo, re.I):
                continue
            if re.search(r"\b(mid|mm6|kids|junior|j|protective|stormshade|softground|ft|shadow|steel|nostalgia|lab|swoven|moto)\b", titulo, re.I):
                continue
            tipo = tipo_modelo(titulo)
            nombres = [str(o.get("name", "")).lower() for o in p.get("options", [])]
            ic = next((k for k, n in enumerate(nombres) if "colo" in n or "顏色" in n or "颜色" in n), None)
            imgs = {vid: im.get("src") for im in p.get("images", []) for vid in (im.get("variant_ids") or [])}
            primera = (p.get("images") or [{}])[0].get("src")
            vistos = set()
            for v in p.get("variants", []) or [{}]:
                color = v.get(f"option{ic + 1}") if ic is not None else None
                if not color:
                    color = re.sub(r"(?i)\b(salomon|xt-6|gore-tex|gtx|advanced|adv)\b", " ", titulo)
                if color in vistos:
                    continue
                vistos.add(color)
                src = (v.get("featured_image") or {}).get("src") or imgs.get(v.get("id")) or primera
                if not src:
                    continue
                segs = [pal_foto(z) for z in re.split(r"\s*/\s*", color) if pal_foto(z)]
                out.append((tipo, segs, set().union(*segs) if segs else set(), ("https:" + src) if src.startswith("//") else src))
    return out


def buscar_foto(tipo, nombre, cands):
    w = pal_foto(nombre)
    if len(w) < 2:
        return None
    mejor, puntos = None, None
    for t, segs, words, url in cands:
        if t != tipo or not w <= words:
            continue
        # el nombre de Bruna tiene que cubrir uno de los dos primeros colores de Salomon
        if not any(sg and sg <= w for sg in segs[:2]):
            continue
        pts = (2 if segs and segs[0] <= w else 0, -len(words - w))
        if puntos is None or pts > puntos:
            mejor, puntos = url, pts
    return mejor


def norm_color(c):
    t = unicodedata.normalize("NFD", str(c).lower())
    t = "".join(ch for ch in t if unicodedata.category(ch) != "Mn")
    t = t.replace("vanilla", "vainilla").replace("grey", "gray")
    t = re.sub(r"\s*/\s*", " / ", t)
    return re.sub(r"\s+", " ", t).strip()


def ancho_local(ruta):
    try:
        from PIL import Image
        return Image.open(ruta).size[0]
    except Exception:
        return 0


def fotos_alta(fotos_cr, nombres_cr):
    """Para cada color XT-6 / GTX / Expanse que muestra la pagina busca la foto oficial: primero Salomon CR, despues otras tiendas oficiales de Salomon.
    Resultado: stock/fotos_alta.json {clave de la pagina: url}."""
    st = json.load(open("stock/stock.json", encoding="utf-8"))
    fotos = json.load(open("stock/fotos.json", encoding="utf-8"))
    cat = {x["id"]: x for x in json.load(open("stock/catalogo.json", encoding="utf-8"))}
    try:
        alias = {k.lower(): v for k, v in json.load(open("stock/alias.json", encoding="utf-8")).items()}
    except Exception:
        alias = {}
    lineas = {"xt-6": "XT-6", "xt-6 gtx": "XT-6 GORE-TEX", "xt-6 expanse": "XT-6 Expanse"}
    mostrados = {}
    for f in st.get("i", []) + st.get("s", []):
        mostrados[(f[0], f[2])] = 1
    for f in st.get("p", []):
        mostrados[(f[0], f[1])] = 1
    scr = {}
    for (modelo, color_cr), nombre in nombres_cr.items():
        if fotos_cr.get((modelo, color_cr)):
            scr[(modelo.lower().replace("salomon ", "", 1), norm_color(nombre))] = fotos_cr[(modelo, color_cr)]
    try:
        prev = json.load(open("stock/fotos_alta.json", encoding="utf-8"))
    except Exception:
        prev = {}
    prev_faltan = set(prev.pop("_sin_foto", []))
    import datetime
    hora_de_revisar = datetime.datetime.utcnow().minute < 6
    cands, alta, faltan = None, {}, []
    for (modelo, color) in mostrados:
        m = re.sub(r"\s*\(.*?\)\s*", " ", modelo).strip()
        tipo = m.lower().replace("salomon ", "", 1)
        if tipo not in lineas:
            continue
        color = alias.get(color.lower().strip(), color.strip())
        clave = tipo + "|" + norm_color(color)
        if clave in alta:
            continue
        entrada = cat.get(fotos.get(clave, ""))
        if not entrada:
            entrada = next((x for x in cat.values() if x.get("linea") == lineas[tipo] and norm_color(x.get("color", "")) == norm_color(color)), None)
        prod = (entrada or {}).get("producto", "")
        # Andres pidio la foto oficial para todos los colores; la foto propia queda si no hay oficial
        if prod.startswith("http"):
            continue
        url = scr.get((tipo, norm_color(color))) or prev.get(clave)
        if not url and clave in prev_faltan and not hora_de_revisar:
            faltan.append(clave)
            continue
        if not url:
            if cands is None:
                cands = candidatos_fuentes()
                print("  fotos oficiales revisadas:", len(cands))
            url = buscar_foto(tipo, color, cands)
        if url:
            alta[clave] = ("https:" + url) if url.startswith("//") else url
        else:
            faltan.append(clave)
    alta["_sin_foto"] = sorted(faltan)
    json.dump(alta, open("stock/fotos_alta.json", "w", encoding="utf-8"), ensure_ascii=False, indent=0, sort_keys=True)
    print("Fotos en alta:", len(alta), "| sin foto oficial:", len(faltan))
    for k in sorted(faltan):
        print("  sin foto:", k)


if __name__ == "__main__":
    sys.exit(main())
