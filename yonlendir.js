// Kampanya adı: ?k= (ör. /ig?k=story) > sayfanın data-k değeri > "site".
// Play'de utm_campaign, App Store'da ct olarak raporlanır.
(function () {
  var gecerli = /^[a-z0-9_-]{1,40}$/;
  var varsayilan = document.currentScript.getAttribute('data-k') || 'site';
  var k = new URLSearchParams(location.search).get('k') || varsayilan;
  if (!gecerli.test(k)) k = varsayilan;

  // pt: App Store Connect provider token (hesaba ait, her kampanyada aynı).
  var ios = 'https://apps.apple.com/tr/app/apple-store/id6792290422?pt=129188874&ct=' + k + '&mt=8';
  var android = 'https://play.google.com/store/apps/details?id=com.selman.memur_ilanlari'
    + '&referrer=' + encodeURIComponent('utm_source=' + k + '&utm_medium=social&utm_campaign=' + k);
  document.getElementById('ios').href = ios;
  document.getElementById('android').href = android;

  var ua = navigator.userAgent;
  var iPadOs = /Macintosh/.test(ua) && navigator.maxTouchPoints > 1;
  if (/iPhone|iPad|iPod/.test(ua) || iPadOs) location.replace(ios);
  else if (/Android/.test(ua)) location.replace(android);
})();
