/* Encabezado, menú, botón flotante y estadísticas compartidos por todas las páginas de Bruna.cr.
   Se incluye justo después de <body> con <script src=".../assets/site.js" data-variant="solid|overlay"></script> */
(function () {
  var me = document.currentScript;
  var base = (me.getAttribute("src") || "").replace(/assets\/site\.js.*$/, "");
  var variant = me.getAttribute("data-variant") || "solid";
  var IG = "thebruna.cr";
  var path = location.pathname.replace(/index\.html$/, "");
  var page = /\/stock\/$/.test(path) ? "stock" : /\/catalogo\/$/.test(path) ? "catalogo" : /\/terminos\/$/.test(path) ? "terminos" : "inicio";
  var on = function (k) { return page === k ? ' class="on"' : ""; };

  var links =
    '<a href="' + base + 'stock/"' + on("stock") + '>Qué hay en mi talla</a>' +
    '<a href="' + base + 'stock/#promos">Descuentos</a>' +
    '<a href="' + base + 'catalogo/"' + on("catalogo") + '>Catálogo</a>' +
    '<a href="' + base + 'terminos/"' + on("terminos") + '>Términos</a>';

  document.body.insertAdjacentHTML("afterbegin",
    '<header class="snav ' + variant + '">' +
      '<a class="logo" href="' + base + '" aria-label="Inicio"><img src="' + base + 'assets/logo_blanco.png" alt="bruna"></a>' +
      '<nav class="links">' + links + '<a href="https://instagram.com/' + IG + '">Instagram</a></nav>' +
      '<button class="burger" id="sburger" aria-label="Abrir menú"><i></i><i></i><i></i></button>' +
    '</header>' +
    '<div class="smenu" id="smenu" role="dialog" aria-modal="true" aria-label="Menú">' +
      '<div class="hd"><a href="' + base + '"><img src="' + base + 'assets/cisne.png" alt="Inicio"></a><button class="x" id="sclose" aria-label="Cerrar menú">×</button></div>' +
      '<ul>' +
        '<li><a href="' + base + '"' + on("inicio") + '><span>Inicio<small>Cómo comprar en Bruna</small></span></a></li>' +
        '<li><a href="' + base + 'stock/"' + on("stock") + '><span>Qué hay en mi talla<small>Todo lo disponible hoy</small></span></a></li>' +
        '<li><a href="' + base + 'stock/#promos"><span>Descuentos especiales<small>Pares rebajados</small></span></a></li>' +
        '<li><a href="' + base + 'catalogo/"' + on("catalogo") + '><span>Catálogo completo<small>Todos los colores que trabajamos</small></span></a></li>' +
        '<li><a href="' + base + 'stock/#guia"><span>Guía de tallas<small>UK, EU, US y cm</small></span></a></li>' +
        '<li><a href="' + base + 'terminos/"' + on("terminos") + '><span>Términos de compra<small>Reclamos, cambios y devoluciones</small></span></a></li>' +
      '</ul>' +
      '<div class="ft"><a class="ig" href="https://ig.me/m/' + IG + '">Escribinos</a><a class="wa" href="https://instagram.com/' + IG + '">Ver Instagram</a></div>' +
      '<div class="sl">A TU PASO</div>' +
    '</div>');

  document.body.insertAdjacentHTML("beforeend",
    '<a class="sfloat" id="sfloat" href="https://ig.me/m/' + IG + '" aria-label="Escribinos por Instagram">' +
      '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M21 11.5a8.4 8.4 0 0 1-9 8.4 8.6 8.6 0 0 1-3.8-.9L3 20l1.1-4.6A8.4 8.4 0 1 1 21 11.5z"/></svg>' +
      'Escribinos</a>');

  var menu = document.getElementById("smenu");
  function open(v) { menu.classList.toggle("on", v); document.documentElement.style.overflow = v ? "hidden" : ""; }
  document.getElementById("sburger").onclick = function () { open(true); };
  document.getElementById("sclose").onclick = function () { open(false); };
  menu.addEventListener("click", function (e) { if (e.target.closest("a")) open(false); });
  document.addEventListener("keydown", function (e) { if (e.key === "Escape") open(false); });

  var fl = document.getElementById("sfloat");
  function showFloat() { fl.classList.toggle("on", page !== "inicio" || window.scrollY > window.innerHeight * 0.6); }
  window.addEventListener("scroll", showFloat, { passive: true }); showFloat();

  /* Estadísticas (GoatCounter, sin cookies) */
  window.gcEvent = function (n, t) { try { if (window.goatcounter && window.goatcounter.count) window.goatcounter.count({ path: n, title: t || n, event: true }); } catch (e) {} };
  document.addEventListener("click", function (e) {
    var a = e.target.closest && e.target.closest("a"); if (!a) return;
    var h = a.getAttribute("href") || "";
    if (/ig\.me/.test(h)) gcEvent(a.id === "sfloat" ? "click-escribinos-flotante" : "click-escribinos-instagram", location.pathname);
    else if (/instagram\.com/.test(h)) gcEvent("click-ver-instagram", location.pathname);
  }, true);
  var gc = document.createElement("script");
  gc.async = true; gc.src = "https://gc.zgo.at/count.js"; gc.setAttribute("data-goatcounter", "https://brunacr.goatcounter.com/count");
  document.head.appendChild(gc);
})();
