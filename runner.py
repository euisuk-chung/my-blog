"""graph 파일을 읽어 단계를 차례로 실행한다(runner).

    uv run python runner.py                                    # graph.yaml 로 실행
    uv run python runner.py --answer fixtures/no-member.json   # Claude 대신 저장해 둔 응답을 쓴다

단계는 두 가지다.
- claude 단계: 프롬프트 파일로 `claude -p` 를 한 번 부르고, 답(result)을 output 파일에 쓴다
- run 단계: 명령을 실행하고 exit code 를 읽는다 — 0 통과 · 1 거부(이유를 찍는다) · 3 사람에게 · 4 할 일 없음

단계를 마칠 때마다 상태를 state.json 에 남긴다. 멈췄다가 다시 실행하면 거기서 이어 간다.
exit code — 0: 끝 · 1: 실패(graph 오류, 예상하지 못한 결과) · 3: 사람 차례(human_queue/ 에 남김)
"""
import argparse
import json
import os
import shlex
import subprocess
import sys
import time
from pathlib import Path

import yaml

STATE = Path("state.json")
QUEUE = Path("human_queue")
RETRY = "앞 결과(draft.md)가 거부된 이유: {reason}. 이 이유만 고치세요."


def load_graph(path):
    """graph 를 읽고, 갈 곳으로 적은 단계가 모두 있는지 먼저 본다."""
    graph = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    names = set(graph["steps"]) | {"end"}
    for name, step in graph["steps"].items():
        for key in ("next", "on_reject"):
            if key in step and step[key] not in names:
                sys.exit(f"graph 오류 — {name} 의 {key}: {step[key]} 라는 단계가 없습니다")
    if graph["start"] not in names:
        sys.exit(f"graph 오류 — start: {graph['start']} 라는 단계가 없습니다")
    return graph


def load_state(path, graph):
    """같은 graph 로 실행하다 멈춘 state.json 이 있으면 이어 가고, 없으면 새로 시작한다."""
    if STATE.exists():
        state = json.loads(STATE.read_text(encoding="utf-8"))
        if state["status"] == "running" and state["graph"] == path:
            print(f"state.json 에서 이어 갑니다 — 다음 단계 {state['step']}")
            return state
    return {"graph": path, "status": "running", "step": graph["start"],
            "attempts": {}, "reason": "", "last": "", "history": []}


def save(state):
    STATE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def run_claude(step, graph, state, answer, env):
    """claude -p 를 한 번 부른다. 결과: ok · error(호출 실패) · human(권한이 막힘)."""
    prompt = Path(step["claude"]).read_text(encoding="utf-8")
    if state["reason"]:
        prompt += "\n\n" + graph.get("retry_prompt", RETRY).format(reason=state["reason"])
    if answer:
        out = Path(answer).read_text(encoding="utf-8")
    else:
        cmd = ["claude", "-p", prompt, "--output-format", "json"] + step.get("args", [])
        out = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", env=env).stdout
    try:
        reply = json.loads(out)
    except json.JSONDecodeError:
        return "error", "claude 의 응답을 읽을 수 없습니다"
    if reply.get("is_error"):
        return "error", f"claude 호출이 실패했습니다 — {reply.get('result', '')}"
    if reply.get("permission_denials"):
        tools = ", ".join(d.get("tool_name", "?") for d in reply["permission_denials"])
        return "human", f"권한이 막혔습니다 — {tools}"
    Path(step["output"]).write_text(reply["result"], encoding="utf-8")
    return "ok", ""


def run_command(step, env):
    """명령을 실행한다. 결과: ok · reject(거부 이유) · human · nothing(할 일 없음) · fail."""
    done = subprocess.run(shlex.split(step["run"]), capture_output=True, text=True,
                          encoding="utf-8", env=env)
    said = " / ".join(line.removeprefix("거부 — ") for line in done.stdout.splitlines() if line.strip())
    if done.returncode == 0:
        return "ok", ""
    if done.returncode == 1 and said:
        return "reject", said
    if done.returncode == 3:
        return "human", said or "단계가 사람에게 넘겼습니다"
    if done.returncode == 4:
        return "nothing", said or "할 일이 없습니다"
    return "fail", f"{step['run']} 이 exit code {done.returncode} 로 끝났습니다 {done.stderr.strip()[-200:]}"


