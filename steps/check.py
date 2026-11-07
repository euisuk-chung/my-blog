"""검사 단계 — 초안 draft.md 를 수집 결과 sources.json 과 원문 파일에 맞대 다섯 가지를 본다.

    uv run python steps/check.py draft.md sources.json

1 구조       — status 세 줄 · 머리 한 줄 · 소식 · 주장 목록 · 뺀 소식이 정해진 모양인가
2 출처와 기간 — 원문 id · 원문 링크가 items 에 있고, 세 회사 공식 사이트이고, 게시일이 가져온 날이나 그 전날인가
3 원문 대조   — 인용이 그 원문 파일에 글자 그대로 있고, 주장에 든 숫자가 인용에도 있는가
4 형식       — 소식마다 세 문장과 원문 링크 한 줄인가
5 근거       — 소식의 문장마다 주장 목록에 주장으로 올라 있는가
exit code — 0: 통과 · 1: 거부(이유를 찍는다 — runner 가 다시 쓰는 프롬프트에 붙인다)
보지 않는 것: 원문 자체가 사실인지 · 주장과 인용이 같은 뜻인지 · 뺀 소식이 맞게 빠졌는지 — 승인 때 사람이 본다
"""
import json
import re
import sys
from datetime import date, timedelta
from pathlib import Path
from urllib.parse import urlparse

OFFICIAL = {"blog.google", "www.anthropic.com", "openai.com"}
SENTENCE = re.compile(r"(?<=[.!?])\s+")
NUMBER = re.compile(r"\d+(?:[.,]\d+)*")


def same(text):
    """비교할 때만 — 따옴표 모양과 띄어쓰기를 맞춘다."""
    for a, b in (("“", '"'), ("”", '"'), ("‘", "'"), ("’", "'"), ("‑", "-")):
        text = text.replace(a, b)
    return " ".join(text.split()).rstrip(".")


def read_draft(text):
    """초안을 머리 · 소식 · 주장 목록 · 뺀 소식으로 나눈다. 모양이 틀리면 ValueError."""
    lines = text.splitlines()
    if lines[:3] != ["---", "status: ready", "---"]:
        raise ValueError("맨 앞 세 줄이 --- · status: ready · --- 가 아닙니다")
    body = [line for line in lines[3:] if line.strip()]
    if not body or not body[0].startswith("# "):
        raise ValueError("머리 한 줄(# 로 시작)이 없습니다")
    parts, name = {}, None
    for line in body[1:]:
        if line.startswith("## "):
            name = line[3:].strip()
            parts[name] = []
        elif name is None:
            raise ValueError(f"소제목 앞에 글이 있습니다: {line}")
        else:
            parts[name].append(line)
    names = list(parts)
    for need in ("주장 목록", "뺀 소식"):
        if need not in names:
            raise ValueError(f"「## {need}」 이 없습니다")
    if names[-2:] != ["주장 목록", "뺀 소식"] or len(names) < 3:
        raise ValueError("소식 하나 이상 · 주장 목록 · 뺀 소식이 이 차례로 있어야 합니다")
    claims = blocks(parts["주장 목록"], ("- 주장: ", "  원문: ", "  인용: "))
    left = [] if parts["뺀 소식"] == ["- 없음"] else blocks(parts["뺀 소식"], ("- 제목: ", "  원문: ", "  이유: "))
    news = {n: parts[n] for n in names[:-2]}
    return news, claims, left


def blocks(lines, heads):
    """세 줄씩 끊어 읽는다 — 줄 머리가 정해진 대로가 아니면 ValueError."""
    if len(lines) % 3:
        raise ValueError(f"{heads[0].strip()} 목록이 세 줄씩 끊어지지 않습니다")
    out = []
    for i in range(0, len(lines), 3):
        group = lines[i:i + 3]
        for line, head in zip(group, heads):
            if not line.startswith(head):
                raise ValueError(f"「{head.strip()}」 줄이 있어야 할 자리에 다른 줄이 있습니다: {line}")
        out.append([line[len(head):].strip() for line, head in zip(group, heads)])
    return out


