"""승인 단계 — 검사를 통과한 초안으로 PR 을 열고, 내 승인을 기다린다.

    uv run python steps/approve.py draft.md

1. 초안에서 status 세 줄 · 주장 목록 · 뺀 소식을 떼고, 글만 posts/<오늘>.md 로 쓴다
2. make_site.py 로 docs/ 를 다시 만든다
3. 새 branch draft/<오늘> 에 posts · docs · runs 를 커밋하고 GitHub 에 push 한다
4. 주장 목록 · 뺀 소식을 본문에 담아 main 으로 가는 PR 을 연다
5. needs_approval 을 찍고 exit code 3 — runner 가 human queue 에 남기고 멈춘다
게시는 이 단계가 하지 않는다. 내가 PR 을 읽고 합치면 GitHub Pages 가 main 의 docs/ 를 올린다.
exit code — 3: 사람 차례(PR 을 열었다 · 열지 못했다)
"""
import subprocess
import sys
from datetime import date
from pathlib import Path

BODY = Path("pr-body.md")


def split(text):
    """초안을 글 · 주장 목록 · 뺀 소식으로 나눈다. 검사를 통과한 초안이라 모양은 정해져 있다."""
    body = text.split("\n---\n", 1)[1]
    post, rest = body.split("\n## 주장 목록\n", 1)
    claims, left = rest.split("\n## 뺀 소식\n", 1)
    return post.strip() + "\n", claims.strip(), left.strip()


def run(*args):
    """명령 하나를 실행하고, 실패하면 이유를 담아 멈춘다."""
    done = subprocess.run(args, capture_output=True, text=True, encoding="utf-8")
    if done.returncode != 0:
        raise RuntimeError(f"{' '.join(args[:3])} — {(done.stderr or done.stdout).strip()[-300:]}")
    return done.stdout.strip()


def main(draft_path):
    today = date.today().isoformat()
    post, claims, left = split(Path(draft_path).read_text(encoding="utf-8"))
    head = post.splitlines()[0].lstrip("# ").strip()
    BODY.write_text(
        "검사 다섯(구조 · 출처와 기간 · 원문 대조 · 형식 · 근거)을 통과한 초안입니다.\n\n"
        "검사가 보지 않은 것 — 합치기 전에 사람이 봅니다\n"
        "- 주장과 인용이 같은 뜻인가\n- 뺀 소식이 맞게 빠졌는가\n- 원문 자체가 사실인가\n\n"
        f"## 주장 목록\n\n{claims}\n\n## 뺀 소식\n\n{left}\n", encoding="utf-8")
    try:
        Path("posts").mkdir(exist_ok=True)
        Path(f"posts/{today}.md").write_text(post, encoding="utf-8")
        run(sys.executable, "make_site.py")
        branch = f"draft/{today}"
        run("git", "switch", "-c", branch)
        run("git", "add", "--", *[p for p in ("posts", "docs", "runs") if Path(p).exists()])
        run("git", "commit", "-m", f"{today} 소식 초안")
        run("git", "push", "-u", "origin", branch)
        url = run("gh", "pr", "create", "--base", "main", "--head", branch,
                  "--title", head, "--body-file", str(BODY))
        run("git", "switch", "main")
    except RuntimeError as e:
        print(f"PR 을 열지 못했습니다 — {e}")
        return 3
    print(f"needs_approval — PR 을 열었습니다: {url.splitlines()[-1]}")
    return 3


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
