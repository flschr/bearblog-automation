---
uid: uGLMYTqsDkoGReRofLxU
title: Aufgeräumtes Zuhause
slug: aufgeraumtes-zuhause
alias: ""
published_date: "2026-02-12T14:44:00+00:00"
all_tags: "[\"bearblog\", \"blog\", \"blogging\", \"coding\"]"
publish: "True"
make_discoverable: "True"
is_page: "False"
canonical_url: ""
meta_description: ""
meta_image: "https://bear-images.sfo2.cdn.digitaloceanspaces.com/fischr/photo-1592634549335-f6be8df97b47.webp"
lang: de
class_name: ""
first_published_at: "2026-02-12T14:44:00+00:00"
---

Felix hat vor kurzem dazu [aufgerufen](https://wirres.net/articles/geht-hin-und-baut-eigenheime), das man sich ein Zuhause im Netz baut. Mein Blog ist im Grunde schon seit 2002 mein Zuhause, auch wenn es viele Jahre gab in denen es brach lag und ich mehr als einmal mit dem Gedanken gespielt habe, es endgültig zu löschen. Zum Glück habe ich diese Entscheidung immer ausgesessen, auch wenn ich in der Vergangenheit [nicht immer so egal](/das-fruhere-internet-ich/) unterwegs war.

So wie bei Felix und vielen anderen auch, ist meine Webseite mein kleiner Hobbykeller im Internet, oder anders gesagt, eine einzige Dauerbaustelle. Man schraubt hier, man optimiert da und so gedeiht alles vor sich hin.

Heute, während ich kränkelnd auf der Couch saß und mich frage, was die nächste belanglose Ablenkung auf Netflix sein kann, die einfach nur leise durch mein von Ibuprofen vernebeltes Hirn rieselt, habe ich mit etwas Abscheu auf eben jenen Hobbykeller geschaut. Im Second-Screen, wie man das eben heute so macht.

![Ein überladener Tisch mit Stapeln von Magazinen und Zeitschriften, darunter Comics und ältere Ausgaben von Playboy. Verschiedene Sammelgegenstände wie Geschirr und Küchenutensilien stehen im Hintergrund.](https://bear-images.sfo2.cdn.digitaloceanspaces.com/fischr/mr-brown-ao-xvrregw-unsplash.webp)
*Symbolbild Rumpelkammer (Foto: Mr. Brown, [Unsplash](https://unsplash.com/de/fotos/ein-raum-gefullt-mit-vielen-buchern-und-zeitschriften-aO--XvrrEGw))*

Dann kam die Erkenntnis: Mein Hobbykeller ist eine Rumpelkammer. Vollgestellt bis unter die Decke mit nutzlosem Zeug, das vermutlich niemand jemals braucht, mir aber wichtig genug erschien es irgendwann mal in den Raum zu stellen. Alles ruft laut *hier*, und *schenk mir Aufmerksamkeit*.

Klassischer [Feature Creep](https://en.wikipedia.org/wiki/Feature_creep). Vermutlich die größte Gefahr von Vibe-Coding. Man kann sich ja ganz einfach alles bauen lassen, was man sich so einbildet. Sehr verlockend, aber am Ende zerstört man damit nicht nur das Produkt sondern [verliert auch seine User](/ein-kurzes-winken-aus-dem-kaninchenbau/).

---

Flucht nach vorne, damit muss jetzt Schluss sein. Zuerst musste ein neues Theme her. Das [Standard Writer-Theme](https://bear-images.sfo2.cdn.digitaloceanspaces.com/themes/writer.png) von Bearblog hat bereits 95% der Arbeit erledigt. Ich habe eigentlich nur noch den [Bleed-Effekt](https://kilianvalkhof.com/2020/css-html/full-bleed-layout-using-simple-css/) für die Bilder eingefügt, und etwas an den Headlines gedreht. Im nächsten Schritt sind dann radikal alle selbstgeschraubten Skripte und auch die Fotogalerie rausgeflogen.

Dafür gibt es jetzt [eine Shorts-Section](/shorts/), die nicht nur meinen Foto-Posts eine neue Heimat bietet, sondern auch alle anderen Kurzformate in einer Art Timeline darstellt. Technisch sind das alles ganz normale Blogartikel, die basierend auf vergebenen Tags in der Shorts-Section auftauchen. Glücklicherweise hatten die allermeisten Posts schon die richtigen Tags, womit sich die Anpassung auf ein paar Zeilen zusätzliches CSS beschränkt hat.

Im Hintergrund läuft meine inzwischen sehr stabile [Blog-Automatisierung](https://github.com/flschr/bearblog-automation/), die schon seit Monaten neue Posts zu Mastodon, Bluesky, [IndexNow](https://www.indexnow.org/) und [archive.org](https://archive.org/) pusht. Das Repository sammelt gleichzeitig Webmentions ein (kann Bearblog leider nicht automatisch), und prüft regelmäßig ob meine Artikel tote Links enthalten und informiert mich im Fall der Fälle über Github-Issues über zu reparierende Artikel. Achja, ein Backup aller Artikel wird im Repository auch automatisch angelegt.

Spannender Nebeneffekt von diesem ganzen Zirkus ist, dass das Repository auch die Mappings von Blog-URL zu den Social Media-Posts wegschreibt. Damit konnte ich hier im Blog sehr einfach anzeigen, wie viele Likes, Boosts und Mentions ein bestimmter Artikel bekommen hat. Wie gesagt, konnte, denn dieses Skript ist natürlich auch dem Aufräumwahn zum Opfer gefallen. Das Repository werkelt aber weiterhin im Hintergrund, nur für den Fall der Fälle, das ich mir hier doch irgendwann wieder mehr Rauschen einbilde.

Damit steht ab jetzt der eigentliche Inhalt im Vordergrund und das ganze technische Gedöns und Gerümpel steht, versteckt vor dem Blick des geneigten Besuchers in der Abstellkammer. Das fühlt sich herrlich aufgeräumt und befreiend an.

![Sieben Fischköpfe liegen auf einem weißen Untergrund, einige in verschiedenen Größen und leicht unterschiedlichen Winkeln angeordnet. Die Köpfe haben eine glänzende, silbrige Oberfläche mit charakteristischen Augen und Kiemen.](https://bear-images.sfo2.cdn.digitaloceanspaces.com/fischr/photo-1592634549335-f6be8df97b47.webp)
*Symbolbild alles ordentlich aufgeräumt (Foto: Gunnar Ridderström, [Unsplash](https://unsplash.com/de/fotos/silberfisch-auf-weissem-tisch-faGhR9LEAE0))*

Im Automatisierungs-Repository habe ich jetzt noch einen neuen Short-Post Typ konfiguriert, damit alle hier im Blog veröffentlichte Kurzgedanken nicht nur in den Shorts landen, sondern auch als nativer Toot bei Mastodon (und Bluesky) auftauchen. Das sieht dann so aus, als hätte ich den Post direkt dort verfasst, ganz ohne Backlink zum Artikel.

In diesem Sinne: Baut euer Eigenheim im Netz, aber räumt von Zeit zu Zeit auch mal auf.