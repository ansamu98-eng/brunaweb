/* Reseñas reales de clientes de Bruna (tomadas de mensajes de Instagram).
   Para agregar una: subir el recorte a assets/resenas/ y sumar un objeto a RESENAS.
   Solo mensajes reales; sin apellidos, fotos de perfil ni usuarios. */
(function () {
  var RESENAS = [
    { t: "Muchas gracias por su paciencia, su atención y su excelente servicio. Ya me llegó mi pedido 🥳🙌 ¡Que tengan una linda tarde!", n: "Ana S.", f: "Noviembre 2026", img: "r1.jpg" },
    { t: "Ya recibí mis tenis y me quedaron perfectas 🥹❤️ ¡Muchísimas gracias Bruna por tan excelente servicio! De fijo las próximas las compro con ustedes!!!", n: "Alexandra", f: "", img: "r3.jpg" },
    { t: "Holaaa!! Ya me llegaron, estoy encantada, son preciosaaas 😍😍 todo fue súper rápidooo, muchísimas gracias 😊", n: "Clienta por Instagram", f: "", img: "r4.jpg" },
    { t: "Llegaron súper bien!! Muchísimas gracias. De fijo nos estaremos hablando para próximas", n: "Cliente por Instagram", f: "", img: "r2.jpg" },
    { t: "Si me quedaron!!!!!!! 😍😍😍😍 están perfectos y me encantan!!! Muchísimas gracias", n: "Cliente por Instagram", f: "", img: "r5.jpg" }
  ];
  var DATOS = [["+850", "pares vendidos desde abril 2026"], ["100%", "originales, verificados"], ["1 a 2 días", "envío a todo el país"]];

  var el = document.getElementById("resenas");
  if (!el) return;
  var base = (el.getAttribute("data-base") || "") + "assets/resenas/";
  var esc = function (s) { return String(s).replace(/[&<>"]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]; }); };

  var css = document.createElement("style");
  css.textContent =
    ".rs{max-width:1000px;margin:0 auto;padding:40px 16px 8px;font-family:Poppins,system-ui,sans-serif;color:#4A3428}" +
    ".rs h2{font-size:24px;font-weight:600;margin:0 0 4px;letter-spacing:-.01em;text-align:center}" +
    ".rs .rs-sub{margin:0 auto 20px;font-size:14px;color:#8b7a6f;text-align:center;max-width:46ch}" +
    ".rs-datos{display:flex;justify-content:center;flex-wrap:wrap;gap:10px 28px;margin:0 0 22px}" +
    ".rs-datos div{text-align:center}.rs-datos b{display:block;font-size:22px;font-weight:600;color:#F8503B}.rs-datos span{font-size:12.5px;color:#8b7a6f}" +
    ".rs-lista{display:flex;gap:14px;overflow-x:auto;scroll-snap-type:x mandatory;padding:4px 2px 14px;scrollbar-width:none}" +
    ".rs-lista::-webkit-scrollbar{display:none}" +
    ".rs-c{flex:0 0 82%;max-width:340px;scroll-snap-align:center;background:#fff;border:1px solid #ece4d9;border-radius:22px;padding:20px 20px 16px;display:flex;flex-direction:column;gap:12px}" +
    "@media(min-width:900px){.rs-lista{display:grid;grid-template-columns:repeat(3,1fr);overflow:visible}.rs-c{max-width:none}}" +
    ".rs-c .q{font-size:15px;line-height:1.55;margin:0;flex:1}" +
    ".rs-c .q::before{content:'\\201C';display:block;font-size:40px;line-height:.6;color:#F8503B;margin-bottom:6px}" +
    ".rs-c .pie{display:flex;justify-content:space-between;align-items:center;gap:8px;font-size:13px}" +
    ".rs-c .pie b{font-weight:600}.rs-c .pie span{color:#8b7a6f;font-size:12px}" +
    ".rs-c button{border:0;background:none;padding:0;color:#4A3428;font:inherit;font-size:12.5px;text-decoration:underline;text-underline-offset:3px;cursor:pointer}" +
    ".rs-nota{font-size:12px;color:#8b7a6f;text-align:center;margin:4px 0 0}" +
    ".rs-lb{position:fixed;inset:0;z-index:60;background:rgba(43,30,24,.72);display:none;align-items:center;justify-content:center;padding:20px}" +
    ".rs-lb.on{display:flex}.rs-lb img{max-width:min(560px,100%);max-height:80vh;border-radius:16px}" +
    ".rs-lb button{position:absolute;top:16px;right:16px;width:40px;height:40px;border-radius:50%;border:0;background:#fff;font-size:20px;cursor:pointer}";
  document.head.appendChild(css);

  el.className = "rs";
  el.innerHTML =
    '<h2>Lo que dicen nuestros clientes</h2>' +
    '<p class="rs-sub">Mensajes reales que nos han enviado por Instagram después de recibir su par.</p>' +
    '<div class="rs-datos">' + DATOS.map(function (d) { return "<div><b>" + d[0] + "</b><span>" + esc(d[1]) + "</span></div>"; }).join("") + "</div>" +
    '<div class="rs-lista">' + RESENAS.map(function (r, i) {
      return '<figure class="rs-c" style="margin:0"><blockquote class="q" style="margin:0">' + esc(r.t) + '</blockquote>' +
        '<figcaption class="pie"><div><b>' + esc(r.n) + '</b>' + (r.f ? '<br><span>' + esc(r.f) + '</span>' : '') + '</div>' +
        (r.img ? '<button type="button" data-i="' + i + '">Ver mensaje</button>' : '') + '</figcaption></figure>';
    }).join("") + "</div>" +
    '<p class="rs-nota">Para cuidar su privacidad mostramos solo el nombre.</p>' +
    '<div class="rs-lb" role="dialog" aria-modal="true" aria-label="Mensaje original"><button type="button" aria-label="Cerrar">×</button><img alt="Mensaje original del cliente"></div>';

  var lb = el.querySelector(".rs-lb"), im = lb.querySelector("img");
  el.querySelectorAll(".rs-c button").forEach(function (b) {
    b.onclick = function () { im.src = base + RESENAS[+b.getAttribute("data-i")].img; lb.classList.add("on"); };
  });
  lb.onclick = function (e) { if (e.target === lb || e.target.tagName === "BUTTON") lb.classList.remove("on"); };
  document.addEventListener("keydown", function (e) { if (e.key === "Escape") lb.classList.remove("on"); });
})();
