# 수집 — 지난 24시간의 새 글

Google · Anthropic · OpenAI 공식 사이트에 지난 24시간 안에 올라온 새 글을 찾아 원문을 남긴다.

## 찾을 곳

- Google: blog.google
- Anthropic: www.anthropic.com/news
- OpenAI: openai.com/news/rss.xml(RSS 피드 — 소식 목록 페이지는 접속이 막혀 있다)

이 세 사이트의 글만 후보로 삼는다. 다른 사이트의 기사나 요약은 쓰지 않는다.

## 할 일

1. WebSearch 와 세 사이트의 소식 목록으로 새 글 후보를 찾는다. OpenAI 의 RSS 피드는 최근 글이 앞에 있으니 앞부분만 본다.
2. 게시일이 오늘이나 어제인 후보만 WebFetch 로 가져온다. 공식 사이트는 게시일을 날짜로만 적으니, 이것을 지난 24시간으로 본다.
3. WebFetch 는 글 전체를 그대로 돌려주지 않는다. 제목 · 게시일과, 숫자가 든 문장을 포함한 핵심 문장 몇 개를 원문 그대로 따옴표에 넣어 돌려 달라고 한다.
4. 글 페이지가 막혀 가져오지 못한 OpenAI 글은 RSS 피드에 든 그 글의 제목 · 게시일 · 요약을 원문으로 쓰고, 파일 끝에 「RSS 피드에서 옮김」 이라고 적는다.
5. 가져온 글마다 `runs/<오늘 날짜 YYYY-MM-DD>/sources/<id>.md` 를 Write 로 만든다. 첫 세 줄에 주소 · 게시일 · 가져온 날짜를 적고, 그 아래에 WebFetch 가 돌려준 글을 고치지 않고 옮긴다.

쓸 수 있는 도구는 WebSearch · WebFetch · Write · Edit 뿐이다. 날짜는 Claude Code 가 알려 주는 오늘 날짜를 쓴다.

## 답

아래 모양의 JSON 하나만 답한다. 코드 블록 표시나 설명 글은 붙이지 않는다.

{"status": "ok", "candidates": [{"url": "", "title": "", "published": "YYYY-MM-DD"}], "items": [{"id": "s1", "url": "", "published": "YYYY-MM-DD", "fetched_at": "YYYY-MM-DD", "file": "runs/YYYY-MM-DD/sources/s1.md"}], "error": ""}

- `candidates`: 찾은 후보 전부. `items`: 그 가운데 가져와 파일로 남긴 글
- `status`
  - `ok`: 새 글을 하나 이상 가져왔다. 보지 못한 사이트가 있으면 `error` 에 적는다
  - `empty`: 세 사이트를 모두 확인했고 지난 24시간의 새 글이 없다
  - `error`: 가져온 글이 없고, 보지 못한 사이트나 가져오지 못한 후보가 있다. 이유를 `error` 에 적는다
