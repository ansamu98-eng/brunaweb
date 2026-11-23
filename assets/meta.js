/* Pixel de Meta (Facebook/Instagram Ads). Para activarlo, poner aquí el ID del conjunto de datos/pixel de Bruna.
   Mientras esté vacío no se carga nada. Eventos que manda la web:
   PageView (cada página), ViewContent (abrir un par), InitiateCheckout (tocar "Pedir/Reservar por Instagram"),
   Search (buscador) y Lead (tocar "Avisame"). */
(function () {
  var META_PIXEL_ID = "";
  window.metaTrack = function () {};
  if (!META_PIXEL_ID) return;
  !function(f,b,e,v,n,t,s){if(f.fbq)return;n=f.fbq=function(){n.callMethod?n.callMethod.apply(n,arguments):n.queue.push(arguments)};if(!f._fbq)f._fbq=n;n.push=n;n.loaded=!0;n.version='2.0';n.queue=[];t=b.createElement(e);t.async=!0;t.src=v;s=b.getElementsByTagName(e)[0];s.parentNode.insertBefore(t,s)}(window,document,'script','https://connect.facebook.net/en_US/fbevents.js');
  fbq('init', META_PIXEL_ID);
  fbq('track', 'PageView');
  window.metaTrack = function (ev, data) { try { fbq('track', ev, data || {}); } catch (e) {} };
})();
