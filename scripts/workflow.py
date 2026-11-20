"""Validate, snapshot and explicitly migrate delivery rules."""
import argparse
import difflib
import hashlib
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RULES = ROOT / "skills" / "creek-delivery" / "references"
SYNC_PROTOCOL = (
    "用户确认绑定到目标项目、完整清单版本和内容摘要",
    "更换目标项目或清单内容发生变化时，原确认失效，展示完整新清单并重新确认",
    "逐条先登记写入中，再调用实际工具",
    "恢复时跳过已成功项",
    "先按远端 ID 或稳定标记查询",
    "无法判定、冲突或多重匹配标记待核对，停止该项",
)


def validate(config):
    stages = {s["id"]: s for s in config["stages"]}
    if len(stages) != len(config["stages"]) or not config["version"]:
        raise ValueError("Duplicate stage or missing version")
    entry = config["entry"]
    if entry not in stages or stages[entry]["dependencies"]:
        raise ValueError("Invalid entry")
    done = set()
    while len(done) < len(stages):
        ready = set()
        for key, stage in stages.items():
            deps = set(stage["dependencies"])
            if stage["role"] not in config["roles"] or not stage["artifact"] or not stage["pause"]:
                raise ValueError(f"Incomplete stage {key}")
            if key != entry and not deps:
                raise ValueError(f"Unreachable stage {key}")
            if deps <= done:
                ready.add(key)
        if ready <= done:
            raise ValueError("Cycle or unknown dependency")
        done.update(ready)
    for kind in ("case", "defect"):
        gate = f"{kind}-confirm"
        sync = stages.get(f"{kind}-sync", {})
        if gate not in stages or gate not in sync.get("dependencies", []):
            raise ValueError(f"Missing confirmation for {kind}")
        sources = set()
        pending = list(stages[gate]["dependencies"])
        while pending:
            ancestor = pending.pop()
            if ancestor not in sources:
                sources.add(ancestor)
                pending.extend(stages[ancestor]["dependencies"])
        required = "cases" if kind == "case" else "regression"
        if required not in sources:
            raise ValueError(f"{gate} requires completed {required}")
        if stages[gate]["artifact"] != f"{kind}-approval" or stages[gate]["role"] != "orchestrator":
            raise ValueError(f"Invalid approval owner or artifact for {kind}")
    for stage in stages.values():
        if stage["role"] == "sync" and stage["id"] not in {"case-sync", "defect-sync"}:
            raise ValueError("Remote writes require a recognized approval gate")


def bundle():
    config = json.loads((ROOT / "workflows/workflow.json").read_text(encoding="utf8"))
    validate(config)
    rules = {p.name: p.read_text(encoding="utf8") for p in sorted(RULES.glob("*.md"))}
    expected = {"intake", "run-records", "agents", "development", "yunxiao", "testing", "delivery", "测试计划模板", "测试用例模板", "需求与资料核对表模板", "缺陷记录与回归表模板"}
    if any(not rules.get(name + ".md", "").strip() for name in expected):
        raise ValueError("Missing rule")
    entry = (RULES.parent / "SKILL.md").read_text(encoding="utf8")
    for instruction in SYNC_PROTOCOL:
        if instruction not in entry or instruction not in rules["yunxiao.md"]:
            raise ValueError(f"Missing mandatory sync instruction: {instruction}")
    return json.dumps({"workflow": config, "entry": entry, "rules": rules}, indent=2, ensure_ascii=False) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["check", "start", "resume", "diff", "migrate"])
    parser.add_argument("batch", nargs="?", type=Path)
    parser.add_argument("--confirmed-diff")
    args = parser.parse_args()
    if args.action == "check":
        bundle()
        return
    if not args.batch:
        parser.error("Batch directory required")
    path = args.batch
    pointer = path / "current"
    history = []
    if args.action == "start":
        new = bundle()
        path.mkdir(parents=True, exist_ok=False)
    else:
        previous = pointer.read_text(encoding="ascii").strip()
        if previous.startswith("{"):
            state = json.loads(previous)
            previous = state["snapshot"]
            history = state["migrations"]
        old = (path / previous).read_text(encoding="utf8")
        if hashlib.sha256(old.encode()).hexdigest() != previous:
            raise ValueError("Snapshot integrity failure")
        if args.action == "resume":
            print(old)
            return
        new = bundle()
        delta = "".join(difflib.unified_diff(old.splitlines(True), new.splitlines(True)))
        if not delta:
            print("No changes")
            return
        token = hashlib.sha256(delta.encode()).hexdigest()
        if args.action == "diff":
            print(delta, token, sep="\n")
            return
        if args.confirmed_diff != token:
            parser.error("Confirmed diff digest required")
    digest = hashlib.sha256(new.encode()).hexdigest()
    (path / digest).write_text(new, encoding="utf8")
    if args.action == "migrate":
        history.append({"from": previous, "to": digest, "diff": token})
        state_text = json.dumps({"snapshot": digest, "migrations": history})
    else:
        state_text = digest
    pending = path / "current.tmp"
    pending.write_text(state_text, encoding="ascii")
    os.replace(pending, pointer)


if __name__ == "__main__":
    main()