def main(draft_path, sources_path):
    found = json.loads(Path(sources_path).read_text(encoding="utf-8"))
    items = {item["id"]: item for item in found.get("items", [])}
    try:
        news, claims, left = read_draft(Path(draft_path).read_text(encoding="utf-8"))   # 1 구조
    except ValueError as e:
        print(f"거부 — [1 구조] {e}")
        return 1
    why = []
    links = {n: lines[-1].removeprefix("원문: ").strip() for n, lines in news.items()
             if lines and lines[-1].startswith("원문: ")}
    urls = {item["url"] for item in items.values()}
    for _, sid, _ in claims:                                                 # 2 출처와 기간
        if sid not in items:
            why.append(f"[2 출처와 기간] 주장의 원문 id {sid} 는 sources.json 의 items 에 없습니다")
    for url in list(links.values()) + [url for _, url, _ in left]:
        if url not in urls:
            why.append(f"[2 출처와 기간] 원문 링크가 sources.json 의 items 에 없습니다: {url}")
    for item in items.values():
        if item["url"] not in set(links.values()) | {url for _, url, _ in left}:
            why.append(f"[2 출처와 기간] 원문 {item['id']} 이 초안에도 뺀 소식에도 없습니다")
        if urlparse(item["url"]).hostname not in OFFICIAL:
            why.append(f"[2 출처와 기간] 원문 {item['id']} 은 세 회사 공식 사이트의 글이 아닙니다: {item['url']}")
        try:
            fetched, published = date.fromisoformat(item["fetched_at"]), date.fromisoformat(item["published"])
        except (KeyError, ValueError):
            why.append(f"[2 출처와 기간] 원문 {item['id']} 의 게시일 · 가져온 날짜를 YYYY-MM-DD 로 읽지 못했습니다")
            continue
        if published not in (fetched, fetched - timedelta(days=1)):
            why.append(f"[2 출처와 기간] 원문 {item['id']} 의 게시일 {item['published']} 이 가져온 날({item['fetched_at']})이나 그 전날이 아닙니다")
    for said, sid, quote in claims:                                          # 3 원문 대조
        if sid not in items:
            continue
        quote = quote[1:-1] if quote[:1] == quote[-1:] == '"' else quote
        try:
            source = Path(items[sid]["file"]).read_text(encoding="utf-8")
        except OSError:
            why.append(f"[3 원문 대조] 원문 파일 {items[sid]['file']} 을 열지 못했습니다")
            continue
        if same(quote) not in same(source):
            why.append(f"[3 원문 대조] 인용이 원문 파일 {sid} 에 없습니다: \"{quote}\"")
        quoted = {n.replace(",", "") for n in NUMBER.findall(quote)}
        for num in NUMBER.findall(said):
            if num.replace(",", "") not in quoted:
                why.append(f"[3 원문 대조] 주장의 숫자 {num} 이 인용에 없습니다: {said}")
    said_all = {same(said) for said, _, _ in claims}
    for name, lines in news.items():
        if not lines or not lines[-1].startswith("원문: "):
            why.append(f"[4 형식] 「{name}」 의 끝에 원문 링크 한 줄이 없습니다")
            continue
        text = " ".join(lines[:-1])
        sentences = [s for s in SENTENCE.split(text) if s.strip()]
        if len(sentences) != 3:                                              # 4 형식
            why.append(f"[4 형식] 「{name}」 은 세 문장이어야 하는데 {len(sentences)}문장입니다")
        for s in sentences:                                                  # 5 근거
            if same(s) not in said_all:
                why.append(f"[5 근거] 주장 목록에 없는 문장입니다: {s}")
    for line in why[:5]:
        print(f"거부 — {line}")
    if why:
        return 1
    print(f"통과 — 다섯 검사 · 소식 {len(news)} · 주장 {len(claims)} · 뺀 소식 {len(left)}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1], sys.argv[2]))
