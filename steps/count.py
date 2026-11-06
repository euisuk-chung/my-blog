"""수집 결과 sources.json 을 읽어 다음에 갈 곳을 정한다.

    uv run python steps/count.py sources.json

exit code — 0: 새 글이 있다 · 1: 거부(수집을 다시) · 4: 새 글 0건(할 일 없음, 남은 단계를 건너뛴다)
가져온 글이 있으면 error 칸에 적힌 것(보지 못한 곳 등)이 있어도 0 — 그 글을 함께 찍는다
"""
import json
import sys
from pathlib import Path

NEED = ("id", "url", "published", "fetched_at", "file")


def main(path):
    try:
        found = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        print(f"거부 — {path} 를 JSON 으로 읽지 못했습니다({type(e).__name__})")
        return 1
    status = found.get("status")
    if status == "empty":                     # 세 곳을 다 봤고 새 글이 없다 — 실패가 아니다
        print("새 글 0건 — 오늘은 올릴 글이 없습니다")
        return 4
    if status == "error":                     # 보지 못한 곳이 있다 — 0건이라고 말할 수 없다
        print(f"거부 — 수집이 실패했습니다: {found.get('error') or '이유가 적혀 있지 않습니다'}")
        return 1
    if status != "ok":
        print(f"거부 — status 는 ok · empty · error 가운데 하나여야 합니다: {status}")
        return 1
    items = found.get("items") or []
    if not items:
        print("거부 — status 는 ok 인데 items 가 비었습니다")
        return 1
    for item in items:
        lack = [key for key in NEED if not item.get(key)]
        if lack:
            print(f"거부 — {item.get('id', '?')} 에 {', '.join(lack)} 이 없습니다")
            return 1
        if not Path(item["file"]).is_file():
            print(f"거부 — 원문 파일이 없습니다: {item['file']}")
            return 1
    if found.get("error"):                    # 가져온 글은 있고 error 칸에도 적힌 것이 있다 — 넘기되 그 글을 보인다
        print(f"새 글 {len(items)}건 — error 칸: {found['error']}")
    else:
        print(f"새 글 {len(items)}건")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
