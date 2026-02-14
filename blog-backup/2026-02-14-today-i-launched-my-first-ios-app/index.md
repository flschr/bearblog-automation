---
uid: FhnZYSAyVnTgCqHHUEIT
title: Today I launched my first iOS app
slug: today-i-launched-my-first-ios-app
alias: ""
published_date: "2026-02-14T08:47:00+00:00"
all_tags: "[\"blog\", \"coding\"]"
publish: "True"
make_discoverable: "True"
is_page: "False"
canonical_url: ""
meta_description: ""
meta_image: "https://bear-images.sfo2.cdn.digitaloceanspaces.com/justasimpleapp/boost-iosw-app2.webp"
lang: en
class_name: ""
first_published_at: "2026-02-14T08:47:00+00:00"
---

Today is the day I launched [my first iOS app](https://justasimple.app/boost/), and that sentence still feels slightly unreal.

A few days ago, I wrote about [falling into a new rabbit hole](/ein-kurzes-winken-aus-dem-kaninchenbau/) of building iOS apps (sorry, German only) and why creating iOS apps has been a quiet dream for a long time. Not in a "startup" or "side hustle" sense, but in the idea of building small, delightful tools that live on a device people carry every day. Tools that feel calm, intentional, and finished.

For years, that idea stayed abstract. Even with a few Swift courses during Covid, my skills weren’t enough to deliver on what were probably overly ambitious ideas. And then there also was just everything else, work, family, life.

Today, with coding assistants capable of generating large parts of an app, the entry barrier felt low enough that I decided to try again.

---

Coding assistants are incredibly good at getting ideas onto the screen, and the generated code is often surprisingly solid. In my experience, it helps if you understand the fundamentals such as software architecture, how user interfaces are composed, and how system permissions work.

I personally believe that understanding your own code is essential. Without that, a codebase quickly becomes overly complex once exceptions and edge cases accumulate. Keeping an app well-structured and efficient still requires human judgment.

But the most important aspect is, that you need to understand the core use-case of your app and really try to focus on that as clearly as possible. Keep away from adding more and more features, just because it's cheap. This will in the end kill your app.

---

A lot of this experience was surprisingly fun, at least most of the time. But a few things nearly killed the project.

Widgets for example look simple, but they are not. Once they become interactive, they are essentially small apps with their own constraints.

Making them work reliably meant sharing core logic and data with the main app, without corrupting the database along the way. It took time to understand that properly, and I also realized why many apps simply don’t offer widgets at all.

Another beast is notifications. Getting notifications to show up is easy. Getting them to be *reliable* is not, at least if you don’t want to run servers to manage notifications for users, which I don’t.

In particular, badge counts turned out to be more subtle than expected. After several evenings of trial and error, the final solution felt obvious in hindsight, which is usually a sign that the learning actually stuck.

And then there was the whole Apple developer experience. App Store Connect, at least to me, feels like a CRM from the 90s. It’s easy to get lost in its many sections, nested views, and hidden requirements. Adding in-app purchases, even when they are purely voluntary donations, comes with a surprising amount of bureaucracy.

The App Store review process itself also requires patience. Reviews take time, and feedback can be very detailed. That said, Apple clearly takes this responsibility seriously. I genuinely appreciate that. The strict review process enforces a minimum level of quality across the platform.

This becomes especially noticeable when working with Apple Health. If you want to read or write Health data, Apple is extremely precise about user flows, wording, and disclosure. Every screen, every explanation, every sentence matters.

This all can be exhausting, but it also explains why the platform works the way it does.

## Bottom line

Putting something together that just works is easy.
Putting something together that *works reliably* across edge cases and offers a good experience throughout the core use cases is hard work.

In that sense, it does help to be a perfectionist, at least about the things that matter. And that difference mattered more than I expected.