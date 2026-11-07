# project1 — 매일 아침 AI 기업 소식 블로그

프로젝트 1 블로그의 검사 · 승인 단계를 더한 상태입니다. graph 는 수집 → 세기 → 작성 → 검사 → 승인까지 실행하고, 승인 단계가 PR 을 연 뒤 멈춥니다. PR 을 읽고 합치는 일은 내가 GitHub 에서 합니다.
`project1` 아래 번호 폴더는 차시마다의 시작 상태 전체입니다. 앞 실습을 끝내지 못했으면 그 폴더를 통째로 복사해 따라잡습니다.

| 파일 | 하는 일 |
|---|---|
| `make_site.py` | `posts/` 의 글로 블로그 페이지 `docs/` 를 만든다. 글이 없으면 「아직 올라온 글이 없습니다.」만 적는다 |
| `docs/` | GitHub Pages 가 올리는 폴더. `.nojekyll` 은 다른 변환 없이 그대로 올리라는 표시 |
| `runner.py` | `graph.yaml` 을 읽어 단계를 차례로 실행하는 runner |
| `examples/PLAN.md` | 과제 · 핵심 세 줄 · 조건마다 반영할 설정과 파일 |
| `examples/graph.yaml` | 수집(collect) → 세기(count) → 작성(write) → 검사(check) → 승인(approve) graph. 검사가 거부하면 이유를 붙여 작성을 다시, 승인 단계가 PR 을 열면 exit code 3 으로 멈춘다 |
| `examples/graph-retry.yaml` | 작성 → 검사만 있는 연습 graph. 다시 쓰기와 human queue 를 PR 없이 시험한다 |
| `examples/CLAUDE.md` | 내 독자 · 말투 · 하지 말 것 |
| `examples/settings.json` | hook 을 거는 설정. `.claude/settings.json` 으로 복사한다 |
| `prompts/collect.md` | 수집 프롬프트 — 지난 24시간 · 세 회사 공식 사이트(OpenAI 는 RSS 피드) · 원문을 `runs/<날짜>/sources/` 에 · 답은 `sources.json` |
| `prompts/write.md` | 작성 프롬프트 — 숫자 · 인용은 원문 파일에 있는 것만 · 뉴스레터 형식 · 주장 목록 · 뺀 소식(제목 · 원문 · 이유) |
| `steps/check.py` | 검사 다섯 — 구조 · 출처와 기간 · 원문 대조(숫자 · 인용) · 형식 · 근거. 통과 0 · 거부 1(이유를 찍는다) |
| `steps/approve.py` | 초안의 글을 `posts/<날짜>.md` 로 쓰고 `docs/` 를 다시 만든 뒤, branch `draft/<날짜>` 를 push 하고 PR 을 연다. `needs_approval` 을 찍고 exit code 3 |
| `steps/count.py` | `sources.json` 의 status 로 갈 곳을 정한다 — 새 글 있음 0(error 칸에 적힌 것이 있으면 함께 찍음) · 새 글 0건 4 · 수집 실패 1(수집을 다시) |
| `.claude/hooks/protect.py` | collect 단계만 `runs/<날짜>/sources/` 에 쓰게 하는 PreToolUse hook. 막을 때 exit code 2 |
| `fixtures/` | Claude 를 부르지 않고 시험하는 입력 — 새 글 0건 · 수집 오류 · 일부 사이트만 확인한 수집 결과 · hook 에 넣을 도구 호출 둘 · 틀린 인용 초안을 내는 작성 응답(`wrong-quote.json`) · 검사 단계에서 이어 가는 상태(`state-retry.json`) |
| `fixtures/check/` | 검사 시험용 — 수집 결과와 원문 셋, 통과하는 초안 하나(`good.md`), 검사마다 거부되는 초안 다섯. 원문 `s1.md` 는 실제로 가져온 글이고, 날짜만 시험용으로 바꿨다 |

## 내 저장소로 옮기기

```bash
cd ~
cp -r harness-practice/project1/11 my-blog
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

이미 `~/my-blog` 가 있으면 이번에 더해지거나 바뀐 것만 복사하고, graph 를 제자리에 둡니다.

```bash
cd ~/harness-practice/project1/11
cp -r steps fixtures examples .gitignore README.md ~/my-blog/
cd ~/my-blog
cp examples/graph.yaml graph.yaml
```

번호 폴더에는 `.git` 도, 맨 위의 `CLAUDE.md` · `PLAN.md` · `graph.yaml` 도 없습니다. 그래서 `cp -r ~/harness-practice/project1/11/. ~/my-blog/` 처럼 폴더 안을 통째로 덮어써도 내 Git 기록과 고쳐 둔 `CLAUDE.md` 는 그대로 남습니다.
`cp -r harness-practice/project1/11 my-blog` 는 `my-blog` 가 이미 있으면 그 안에 `11` 폴더를 새로 만드니, 이미 있는 폴더에는 쓰지 않습니다.

## 실행

```bash
uv run python steps/check.py fixtures/check/good.md fixtures/check/sources.json          # 검사 다섯 통과 — exit code 0
uv run python steps/check.py fixtures/check/wrong-quote.md fixtures/check/sources.json   # 틀린 인용 — 거부 이유를 찍고 exit code 1
cp fixtures/check/sources.json sources.json
uv run python runner.py examples/graph-retry.yaml --answer fixtures/wrong-quote.json     # 세 번 다시 써도 거부 — human queue · exit code 3
cp fixtures/check/wrong-quote.md draft.md
cp fixtures/state-retry.json state.json
uv run python runner.py examples/graph-retry.yaml                                        # 틀린 인용을 Claude 가 다시 쓴다 — Claude 를 한 번 이상 부릅니다
uv run python runner.py                                                                  # 수집 → 승인 — PR 을 열고 exit code 3
```

검사 fixture 는 `bad-structure` · `bad-source` · `wrong-quote` · `bad-format` · `bad-claim` 다섯이고, 하나마다 검사 하나가 거부합니다.
승인 단계는 GitHub 저장소(`origin`)와 `gh` 로그인이 있어야 PR 을 엽니다. 열지 못하면 이유를 찍고 같은 exit code 3 으로 멈춥니다.
PR 을 합치면 GitHub Pages 가 main 의 `docs/` 를 올립니다. 합친 뒤에는 `git pull` 로 내 컴퓨터의 main 도 맞춥니다.
원문은 `runs/<날짜>/sources/` 에 남고, 그날의 수집 결과 `sources.json` · 초안 `draft.md` · PR 본문 `pr-body.md` 는 Git 에 올리지 않습니다.
