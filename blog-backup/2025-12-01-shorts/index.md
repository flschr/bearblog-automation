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
   SHORTS (page-marker)
   - media flush to card edges
   - top corners rounded (only)
   - date is permalink under media
   - kill global ul.blog-posts "–" styling for this list
   ========================= */

body:has(.page-marker[data-page="shorts"]) ul.embedded.blog-posts{
  list-style: none;
  padding: 0;
  margin: 2rem 0 3rem;
  display: grid;
  gap: 1.25rem;
}

/* Card */
body:has(.page-marker[data-page="shorts"]) ul.embedded.blog-posts > li{
  position: relative;
  border: 1px solid var(--border);
  border-radius: var(--radius);
  background: rgba(0,0,0,0.015);
  overflow: hidden; /* clip media to rounded card */
  padding: 0;       /* IMPORTANT: no padding on card itself */
}

@media (prefers-color-scheme: dark){
  body:has(.page-marker[data-page="shorts"]) ul.embedded.blog-posts > li{
    background: rgba(255,255,255,0.03);
  }
}

/* ---- Neutralize global ul.blog-posts list styling (the "–" etc.) ---- */
body:has(.page-marker[data-page="shorts"]) ul.embedded.blog-posts > li{
  padding-left: 0 !important;
}
body:has(.page-marker[data-page="shorts"]) ul.embedded.blog-posts > li::before{
  content: none !important;
}

/* Hide original date + title (we’ll generate date permalink via JS) */
body:has(.page-marker[data-page="shorts"]) ul.embedded.blog-posts > li > span{
  display: none !important;
}
body:has(.page-marker[data-page="shorts"]) ul.embedded.blog-posts > li > a{
  display: none !important;
}

/* Content wrapper: no padding (so media can be edge-to-edge) */
body:has(.page-marker[data-page="shorts"]) ul.embedded.blog-posts > li > div{
  padding: 0;
  margin: 0;
}

/* Media wrapper: first paragraph containing media should be flush */
body:has(.page-marker[data-page="shorts"]) ul.embedded.blog-posts > li > div p:first-child:has(> img),
body:has(.page-marker[data-page="shorts"]) ul.embedded.blog-posts > li > div p:first-child:has(> video),
body:has(.page-marker[data-page="shorts"]) ul.embedded.blog-posts > li > div p:first-child:has(> iframe){
  margin: 0;
  padding: 0;
}

/* Media itself: FULL WIDTH, no crop */
body:has(.page-marker[data-page="shorts"]) ul.embedded.blog-posts > li > div img,
body:has(.page-marker[data-page="shorts"]) ul.embedded.blog-posts > li > div video,
body:has(.page-marker[data-page="shorts"]) ul.embedded.blog-posts > li > div iframe{
  display: block;
  width: 100%;
  max-width: 100%;
  margin: 0;
  border: 0;
  height: auto;
  object-fit: contain; /* never crop */
}

/* Only top corners rounded for the media */
body:has(.page-marker[data-page="shorts"]) ul.embedded.blog-posts > li > div img,
body:has(.page-marker[data-page="shorts"]) ul.embedded.blog-posts > li > div video,
body:has(.page-marker[data-page="shorts"]) ul.embedded.blog-posts > li > div iframe{
  border-radius: var(--radius) var(--radius) 0 0;
}

/* iframe ratio */
body:has(.page-marker[data-page="shorts"]) ul.embedded.blog-posts > li > div iframe{
  aspect-ratio: 16 / 9;
  height: auto !important;
}

/* Text paragraphs: add padding inside card */
body:has(.page-marker[data-page="shorts"]) ul.embedded.blog-posts > li > div p{
  margin: 0.85rem 0;
  padding: 0 1.1rem;
  max-width: var(--text-measure);
}

/* But the media paragraph stays flush (already handled) */
body:has(.page-marker[data-page="shorts"]) ul.embedded.blog-posts > li > div p:first-child{
  padding: 0;
  max-width: none;
}

/* Date permalink injected by JS */
body:has(.page-marker[data-page="shorts"]) ul.embedded.blog-posts .shorts-permalink{
  display: inline-block;
  padding: 0.65rem 1.1rem 0.1rem;
  font-size: 0.82em;
  line-height: 1.2;
  color: var(--muted);
  text-decoration: none;
}

body:has(.page-marker[data-page="shorts"]) ul.embedded.blog-posts .shorts-permalink:hover{
  text-decoration: underline;
  text-decoration-thickness: 1px;
  text-underline-offset: 0.18em;
  opacity: 0.9;
}
</style>

<script>
/* Make the date clickable (link to the article) and place it under the media.
   CSS can’t turn <time> into a link; we reuse the existing title link href. */
window.addEventListener("load", () => {
  const marker = document.querySelector(".page-marker[data-page='shorts']");
  if (!marker) return;

  document.querySelectorAll("ul.embedded.blog-posts > li").forEach(li => {
    const time = li.querySelector(":scope > span time");
    const titleLink = li.querySelector(":scope > a[href]");
    const content = li.querySelector(":scope > div");
    if (!time || !titleLink || !content) return;

    // Create permalink from date
    const a = document.createElement("a");
    a.href = titleLink.getAttribute("href");
    a.className = "shorts-permalink";
    a.textContent = time.textContent.trim();

    // Insert AFTER the first media paragraph (if present), otherwise at top of content
    const firstP = content.querySelector("p");
    const hasMediaFirst =
      firstP &&
      (firstP.querySelector("img,video,iframe"));

    if (hasMediaFirst) {
      firstP.insertAdjacentElement("afterend", a);
    } else {
      content.insertAdjacentElement("afterbegin", a);
    }
  });
});
</script>


<span class="page-marker" data-page="shorts" hidden></span>
{{ posts | tag:shorts | content:True }}