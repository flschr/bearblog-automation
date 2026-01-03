---
uid: cwFPopykEFXqrJFLurdY
title: Taking a bite out of the Apple iCloud
slug: taking-a-bite-out-of-the-apple-icloud
alias: ""
published_date: "2026-01-03T23:45:00+00:00"
all_tags: "[\"blog\", \"digitallife\"]"
publish: "True"
make_discoverable: "True"
is_page: "False"
canonical_url: ""
meta_description: ""
meta_image: "https://bear-images.sfo2.cdn.digitaloceanspaces.com/fischr/001-1.webp"
lang: en
class_name: ""
first_published_at: "2026-01-03T23:45:00+00:00"
---

I am an Apple fan. My house is full of their tech, and I usually find their products delightful to use. I have always had trust in Apple, believing they would handle my data responsibly, prioritize customer satisfaction, and never let a customer down. In fact, I have never had any reason to distrust them or imagine that I should have a backup plan in case Apple goes berserk.

But recently, that facade developed a crack. After reading how [Paris was locked out of his Apple account](https://hey.paris/posts/appleid/), I realized that if the same happened to me, it would be a disaster.

Over the years, I had integrated almost every part of my life into their ecosystem. We use the Apple iCloud for our photos & videos, documents, contacts, calendars, passwords, and, yes, even our mailboxes. I guess this is what you call *having all eggs in one basket*.

Even though I do have local and additional cloud backups of my documents, mails, and the entire photo library, there are obviously some critical blind spots I need to fix ... now!

![Four-panel comic featuring a person discussing the phrase "Don't put all your chickens in one basket." The first panel shows chickens in a basket, the second expresses concern about losing the basket, the third questions where to get eggs, and the fourth depicts the person looking thoughtful, emphasizing they still have one fewer basket and several chickens.](https://bear-images.sfo2.cdn.digitaloceanspaces.com/fischr/igsnkneqp4yy.webp)

---

## What I have changed this week

### Moving away from Apple Passwords

As said, I've been using Apple Passwords, in fact since day one. It's convenient and free and works well enough for someone who is deeply in the Apple ecosystem. It's not the best password manager in the world, but it is getting its job done and doesn't cost any money. Since its debut, I canceled our 1Password family account and moved everyone in my household to the Apple solution.

At that time, I definitely thought about the risks of putting my online accounts into the walled garden of Apple but decided that losing access to my Apple account is an extremely unlikely event. Apple is a good friend, so why not? As we learned, I was wrong.

The last days I moved my personal passwords to [Proton Pass](https://proton.me/pass), and as I was on it, I also decided to do a spring clean (even though it's still winter) and deleted over 100 accounts to services I didn't use recently.

### Secure the access to my Mailboxes

Two years ago, I moved all our mail accounts to iCloud. It doesn't cost any money, is easy to manage for the whole family, and I trust Apple more than any other provider.

Since I use my own domain, I figured I could just switch to a new mail provider by changing my DNS settings if anything goes south. But then I found the catch:

I realized that my Cloudflare account (where I manage my domain settings) was using "Sign in with Apple". If Apple locked me out, I would also be locked out of Cloudflare and wouldn't be able to change my DNS settings to move my email to a new provider. *Wonderful superclusterfuck!*

I immediately decoupled my Cloudflare login from Apple and switched it to a standard mail login. For now, I’m staying with my mails living in iCloud, but if ever needed, the escape path is now fully accessible.

## Sovereignty, not hate

I want to be clear that I still love Apple products. This wasn't a move made out of anger, but out of a need for more digital resilience. If Apple ever decides to lock my account, either by mistake or by policy, it will be an annoyance, but it won't be a disaster anymore.