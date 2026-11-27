"""Copia a stock/fotos/ las fotos que la página usaba desde otras tiendas (CDN de Shopify, Zalando, etc.).

Lee las URLs externas de stock/fotos_alta.json y stock/catalogo.json, las descarga una sola vez como
stock/fotos/ext-<id>.jpg y anota la equivalencia en stock/fotos_local.json (URL -> foto local).
La página usa la foto local cuando existe, así no depende de que esas tiendas mantengan sus enlaces.
Si una descarga falla, se deja la URL original y se reintenta en la próxima corrida.
"""
import hashlib
import io
import json
import os
import urllib.request

from PIL import Image

DIR = "stock"
FOTOS = os.path.join(DIR, "fotos")
MAPA = os.path.join(DIR, "fotos_local.json")


def cargar(ruta, defecto):
    try:
        with open(ruta, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return defecto


def urls_externas():
    urls = set()
    for k, v in cargar(os.path.join(DIR, "fotos_alta.json"), {}).items():
        if isinstance(v, str) and v.startswith("http"):
            urls.add(v)
    for c in cargar(os.path.join(DIR, "catalogo.json"), []):
        for campo in ("producto", "ambiente"):
            v = str(c.get(campo) or "")
            if v.startswith("http"):
                urls.add(v)
    return sorted(urls)


def bajar(url):
    pedido = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Bruna.cr fotos)"})
    with urllib.request.urlopen(pedido, timeout=30) as r:
        datos = r.read()
    im = Image.open(io.BytesIO(datos))
    if im.mode in ("RGBA", "LA", "P"):
        im = im.convert("RGBA")
        fondo = Image.new("RGB", im.size, (255, 255, 255))
        fondo.paste(im, mask=im.split()[3])
        im = fondo
    else:
        im = im.convert("RGB")
    im.thumbnail((1600, 1600))
    return im


def main():
    os.makedirs(FOTOS, exist_ok=True)
    mapa = cargar(MAPA, {})
    nuevas = fallidas = 0
    for url in urls_externas():
        local = mapa.get(url)
        if local and os.path.exists(os.path.join(DIR, local)):
            continue
        nombre = "ext-" + hashlib.sha1(url.encode("utf-8")).hexdigest()[:12] + ".jpg"
        try:
            bajar(url).save(os.path.join(FOTOS, nombre), "JPEG", quality=86, optimize=True, progressive=True)
            mapa[url] = "fotos/" + nombre
            nuevas += 1
        except Exception as e:  # noqa: BLE001 - una foto que falla no debe frenar el resto
            fallidas += 1
            print("No se pudo bajar:", url, "-", e)
    vigentes = set(urls_externas())
    mapa = {u: p for u, p in sorted(mapa.items()) if u in vigentes}
    with open(MAPA, "w", encoding="utf-8") as f:
        json.dump(mapa, f, ensure_ascii=False, indent=0)
    print(f"fotos externas copiadas: {nuevas}, fallidas: {fallidas}, total locales: {len(mapa)}")


if __name__ == "__main__":
    main()
