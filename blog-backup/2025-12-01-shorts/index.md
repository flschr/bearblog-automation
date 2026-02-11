---
uid: KpcGoCZNcfaVierAuLSW
title: Shorts
slug: shorts
alias: ""
published_date: "2025-12-01T19:32:00+00:00"
all_tags: "[]"
publish: "True"
make_discoverable: "False"
is_page: "True"
canonical_url: ""
meta_description: ""
meta_image: "https://bear-images.sfo2.cdn.digitaloceanspaces.com/fischr/photo-1592634549335-f6be8df97b47.webp"
lang: ""
class_name: ""
first_published_at: "2025-12-01T19:32:00+00:00"
---

<span hidden>Eine kleine Auswahl von sehenswerten Fotos von René Fischer.</span>

<style>
/* =========================
   SHORTS stream (page-marker)
   - media bleeds to card edge
   - date under media, before text
   - title hidden
   ========================= */

/* activate on your marker */
body:has(.page-marker[data-page="shorts"]) ul.embedded.blog-posts{
  list-style: none;
  padding: 0;
  margin: 2rem 0 3rem;
  display: grid;
  gap: 1.25rem;
}

/* card */
body:has(.page-marker[data-page="shorts"]) ul.embedded.blog-posts > li{
  position: relative;
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 0; /* we’ll manage padding per section */
  background: rgba(0,0,0,0.015);
  overflow: hidden; /* ensures bleed stays inside rounded corners */
}

@media (prefers-color-scheme: dark){
  body:has(.page-marker[data-page="shorts"]) ul.embedded.blog-posts > li{
    background: rgba(255,255,255,0.03);
  }
}

/* reorder so content block comes first (media + text),
   then our date permalink (injected via JS) */
body:has(.page-marker[data-page="shorts"]) ul.embedded.blog-posts > li{
  display: flex;
  flex-direction: column;
}

/* content wrapper */
body:has(.page-marker[data-page="shorts"]) ul.embedded.blog-posts > li > div{
  order: 1;
  padding: 0 1.1rem 1.05rem; /* side padding for text */
}

/* hide original title link (we’ll reuse it as date permalink via JS) */
body:has(.page-marker[data-page="shorts"]) ul.embedded.blog-posts > li > a{
  display: none !important;
}

/* original date block: hide (JS will create a permalink) */
body:has(.page-marker[data-page="shorts"]) ul.embedded.blog-posts > li > span{
  display: none !important;
}

/* === media: bleed to card edge, never crop === */
body:has(.page-marker[data-page="shorts"]) ul.embedded.blog-posts > li > div p:first-child:has(> img),
body:has(.page-marker[data-page="shorts"]) ul.embedded.blog-posts > li > div p:first-child:has(> video),
body:has(.page-marker[data-page="shorts"]) ul.embedded.blog-posts > li > div p:first-child:has(> iframe){
  /* remove text padding so media can touch edges */
  margin: 0;
  padding: 0;
}

/* actual media elements */
body:has(.page-marker[data-page="shorts"]) ul.embedded.blog-posts img,
body:has(.page-marker[data-page="shorts"]) ul.embedded.blog-posts video,
body:has(.page-marker[data-page="shorts"]) ul.embedded.blog-posts iframe{
  display: block;
  width: 100%;
  max-width: 100%;
  margin: 0;                 /* no outside margins */
  border-radius: 0;          /* card already has rounding; overflow hidden handles it */
  border: 0;
  height: auto;
  object-fit: contain;       /* NEVER crop */
  aspect-ratio: auto;
}

/* iframes (videos) keep ratio */
body:has(.page-marker[data-page="shorts"]) ul.embedded.blog-posts iframe{
  aspect-ratio: 16 / 9;
  height: auto !important;
}

/* text spacing inside card */
body:has(.page-marker[data-page="shorts"]) ul.embedded.blog-posts > li > div p{
  margin: 0.75rem 0;
}

/* make the first *text* paragraph leave space for date line */
body:has(.page-marker[data-page="shorts"]) ul.embedded.blog-posts > li > div p:nth-child(2){
  margin-top: 0.65rem;
}

/* === date permalink injected via JS === */
body:has(.page-marker[data-page="shorts"]) .shorts-permalink{
  order: 2;
  display: block;
  padding: 0.6rem 1.1rem 0.0rem;
  font-size: 0.82em;
  line-height: 1.2;
  color: var(--muted);
  text-decoration: none;
}

body:has(.page-marker[data-page="shorts"]) .shorts-permalink:hover{
  text-decoration: underline;
  text-decoration-thickness: 1px;
  text-underline-offset: 0.18em;
  opacity: 0.9;
}
</style>

<script>
/* Turns the existing title link into a date permalink (CSS alone can’t do this). */
window.addEventListener("load", () => {
  const root = document.querySelector(".page-marker[data-page='shorts']");
  if (!root) return;

  document.querySelectorAll("ul.embedded.blog-posts > li").forEach(li => {
    const time = li.querySelector("span time");
    const titleLink = li.querySelector(":scope > a[href]");
    if (!time || !titleLink) return;

    // Create date permalink
    const a = document.createElement("a");
    a.href = titleLink.getAttribute("href");
    a.className = "shorts-permalink";
    a.textContent = time.textContent.trim(); // already formatted by Bear’s script

    // Insert right after media (we use flex order anyway)
    li.appendChild(a);
  });
});
</script>

<span class="page-marker" data-page="shorts" hidden></span>
{{ posts | tag:shorts | content:True }}