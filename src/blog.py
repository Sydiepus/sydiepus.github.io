"""Render generated blog pages from parsed post objects."""

from __future__ import annotations

import html

from .page import esc, render_footer, render_head


def render_post(post, site: dict) -> str:
    blog = site["blog"]
    tags = "".join(f"<i>{html.escape(tag)}</i>" for tag in post.tags)
    tags_html = f'<span class="post-tags">{tags}</span>' if tags else ""
    return render_head(
        site,
        f"{post.title} — {blog['title']}",
        post.summary,
        depth=1,
        active="blog",
        page_type="article",
    ) + f"""
<main class="wrap" style="padding-block:clamp(28px,5vw,64px)">
  <article class="article">
    <div class="article-head reveal">
      <p class="article-meta">
        <a href="../blog.html" style="color:inherit">&#9664; {esc(blog["all_posts_label"])}</a>
        &nbsp;&#9654;&nbsp; <time datetime="{post.iso}">{post.pretty}</time>
        &nbsp;&#9654;&nbsp; {post.reading_min} {esc(blog["reading_time_suffix"])}
      </p>
      <h1>{html.escape(post.title)}</h1>
      {tags_html}
    </div>
    <div class="article-body reveal">
{post.html}
    </div>
    <div class="article-nav reveal">
      <a class="btn" href="../blog.html">&#9664; {esc(blog["all_posts_label"])}</a>
      <a class="btn btn-ghost" href="../index.html">{esc(blog["home_label"])}</a>
    </div>
  </article>
</main>
""" + render_footer(site, depth=1) + """
</body>
</html>
"""


def render_index(posts: list, site: dict) -> str:
    blog = site["blog"]
    if posts:
        rows = []
        for post in posts:
            tags = "".join(f"<i>{html.escape(tag)}</i>" for tag in post.tags)
            tags_html = f'<span class="post-tags">{tags}</span>' if tags else ""
            rows.append(f"""      <a class="post reveal" href="{post.url}">
        <span class="post-date"><time datetime="{post.iso}">{post.pretty}</time></span>
        <span>
          <span class="post-title">{html.escape(post.title)}</span>
          <span class="post-sum">{html.escape(post.summary)}</span>
          {tags_html}
        </span>
      </a>""")
        body = f'    <div class="post-list">\n{"\n".join(rows)}\n    </div>'
        label = blog["post_count_label"] if len(posts) == 1 else blog["posts_count_label"]
        count = f"{len(posts):02d} {esc(label)}"
    else:
        body = (
            '    <p class="reveal" style="opacity:.75;font-size:var(--t-lead)">'
            f"{esc(blog['empty_message'])}</p>"
        )
        count = "empty"

    return render_head(site, f"{blog['title']} — {site['site']['name']}",
                       blog["description"], active="blog") + f"""
<main class="wrap" style="padding-block:clamp(28px,5vw,64px)">
  <section>
    <div class="sec-head reveal">
      <h2>{esc(blog["title"])}</h2>
      <span class="micro dim">{count}</span>
    </div>
{body}
  </section>
</main>
""" + render_footer(site) + """
</body>
</html>
"""
