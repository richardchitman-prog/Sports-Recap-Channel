---
layout: default
title: Home
---

# Daily Sports Recap

NBA, NFL, and MLB -- every day, a short recap video and a written breakdown of the
scores, standout performers, and links to the official league highlight reels.

<ul>
{% for post in site.posts %}
  <li>
    <a href="{{ post.url | relative_url }}">{{ post.title }}</a>
    <span> -- {{ post.date | date: "%B %d, %Y" }}</span>
  </li>
{% endfor %}
</ul>
