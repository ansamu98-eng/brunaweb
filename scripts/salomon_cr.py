"""Agrega a stock/stock.json lo que Salomon Costa Rica tiene disponible (XT-6 y XT-6 GTX).

Se guarda en la lista "s": [modelo, talla, color, precio, promo], con el nombre de color
y el precio de Bruna (pestaña Precios de la hoja). La pagina lo muestra como entrega
inmediata; en modo equipo (?equipo=1) se marca en naranja como "Salomon CR".
"""
import csv, json, re, subprocess, sys, unicodedata, urllib.request

MODELOS = {"XT-6": "Salomon XT-6", "XT-6 GORE-TEX": "Salomon XT-6 GTX"}
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
    for p in prods:
        modelo = MODELOS.get((p.get("title") or "").strip().upper())
        if not modelo:
            continue
        nombres = [str(o.get("name", "")).lower() for o in p.get("options", [])]
        ic = next((k for k, n in enumerate(nombres) if "color" in n), 0)
        it = next((k for k, n in enumerate(nombres) if "talla" in n or "size" in n), 1)
        lista = precios.get(modelo, [])
        tipico = sorted(x[2] for x in lista)[len(lista) // 2] if lista else 0
        for v in p.get("variants", []):
            if not v.get("available"):
                continue
            color_cr = v.get(f"option{ic + 1}") or ""
            m = re.search(r"\d+(?:\.\d+)?", str(v.get(f"option{it + 1}") or ""))
            if not color_cr or not m:
                continue
            talla = f"{float(m.group()):g} US Men"
            w = palabras(color_cr)
            cand = [x for x in lista if len(x[1]) >= 2 and x[1] <= w]
            if cand:
                c, _, precio, promo = max(cand, key=lambda x: (len(x[1]), -abs(len(w) - len(x[1]))))
            else:
                partes = []
                for pz in re.split(r"\s*/\s*", color_cr.title()):
                    if pz not in partes:
                        partes.append(pz)
                c, precio, promo = " / ".join(partes), tipico, 0
                sin_match.add(f"{modelo} | {color_cr}")
            filas.append([modelo, talla, c, precio, promo])
    vistos, s = set(), []
    for f in filas:
        k = (f[0], f[1], f[2].lower())
        if k not in vistos:
            vistos.add(k)
            s.append(f)
    s.sort(key=lambda f: (f[0], f[2], float(f[1].split()[0])))
    out["s"] = s
    json.dump(out, open("stock/stock.json", "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    print("Salomon CR:", len(s), "tallas disponibles")
    for x in sorted(sin_match):
        print("  sin nombre en Precios:", x)


if __name__ == "__main__":
    sys.exit(main())
