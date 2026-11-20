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


def fotos_alta(fotos_cr, nombres_cr):
    """Para cada color que se muestra, si no tiene foto o la foto es pequena (< 900 px),
    usa la foto de Salomon CR (2000 px). Resultado: stock/fotos_alta.json {clave de la pagina: url}."""
    fotos = json.load(open("stock/fotos.json", encoding="utf-8"))
    cat = {x["id"]: x for x in json.load(open("stock/catalogo.json", encoding="utf-8"))}
    lineas = {"Salomon XT-6": "XT-6", "Salomon XT-6 GTX": "XT-6 GORE-TEX"}
    alta = {}
    for (modelo, color_cr), nombre in nombres_cr.items():
        url = fotos_cr.get((modelo, color_cr))
        if not url:
            continue
        clave = modelo.lower().replace("salomon ", "", 1) + "|" + norm_color(nombre)
        entrada = cat.get(fotos.get(clave, ""))
        if not entrada:
            entrada = next((x for x in cat.values() if x.get("linea") == lineas.get(modelo) and norm_color(x.get("color", "")) == norm_color(nombre)), None)
        prod = (entrada or {}).get("producto", "")
        if prod.startswith("http"):
            continue  # foto externa grande (Zalando, etc.)
        if prod and ancho_local("stock/" + prod) >= 900:
            continue
        alta[clave] = ("https:" + url) if url.startswith("//") else url
    json.dump(alta, open("stock/fotos_alta.json", "w", encoding="utf-8"), ensure_ascii=False, indent=0, sort_keys=True)
    print("Fotos en alta de Salomon CR:", len(alta))


if __name__ == "__main__":
    sys.exit(main())
