"""Lee las estadisticas de GoatCounter (lo que la gente toca en la pagina) y guarda stock/demanda.csv
para el ERP: tallas mas buscadas, tallas buscadas sin stock, pares mas vistos, avisos y busquedas.
Necesita el secreto GOATCOUNTER_TOKEN. Corre una vez por hora."""
import csv, datetime, json, os, sys, urllib.parse, urllib.request

TOKEN = os.environ.get("GOATCOUNTER_TOKEN", "").strip()
API = "https://brunacr.goatcounter.com/api/v0"
TIPOS = [("sin-stock-", "Talla sin stock"), ("avisame-talla-", "Avisame talla"), ("avisame-par-", "Avisame par"),
         ("talla-", "Talla"), ("ver-par-", "Par visto"), ("buscar-", "Busqueda"), ("compartir-par-", "Par compartido")]


def hits(dias):
    hoy = datetime.date.today()
    q = {"start": (hoy - datetime.timedelta(days=dias)).isoformat(), "end": hoy.isoformat(), "limit": 200}
    out, exclude = {}, []
    for _ in range(10):
        qq = dict(q)
        if exclude:
            qq["exclude_paths"] = ",".join(map(str, exclude))
        req = urllib.request.Request(API + "/stats/hits?" + urllib.parse.urlencode(qq),
                                     headers={"Authorization": "Bearer " + TOKEN, "Content-Type": "application/json"})
        d = json.load(urllib.request.urlopen(req, timeout=30))
        for h in d.get("hits", []):
            out[h.get("path", "")] = (h.get("count", 0), h.get("title", ""))
            exclude.append(h.get("path_id"))
        if not d.get("more"):
            break
    return out


def main():
    if not TOKEN:
        print("Sin GOATCOUNTER_TOKEN: no se calcula la demanda."); return
    if os.path.exists("stock/demanda.csv") and datetime.datetime.utcnow().minute >= 6:
        print("La demanda se actualiza una vez por hora."); return
    h30, h7 = hits(30), hits(7)
    filas = []
    for path, (n, titulo) in h30.items():
        clave = path.lstrip("/")
        tipo = next((t for pre, t in TIPOS if clave.startswith(pre)), None)
        if not tipo:
            continue
        filas.append([tipo, clave, titulo, n, h7.get(path, (0, ""))[0]])
    filas.sort(key=lambda f: (f[0], -f[3]))
    with open("stock/demanda.csv", "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["Tipo", "Clave", "Detalle", "Ultimos 30 dias", "Ultimos 7 dias"])
        w.writerows(filas)
    print("Demanda:", len(filas), "filas")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("No se pudo leer GoatCounter:", e); sys.exit(0)
