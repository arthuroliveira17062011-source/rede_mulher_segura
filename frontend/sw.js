// Service worker mínimo — necessário para o navegador permitir
// "Adicionar à tela inicial" (o atalho não aparece sem isso no Android/Chrome).
const CACHE_NOME = "sabor-caseiro-v2";
const ARQUIVOS_BASICOS = ["./index.html", "./style.css", "./manifest.json", "./icon-192.png", "./icon-512.png"];

self.addEventListener("install", (evento) => {
  evento.waitUntil(
    caches.open(CACHE_NOME).then((cache) => cache.addAll(ARQUIVOS_BASICOS))
  );
  self.skipWaiting();
});

self.addEventListener("activate", (evento) => {
  evento.waitUntil(
    caches.keys().then((chaves) =>
      Promise.all(chaves.filter((chave) => chave !== CACHE_NOME).map((chave) => caches.delete(chave)))
    )
  );
  self.clients.claim();
});

self.addEventListener("fetch", (evento) => {
  evento.respondWith(
    caches.match(evento.request).then((resposta) => resposta || fetch(evento.request))
  );
});
