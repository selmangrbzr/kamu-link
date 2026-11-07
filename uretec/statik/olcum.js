// Ziyaretçi aradığını buluyor mu? PostHog (AB sunucusu), çerezsiz.
// cookieless_mode 'always': tarayıcıya çerez ya da depolama yazılmaz; ziyaretçi
// sunucuda günlük değişen bir özetle eşlenir (proje ayarı: cookieless_server_hash_mode).
// Olaylar: $pageview / $pageleave (otomatik), ilan_kaynagi (PDF ya da resmî ilan),
// magaza (Play / App Store). Hedefler sayfada data-olay ile işaretli (uretec/sablon.py).
(function () {
  if (location.hostname !== 'kamuuygulama.me') return;

  // ?olcum=kapali ölçümü bu tarayıcıda kapatır, ?olcum=acik geri açar (gizlilik sayfası).
  // Kayıt yalnızca ziyaretçi isterse yazılır; depolama kapalıysa o ziyaret için kapanır.
  var istek = new URLSearchParams(location.search).get('olcum');
  try {
    if (istek === 'kapali') localStorage.setItem('olcum', 'kapali');
    if (istek === 'acik') localStorage.removeItem('olcum');
    if (localStorage.getItem('olcum') === 'kapali') return;
  } catch (e) {
    if (istek === 'kapali') return;
  }

  var JETON = 'phc_CX2jMDMLxLAmegGjAXDvKDMm2jECtvrKHt9Q5xZkZrX4';
  // Reklam engelleyiciler posthog.com'u engellediği için PostHog'un yönetilen
  // ters vekili (Cloudflare) üzerinden kendi alt alan adımızı kullanıyoruz.
  var SUNUCU = 'https://k.kamuuygulama.me';

  // Kütüphane yüklenene kadar çağrıları biriktiren saplama (resmî snippet'in sade hâli).
  var ph = (window.posthog = window.posthog || []);
  if (!ph.__SV) {
    ph._i = [];
    ph.init = function (jeton, ayar, ad) { ph._i.push([jeton, ayar, ad]); };
    ['capture', 'register'].forEach(function (yontem) {
      ph[yontem] = function () { ph.push([yontem].concat([].slice.call(arguments))); };
    });
    ph.__SV = 1;
    var betik = document.createElement('script');
    betik.async = true;
    betik.crossOrigin = 'anonymous';
    betik.src = SUNUCU + '/static/array.js';
    document.head.appendChild(betik);
  }

  ph.init(JETON, {
    api_host: SUNUCU,
    ui_host: 'https://eu.posthog.com',
    cookieless_mode: 'always',
    autocapture: false,
    capture_pageview: true,
    capture_pageleave: true,
    disable_session_recording: true,
    disable_surveys: true,
    advanced_disable_flags: true
  });

  var yol = location.pathname;
  var tur = yol === '/' ? 'ana'
    : yol.indexOf('/ilan/') === 0 ? 'ilan'
    : yol.indexOf('/kurum/') === 0 ? 'kurum'
    : yol.indexOf('/sehir/') === 0 ? 'sehir'
    : yol.indexOf('/rehber') === 0 ? 'rehber'
    : /^\/(hakkinda|nasil-calisir|iletisim|gizlilik)\//.test(yol) ? 'bilgi'
    : 'merkez';
  ph.register({ sayfa_turu: tur });

  function yer(a) {
    if (a.closest('.alt-cubuk')) return 'alt_cubuk';
    if (a.closest('.kolofon')) return 'kolofon';
    if (a.closest('.cagri')) return 'cagri';
    return 'diger';
  }

  // Tıklamadan hemen sonra sayfa değiştiği için sendBeacon ile gönderilir.
  document.addEventListener('click', function (olay) {
    var a = olay.target.closest && olay.target.closest('a[data-olay]');
    if (!a) return;
    var tip = a.getAttribute('data-olay');
    var secenek = { transport: 'sendBeacon' };
    if (tip === 'pdf' || tip === 'resmi') {
      ph.capture('ilan_kaynagi', { kaynak: tip }, secenek);
    } else if (tip === 'magaza') {
      var magaza = a.hostname === 'apps.apple.com' ? 'ios' : 'android';
      ph.capture('magaza', { magaza: magaza, yer: yer(a) }, secenek);
    }
  });
})();
