"""PreToolUse hook — 수집 단계만 runs/<날짜>/sources/ 에 원문을 쓰게 한다.

Claude Code 는 Edit·Write 도구를 쓰기 직전에 이 스크립트를 부르고, 그 도구 호출을 JSON 으로 stdin 에 넣어 준다.
지금 단계 이름은 runner 가 넘기는 환경 변수 RUNNER_STEP 으로 본다.
- collect 단계: runs/<날짜>/sources/ 안의 파일만 쓸 수 있다
- 다른 단계, runner 없이 연 Claude: runs/ 아래를 쓰거나 고칠 수 없다 — 수집이 끝난 원문은 확정이다
exit code — 0: 허용 · 2: 막음(이유는 stderr 에). 입력을 읽지 못하거나 어떤 예외가 나도 2 로 막는다(fail-closed).

    RUNNER_STEP=collect uv run python .claude/hooks/protect.py < fixtures/hook-write-source.json   # Claude 없이 직접 시험하기
"""
import json
import os
import re
import sys
from pathlib import Path

SOURCES = re.compile(r"runs/\d{4}-\d{2}-\d{2}/sources/[^/]+")


def block(reason):
    print(reason, file=sys.stderr)
    sys.exit(2)


def main():
    data = json.loads(sys.stdin.read())
    cwd = Path(data["cwd"]).resolve()
    target = (cwd / data["tool_input"]["file_path"]).resolve()
    path = target.relative_to(cwd).as_posix()       # 폴더 밖이면 여기서 예외 → 막음
    step = os.environ.get("RUNNER_STEP", "")
    if step == "collect":
        if not SOURCES.fullmatch(path):
            block(f"막음 — collect 단계는 runs/<날짜>/sources/ 에만 씁니다: {path}")
        sys.exit(0)
    if path == "runs" or path.startswith("runs/"):
        block(f"막음 — 수집이 끝난 원문은 고치지 않습니다(지금 단계: {step or '없음'}): {path}")
    sys.exit(0)


try:
    main()
except Exception as e:
    block(f"막음 — hook 이 입력을 읽지 못했습니다: {type(e).__name__}")
