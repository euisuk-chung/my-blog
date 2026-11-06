# project1 — 매일 아침 AI 기업 소식 블로그

프로젝트 1 블로그의 수집 · 작성 단계를 더한 상태입니다. graph 는 수집 → 세기 → 작성까지 실행하고, 초안이 준비되면 멈춥니다.
`project1` 아래 번호 폴더는 차시마다의 시작 상태 전체입니다. 앞 실습을 끝내지 못했으면 그 폴더를 통째로 복사해 따라잡습니다.

| 파일 | 하는 일 |
|---|---|
| `make_site.py` | `posts/` 의 글로 블로그 페이지 `docs/` 를 만든다. 글이 없으면 「아직 올라온 글이 없습니다.」만 적는다 |
| `docs/` | GitHub Pages 가 올리는 폴더. `.nojekyll` 은 다른 변환 없이 그대로 올리라는 표시 |
| `runner.py` | `graph.yaml` 을 읽어 단계를 차례로 실행하는 runner |
| `examples/PLAN.md` | 과제 · 핵심 세 줄 · 조건마다 반영할 설정과 파일 |
| `examples/graph.yaml` | 수집(collect) → 세기(count) → 작성(write) graph. 초안 `draft.md` 가 준비되면 멈춘다 |
| `examples/CLAUDE.md` | 내 독자 · 말투 · 하지 말 것 |
| `examples/settings.json` | hook 을 거는 설정. `.claude/settings.json` 으로 복사한다 |
| `prompts/collect.md` | 수집 프롬프트 — 지난 24시간 · 세 회사 공식 사이트(OpenAI 는 RSS 피드) · 원문을 `runs/<날짜>/sources/` 에 · 답은 `sources.json` |
| `prompts/write.md` | 작성 프롬프트 — 숫자 · 인용은 원문 파일에 있는 것만 · 뉴스레터 형식 · 주장 목록 · 뺀 소식(제목 · 원문 · 이유) |
| `steps/count.py` | `sources.json` 의 status 로 갈 곳을 정한다 — 새 글 있음 0(error 칸에 적힌 것이 있으면 함께 찍음) · 새 글 0건 4 · 수집 실패 1(수집을 다시) |
| `.claude/hooks/protect.py` | collect 단계만 `runs/<날짜>/sources/` 에 쓰게 하는 PreToolUse hook. 막을 때 exit code 2 |
| `fixtures/` | Claude 를 부르지 않고 시험하는 입력 — 새 글 0건 · 수집 오류 · 일부 사이트만 확인한 수집 결과 · hook 에 넣을 도구 호출 둘 |

## 내 저장소로 옮기기

```bash
cd ~
cp -r harness-practice/project1/10 my-blog
cd my-blog
cp examples/PLAN.md examples/graph.yaml examples/CLAUDE.md .
cp examples/settings.json .claude/settings.json
uv sync
uv run python make_site.py
```

`CLAUDE.md` 의 독자와 말투는 내 블로그에 맞게 고칩니다. 그다음 Git 저장소로 만들어 GitHub 에 올립니다.

```bash
git init -b main
git add .
git commit -m "블로그 시작"
gh repo create my-blog --public --source=. --push
```

GitHub 의 저장소 화면에서 Settings → Pages 로 가서, Build and deployment 의 Source 를 Deploy from a branch 로 두고 branch 는 `main`, 폴더는 `/docs` 로 골라 Save 를 누릅니다. 잠시 뒤 `https://<아이디>.github.io/my-blog/` 에 빈 블로그가 열립니다.

내 컴퓨터에서 먼저 보려면 `uv run python -m http.server 8001 --directory docs` 를 실행하고 브라우저로 `http://localhost:8001` 을 엽니다. 끝낼 때는 `Ctrl+C` 를 누릅니다.

## 앞 차시 폴더에서 이어 받기

이미 `~/my-blog` 가 있으면 이번에 더해지거나 바뀐 것만 복사하고, graph 와 설정 파일을 제자리에 둡니다.

```bash
cd ~/harness-practice/project1/10
cp -r prompts steps fixtures examples .claude .gitignore README.md ~/my-blog/
cd ~/my-blog
cp examples/graph.yaml graph.yaml
cp examples/settings.json .claude/settings.json
```

번호 폴더에는 `.git` 도, 맨 위의 `CLAUDE.md` · `PLAN.md` · `graph.yaml` 도 없습니다. 그래서 `cp -r ~/harness-practice/project1/10/. ~/my-blog/` 처럼 폴더 안을 통째로 덮어써도 내 Git 기록과 고쳐 둔 `CLAUDE.md` 는 그대로 남습니다.
`cp -r harness-practice/project1/10 my-blog` 는 `my-blog` 가 이미 있으면 그 안에 `10` 폴더를 새로 만드니, 이미 있는 폴더에는 쓰지 않습니다.

## 실행

```bash
uv run python runner.py                                         # 수집 → 세기 → 작성 — Claude 를 두 번 부릅니다
uv run python runner.py --answer fixtures/empty.json            # 새 글 0건 — count 가 exit code 4, 작성 없이 끝
uv run python runner.py --answer fixtures/collect-error.json    # 수집 오류 — 수집을 세 번 하고 human queue 에 남김
RUNNER_STEP=write uv run python .claude/hooks/protect.py < fixtures/hook-edit-source.json   # hook 만 시험 — exit code 2
uv run python steps/count.py fixtures/partial-sources.json       # 일부 사이트만 확인한 날 — 새 글이 있으니 0, error 칸을 함께 찍음
```

원문은 `runs/<날짜>/sources/` 에 남고, 그날의 수집 결과 `sources.json` 과 초안 `draft.md` 는 Git 에 올리지 않습니다.
