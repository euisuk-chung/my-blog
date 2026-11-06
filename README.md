# project1 — 매일 아침 AI 기업 소식 블로그

프로젝트 1의 시작 저장소입니다. 이 폴더를 복사해 내 GitHub 계정의 새 저장소로 올리고, GitHub Pages 로 빈 블로그를 엽니다.
`project1` 아래 번호 폴더는 차시마다의 시작 상태 전체입니다. 앞 실습을 끝내지 못했으면 그 폴더를 통째로 복사해 따라잡습니다.

| 파일 | 하는 일 |
|---|---|
| `make_site.py` | `posts/` 의 글로 블로그 페이지 `docs/` 를 만든다. 글이 없으면 「아직 올라온 글이 없습니다.」만 적는다 |
| `docs/` | GitHub Pages 가 올리는 폴더. `.nojekyll` 은 다른 변환 없이 그대로 올리라는 표시 |
| `runner.py` | `graph.yaml` 을 읽어 단계를 차례로 실행하는 runner |
| `examples/PLAN.md` | 과제 · 핵심 세 줄 · 조건마다 반영할 설정과 파일 |
| `examples/graph.yaml` | 수집 → 작성 → 검사 → 승인 graph 초안. 단계 파일이 아직 없어 실행하지 않는다 |
| `examples/CLAUDE.md` | 내 독자 · 말투 · 하지 말 것 |

## 내 저장소로 옮기기

```bash
cd ~
cp -r harness-practice/project1/09 my-blog
cd my-blog
cp examples/PLAN.md examples/graph.yaml examples/CLAUDE.md .
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
