"""posts/ 의 글로 블로그 페이지(docs/)를 만든다.

    uv run python make_site.py

posts/ 의 YYYY-MM-DD.md 하나가 글 한 편이다. 글마다 docs/YYYY-MM-DD.html 을 만들고,
docs/index.html 에 최근 글부터 목록을 적는다. 글이 없으면 「아직 올라온 글이 없습니다.」만 적는다.
GitHub Pages 는 main 브랜치의 docs/ 폴더를 그대로 올린다(docs/.nojekyll — 다른 변환 없이 그대로).
"""
import html
from pathlib import Path

import markdown

TITLE = "내 블로그 — AI 기업 소식"
POSTS, DOCS = Path("posts"), Path("docs")

PAGE = """<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<style>
body {{ max-width: 42rem; margin: 3rem auto; padding: 0 1rem; font-family: system-ui, sans-serif; line-height: 1.7; color: #222; }}
header a {{ color: inherit; text-decoration: none; }}
a {{ color: #0b57d0; }}
li {{ margin: .4rem 0; }}
</style>
</head>
<body>
<header><h1><a href="./">{site}</a></h1></header>
{body}
</body>
</html>
"""


def page(title, body):
    return PAGE.format(title=html.escape(title), site=html.escape(TITLE), body=body)


def main():
    DOCS.mkdir(exist_ok=True)
    posts = sorted(POSTS.glob("*.md"), reverse=True) if POSTS.exists() else []
    items = []
    for post in posts:
        text = post.read_text(encoding="utf-8")
        head = text.strip().splitlines()[0].lstrip("# ").strip() if text.strip() else post.stem
        (DOCS / f"{post.stem}.html").write_text(page(head, markdown.markdown(text)), encoding="utf-8")
        items.append(f'<li>{post.stem} · <a href="{post.stem}.html">{html.escape(head)}</a></li>')
    body = "<ul>\n" + "\n".join(items) + "\n</ul>" if items else "<p>아직 올라온 글이 없습니다.</p>"
    (DOCS / "index.html").write_text(page(TITLE, body), encoding="utf-8")
    print(f"docs/index.html 을 만들었습니다 — 글 {len(posts)}편")


if __name__ == "__main__":
    main()
