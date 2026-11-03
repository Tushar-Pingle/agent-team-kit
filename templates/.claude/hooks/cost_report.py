#!/usr/bin/env python3
"""Session cost report for the agent team (agent-team-kit).

Sums the tokens of a Claude Code session transcript (JSONL), by model, and
prices them with .claude/hooks/cost.json. Standard library only.

Usage:
  As a SessionEnd hook (reads the hook JSON on stdin, which names the transcript):
    python3 .claude/hooks/cost_report.py --append
  By hand, for the current session (finds the newest transcript for this project):
    python3 .claude/hooks/cost_report.py
  For a given transcript:
    python3 .claude/hooks/cost_report.py --transcript ~/.claude/projects/<dir>/<session>.jsonl

Flags:
  --append   append one line to the cost log (cost.json "log") and write
             .claude/state/last-cost.txt for the next SessionStart.
  --json     print the summary as JSON instead of a table.

Each assistant message in the transcript carries a usage block. Streamed
messages appear more than once with the same message id, so the report keeps
one usage per id. Prices are per 1 million tokens. A model id matches a price
key exactly, else by substring. An empty price table gives tokens only.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sys
from pathlib import Path

HOOK_DIR = Path(__file__).resolve().parent
COST_FILE = HOOK_DIR / "cost.json"
FIELDS = ("input", "output", "cache_write", "cache_read")
USAGE_KEYS = {
    "input": ("input_tokens",),
    "output": ("output_tokens",),
    "cache_write": ("cache_creation_input_tokens",),
    "cache_read": ("cache_read_input_tokens",),
}


def load_prices() -> dict:
    try:
        with COST_FILE.open() as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError):
        return {"currency": "USD", "log": "docs/log/COST.md", "prices_per_million": {}}
    data.setdefault("currency", "USD")
    data.setdefault("log", "docs/log/COST.md")
    data["prices_per_million"] = {k: v for k, v in (data.get("prices_per_million") or {}).items() if not k.startswith("_")}
    return data


def project_dir(data: dict) -> Path:
    return Path(os.environ.get("CLAUDE_PROJECT_DIR") or data.get("cwd") or HOOK_DIR.parents[1]).resolve()


def project_transcript_dir(root: Path) -> Path:
    """Claude Code keeps transcripts in ~/.claude/projects/<path with / and . replaced by ->."""
    encoded = str(root).replace("/", "-").replace(".", "-").replace("_", "-")
    return Path.home() / ".claude" / "projects" / encoded


def newest_transcript(root: Path) -> Path | None:
    folder = project_transcript_dir(root)
    if not folder.is_dir():
        return None
    files = [p for p in folder.glob("*.jsonl") if p.is_file()]
    return max(files, key=lambda p: p.stat().st_mtime) if files else None


def read_usage(transcript: Path) -> dict:
    """Return {model: {field: tokens}} and the message count, one usage per message id."""
    seen: dict[str, tuple[str, dict]] = {}
    order = 0
    with transcript.open(errors="ignore") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            if entry.get("type") != "assistant":
                continue
            message = entry.get("message") or {}
            usage = message.get("usage")
            if not isinstance(usage, dict):
                continue
            model = message.get("model") or "unknown"
            key = message.get("id") or f"{entry.get('uuid', '')}-{order}"
            order += 1
            seen[key] = (model, usage)  # the last chunk of a streamed message has the full usage
    totals: dict[str, dict] = {}
    for model, usage in seen.values():
        bucket = totals.setdefault(model, {field: 0 for field in FIELDS})
        for field, keys in USAGE_KEYS.items():
            bucket[field] += sum(int(usage.get(k) or 0) for k in keys)
    return {"models": totals, "messages": len(seen)}


def price_for(model: str, prices: dict) -> dict | None:
    if model in prices:
        return prices[model]
    for key, value in prices.items():
        if key and key.lower() in model.lower():
            return value
    return None


def cost_of(tokens: dict, price: dict | None) -> float | None:
    if not price:
        return None
    total = 0.0
    for field in FIELDS:
        rate = price.get(field)
        if rate is None and field == "cache_write":
            rate = price.get("input")
        if rate is None and field == "cache_read":
            rate = price.get("input")
        total += tokens[field] * float(rate or 0) / 1_000_000
    return total


def summarize(transcript: Path, config: dict, role: str, session: str) -> dict:
    usage = read_usage(transcript)
    prices = config["prices_per_million"]
    rows, grand = [], {field: 0 for field in FIELDS}
    cost_total, priced = 0.0, True
    for model, tokens in sorted(usage["models"].items()):
        cost = cost_of(tokens, price_for(model, prices))
        if cost is None:
            priced = False
        else:
            cost_total += cost
        rows.append({"model": model, **tokens, "total": sum(tokens.values()), "cost": cost})
        for field in FIELDS:
            grand[field] += tokens[field]
    return {
        "date": dt.datetime.now().astimezone().strftime("%Y-%m-%d %H:%M %Z"),
        "session": session,
        "role": role or "none",
        "transcript": str(transcript),
        "messages": usage["messages"],
        "rows": rows,
        "total": {**grand, "total": sum(grand.values())},
        "cost": cost_total if (priced and rows) else None,
        "currency": config["currency"],
        "priced": priced and bool(prices),
    }


def fmt_cost(value: float | None, currency: str) -> str:
    return f"{value:.4f} {currency}" if value is not None else "n/a (set prices in team.json)"


def table(summary: dict) -> str:
    cur = summary["currency"]
    lines = [f"Session {summary['session']} ({summary['role']}), {summary['messages']} assistant messages, {summary['date']}", "",
             "| Model | Input | Output | Cache write | Cache read | Total | Cost |", "|---|---|---|---|---|---|---|"]
    for r in summary["rows"]:
        lines.append(f"| {r['model']} | {r['input']:,} | {r['output']:,} | {r['cache_write']:,} | {r['cache_read']:,} | {r['total']:,} | {fmt_cost(r['cost'], cur)} |")
    t = summary["total"]
    lines.append(f"| **All** | {t['input']:,} | {t['output']:,} | {t['cache_write']:,} | {t['cache_read']:,} | {t['total']:,} | {fmt_cost(summary['cost'], cur)} |")
    if not summary["priced"]:
        lines += ["", "Prices are not set. Add `cost.prices_per_million` to `team.json` and run the scaffold again, or edit `.claude/hooks/cost.json`."]
    return "\n".join(lines)


def log_lines(summary: dict) -> list[str]:
    cur = summary["currency"]
    date = summary["date"].split(" ")[0]
    out = []
    for r in summary["rows"]:
        cost = f"{r['cost']:.4f}" if r["cost"] is not None else "n/a"
        out.append(f"| {date} | {summary['session']} | {summary['role']} | {r['model']} | {r['input']} | {r['output']} | {r['cache_write']} | {r['cache_read']} | {r['total']} | {cost} |")
    if len(summary["rows"]) > 1:
        t = summary["total"]
        cost = f"{summary['cost']:.4f}" if summary["cost"] is not None else "n/a"
        out.append(f"| {date} | {summary['session']} | {summary['role']} | all | {t['input']} | {t['output']} | {t['cache_write']} | {t['cache_read']} | {t['total']} | {cost} |")
    return out


def append_log(summary: dict, root: Path, config: dict) -> Path:
    log = root / config["log"]
    log.parent.mkdir(parents=True, exist_ok=True)
    if not log.exists():
        log.write_text("# Cost log\n\n| Date | Session | Role | Model | Input | Output | Cache write | Cache read | Total | Cost |\n|---|---|---|---|---|---|---|---|---|---|\n")
    text = log.read_text()
    lines = log_lines(summary)
    with log.open("a") as f:
        f.write(("" if text.endswith("\n") else "\n") + "\n".join(lines) + "\n")
    state = root / ".claude" / "state"
    state.mkdir(parents=True, exist_ok=True)
    t = summary["total"]
    (state / "last-cost.txt").write_text(
        f"{t['total']:,} tokens ({t['output']:,} output), cost {fmt_cost(summary['cost'], summary['currency'])}. Log: {config['log']}\n"
    )
    return log


def current_role(data: dict, root: Path) -> str:
    if data.get("agent_type"):
        return str(data["agent_type"])
    state = root / ".claude" / "state" / "role"
    try:
        return state.read_text().strip()
    except OSError:
        return ""


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--transcript")
    ap.add_argument("--append", action="store_true")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)

    data = {}
    if not sys.stdin.isatty():
        try:
            raw = sys.stdin.read()
            data = json.loads(raw) if raw.strip() else {}
        except json.JSONDecodeError:
            data = {}
    root = project_dir(data)
    config = load_prices()
    transcript = Path(args.transcript) if args.transcript else (Path(data["transcript_path"]) if data.get("transcript_path") else newest_transcript(root))
    if not transcript or not transcript.is_file():
        print("cost_report: no transcript found. Give --transcript <path>, or run this as a SessionEnd hook.")
        return 0  # never block a session end
    session = data.get("session_id") or transcript.stem
    summary = summarize(transcript, config, current_role(data, root), session[:8])
    if args.append:
        append_log(summary, root, config)
    if args.json:
        print(json.dumps(summary, indent=2))
    else:
        print(table(summary))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