def to_human(state, name, why):
    """human_queue/<단계>.json 에 남기고 3 으로 끝낸다."""
    QUEUE.mkdir(exist_ok=True)
    item = {"step": name, "attempts": state["attempts"].get(name, 0), "why": why}
    (QUEUE / f"{name}.json").write_text(json.dumps(item, ensure_ascii=False, indent=2), encoding="utf-8")
    state["status"] = "human"
    save(state)
    print(f"[{name}] 사람에게 넘깁니다: {why}")
    print(f"human_queue/{name}.json 에 남겼습니다 · exit code 3")
    return 3


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("graph", nargs="?", default="graph.yaml")
    ap.add_argument("--answer", help="claude 를 부르지 않고 이 파일을 응답으로 쓴다(fixture)")
    a = ap.parse_args()
    graph = load_graph(a.graph)
    state = load_state(a.graph, graph)
    limit = graph.get("max_attempts", 1)          # 적지 않으면 한 번만 실행한다
    wait = graph.get("backoff_seconds", 1)

    while state["step"] != "end":
        name = state["step"]
        step = graph["steps"][name]
        missing = [f for f in step.get("needs", []) if not Path(f).exists()]
        if missing:                                # 입력 문제 — 다시 해도 같다
            return to_human(state, name, f"입력 파일이 없습니다: {', '.join(missing)}")
        tried = state["attempts"].get(name, 0)
        if tried >= limit:                         # max attempts 는 첫 시도를 포함해 센다
            return to_human(state, name, f"{tried}번 실행했습니다(max_attempts {limit}). 마지막 이유: {state['last']}")
        state["attempts"][name] = tried + 1
        save(state)
        print(f"[{name}] {tried + 1}번째 실행")
        env = dict(os.environ, RUNNER_STEP=name, RUNNER_ATTEMPT=str(tried + 1))
        if "claude" in step:
            result, why = run_claude(step, graph, state, a.answer, env)
        else:
            result, why = run_command(step, env)
        state["history"].append({"step": name, "attempt": tried + 1, "result": result, "why": why})
        state["last"] = why

        if result == "ok":                         # 통과 — 다음 단계로
            if "claude" in step:
                state["reason"] = ""
            state["step"] = step.get("next", "end")
        elif result == "reject":                   # 품질 거부 — 이유를 붙여 다시 쓰게
            print(f"[{name}] {why}")
            if "on_reject" not in step:
                result, why = "fail", f"{name} 이 거부했지만 on_reject 가 없습니다"
            else:
                state["reason"] = why
                state["step"] = step["on_reject"]
        elif result == "error":                    # 일시적 호출 실패 — 기다렸다 같은 단계를 다시
            print(f"[{name}] {why}")
            if tried + 1 < limit:
                pause = wait * 2 ** tried              # backoff — 기다리는 시간을 두 배씩
                print(f"[{name}] {pause}초 기다렸다 다시 부릅니다")
                save(state)
                time.sleep(pause)
        elif result == "human":                    # 입력·권한 문제 — 바로 사람에게
            return to_human(state, name, why)
        elif result == "nothing":                  # 할 일 없음 — 남은 단계를 건너뛰고 정상으로 끝낸다
            print(f"[{name}] 할 일이 없어 끝냅니다: {why}")
            state["step"] = "end"
        if result == "fail":
            state["status"] = "failed"
            save(state)
            print(f"[{name}] 실패 — {why} · exit code 1")
            return 1
        save(state)

    state["status"] = "done"
    save(state)
    print("끝 — exit code 0")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n멈췄습니다 — 다시 실행하면 state.json 에서 이어 갑니다")
        sys.exit(130)
