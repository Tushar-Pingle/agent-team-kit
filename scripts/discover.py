#!/usr/bin/env python3
"""Scan a project folder and print what the agent team needs to know (agent-team-kit).

Usage:
  python3 discover.py --target <project dir> [--out stack.json] [--max-depth 3]

Prints a JSON object with the stack facts it can read from files: languages,
frameworks, package managers, commands, CI, data stores, infra, layout, and
the files it used as sources. The onboard-project skill reads this, confirms
it with the decider, and adds what a scan cannot know (users, constraints,
stage). Standard library only. Read-only.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

SKIP_DIRS = {".git", "node_modules", ".venv", "venv", "__pycache__", "dist", "build", ".next", ".nuxt", "target",
             ".terraform", ".idea", ".vscode", "coverage", ".cache", ".tox", ".mypy_cache", ".pytest_cache", "vendor"}
EXT_LANG = {
    ".py": "Python", ".ts": "TypeScript", ".tsx": "TypeScript", ".js": "JavaScript", ".jsx": "JavaScript", ".mjs": "JavaScript",
    ".go": "Go", ".rs": "Rust", ".java": "Java", ".kt": "Kotlin", ".swift": "Swift", ".rb": "Ruby", ".php": "PHP",
    ".cs": "C#", ".cpp": "C++", ".c": "C", ".scala": "Scala", ".sql": "SQL", ".sh": "Shell", ".tf": "HCL (Terraform)",
    ".vue": "Vue", ".svelte": "Svelte", ".dart": "Dart", ".ex": "Elixir", ".exs": "Elixir", ".r": "R", ".R": "R",
}
# (dependency name as it appears in a manifest, framework label)
DEP_FRAMEWORKS = [
    ("next", "Next.js"), ("react", "React"), ("vue", "Vue"), ("nuxt", "Nuxt"), ("svelte", "Svelte"), ("@sveltejs/kit", "SvelteKit"),
    ("@angular/core", "Angular"), ("express", "Express"), ("fastify", "Fastify"), ("nestjs", "NestJS"), ("@nestjs/core", "NestJS"),
    ("tailwindcss", "Tailwind"), ("vite", "Vite"), ("vitest", "Vitest"), ("jest", "Jest"), ("playwright", "Playwright"), ("@playwright/test", "Playwright"),
    ("cypress", "Cypress"), ("prisma", "Prisma"), ("drizzle-orm", "Drizzle"), ("typeorm", "TypeORM"), ("trpc", "tRPC"),
    ("fastapi", "FastAPI"), ("django", "Django"), ("flask", "Flask"), ("sqlalchemy", "SQLAlchemy"), ("alembic", "Alembic"),
    ("pydantic", "Pydantic"), ("pytest", "pytest"), ("streamlit", "Streamlit"), ("pandas", "pandas"), ("polars", "Polars"),
    ("dbt-core", "dbt"), ("dbt-snowflake", "dbt (Snowflake)"), ("dbt-bigquery", "dbt (BigQuery)"), ("dbt-postgres", "dbt (Postgres)"),
    ("snowflake-connector-python", "Snowflake"), ("snowflake-snowpark-python", "Snowpark"), ("airflow", "Airflow"), ("apache-airflow", "Airflow"),
    ("dagster", "Dagster"), ("prefect", "Prefect"), ("langchain", "LangChain"), ("langgraph", "LangGraph"), ("anthropic", "Anthropic SDK"),
    ("openai", "OpenAI SDK"), ("mcp", "MCP SDK"), ("@modelcontextprotocol/sdk", "MCP SDK"), ("ruff", "Ruff"), ("mypy", "mypy"),
    ("gin-gonic/gin", "Gin"), ("gorilla/mux", "Gorilla Mux"), ("actix-web", "Actix"), ("axum", "Axum"), ("tokio", "Tokio"),
    ("rails", "Rails"), ("spring-boot", "Spring Boot"),
]
DB_HINTS = [("postgres", "PostgreSQL"), ("mysql", "MySQL"), ("sqlite", "SQLite"), ("mongodb", "MongoDB"), ("redis", "Redis"),
            ("snowflake", "Snowflake"), ("bigquery", "BigQuery"), ("duckdb", "DuckDB"), ("supabase", "Supabase"), ("dynamodb", "DynamoDB")]


def walk(root: Path, max_depth: int):
    for path in root.rglob("*"):
        rel = path.relative_to(root)
        if any(part in SKIP_DIRS for part in rel.parts):
            continue
        if len(rel.parts) > max_depth and path.is_dir():
            continue
        yield path, rel


def read(path: Path, limit: int = 200_000) -> str:
    try:
        return path.read_text(errors="ignore")[:limit]
    except OSError:
        return ""


def package_json(path: Path, out: dict) -> None:
    try:
        data = json.loads(read(path))
    except json.JSONDecodeError:
        return
    deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}
    for name, label in DEP_FRAMEWORKS:
        if name in deps:
            out["frameworks"].add(label)
    scripts = data.get("scripts", {})
    pm = "npm"
    if (path.parent / "pnpm-lock.yaml").exists():
        pm = "pnpm"
    elif (path.parent / "yarn.lock").exists():
        pm = "yarn"
    elif (path.parent / "bun.lockb").exists() or (path.parent / "bun.lock").exists():
        pm = "bun"
    out["package_managers"].add(pm)
    run = f"{pm} run" if pm == "npm" else pm
    for key in ("build", "test", "lint", "typecheck", "dev"):
        if key in scripts and key not in out["commands"]:
            out["commands"]["run" if key == "dev" else key] = f"{run} {key}"
    out["commands"].setdefault("install", f"{pm} install")
    if data.get("workspaces"):
        out["notes"].append("npm/pnpm workspaces monorepo")


def pyproject(path: Path, out: dict) -> None:
    text = read(path)
    for name, label in DEP_FRAMEWORKS:
        if re.search(rf'["\']{re.escape(name)}[\[<>=~!;"\' ]', text):
            out["frameworks"].add(label)
    if (path.parent / "uv.lock").exists():
        out["package_managers"].add("uv")
        out["commands"].setdefault("install", "uv sync")
        out["commands"].setdefault("test", "uv run pytest")
    elif (path.parent / "poetry.lock").exists():
        out["package_managers"].add("poetry")
        out["commands"].setdefault("install", "poetry install")
        out["commands"].setdefault("test", "poetry run pytest")
    else:
        out["package_managers"].add("pip")
    if "[tool.ruff]" in text:
        out["commands"].setdefault("lint", "ruff check .")
    if "[tool.mypy]" in text:
        out["commands"].setdefault("typecheck", "mypy .")
    if "[tool.pytest" in text:
        out["commands"].setdefault("test", "pytest")


def requirements(path: Path, out: dict) -> None:
    text = read(path).lower()
    for name, label in DEP_FRAMEWORKS:
        if re.search(rf"^{re.escape(name.lower())}([\[=<>~!]|$)", text, re.M):
            out["frameworks"].add(label)
    out["package_managers"].add("pip")
    out["commands"].setdefault("install", f"pip install -r {path.name}")


def scan(root: Path, max_depth: int) -> dict:
    out: dict = {"languages": set(), "frameworks": set(), "package_managers": set(), "databases": set(), "infra": set(),
                 "commands": {}, "ci": "", "layout": [], "notes": [], "sources": []}
    ext_counts: Counter = Counter()
    top_dirs: list[str] = []
    for path, rel in walk(root, max_depth):
        if path.is_dir():
            if len(rel.parts) == 1:
                top_dirs.append(rel.as_posix())
            continue
        ext_counts[path.suffix] += 1
        name = path.name
        if name == "package.json":
            package_json(path, out); out["sources"].append(rel.as_posix())
        elif name == "pyproject.toml":
            pyproject(path, out); out["sources"].append(rel.as_posix())
        elif name in ("requirements.txt", "requirements-dev.txt"):
            requirements(path, out); out["sources"].append(rel.as_posix())
        elif name == "go.mod":
            out["languages"].add("Go"); out["commands"].setdefault("test", "go test ./..."); out["sources"].append(rel.as_posix())
            text = read(path)
            for dep, label in DEP_FRAMEWORKS:
                if "/" in dep and dep in text:
                    out["frameworks"].add(label)
        elif name == "Cargo.toml":
            out["languages"].add("Rust"); out["commands"].setdefault("test", "cargo test"); out["sources"].append(rel.as_posix())
            text = read(path)
            for dep, label in DEP_FRAMEWORKS:
                if re.search(rf"^{re.escape(dep)}\s*=", text, re.M):
                    out["frameworks"].add(label)
        elif name == "dbt_project.yml":
            out["frameworks"].add("dbt"); out["commands"].setdefault("test", "dbt build"); out["sources"].append(rel.as_posix())
        elif name in ("Gemfile",):
            out["languages"].add("Ruby"); out["sources"].append(rel.as_posix())
        elif name in ("pom.xml", "build.gradle", "build.gradle.kts"):
            out["languages"].add("Java/Kotlin"); out["sources"].append(rel.as_posix())
        elif name.startswith("Dockerfile") or name.startswith("docker-compose"):
            out["infra"].add("Docker"); out["sources"].append(rel.as_posix())
        elif path.suffix == ".tf":
            out["infra"].add("Terraform")
        elif name in ("serverless.yml", "serverless.yaml"):
            out["infra"].add("Serverless Framework")
        elif name in ("vercel.json",):
            out["infra"].add("Vercel")
        elif name in ("fly.toml",):
            out["infra"].add("Fly.io")
        elif name in ("Makefile",):
            out["sources"].append(rel.as_posix())
            text = read(path)
            for target in ("test", "lint", "build"):
                if re.search(rf"^{target}:", text, re.M):
                    out["commands"].setdefault(target, f"make {target}")
        if rel.parts[:2] == (".github", "workflows") and path.suffix in (".yml", ".yaml"):
            out["ci"] = "GitHub Actions"; out["sources"].append(rel.as_posix())
        elif name == ".gitlab-ci.yml":
            out["ci"] = "GitLab CI"; out["sources"].append(rel.as_posix())
        elif rel.parts[:1] == (".circleci",):
            out["ci"] = "CircleCI"
        if name in (".env.example", ".env.sample", "docker-compose.yml", "docker-compose.yaml") or name.endswith(".env.example"):
            text = read(path).lower()
            for hint, label in DB_HINTS:
                if hint in text:
                    out["databases"].add(label)
    for ext, count in ext_counts.most_common():
        if ext in EXT_LANG and count >= 2:
            out["languages"].add(EXT_LANG[ext])
    for fw in list(out["frameworks"]):
        for hint, label in DB_HINTS:
            if hint in fw.lower():
                out["databases"].add(label)
    for d in sorted(top_dirs):
        if d.startswith("."):
            continue
        files = sum(1 for p in (root / d).rglob("*") if p.is_file() and not any(s in p.parts for s in SKIP_DIRS))
        if files:
            out["layout"].append({"path": d, "files": files, "holds": "", "owner": ""})
    if (root / "CLAUDE.md").exists():
        out["notes"].append("CLAUDE.md exists: read it before you change the rules")
    if (root / "docs" / "plans").exists():
        out["notes"].append("docs/plans exists: the project may already have plans")
    for key in ("languages", "frameworks", "package_managers", "databases", "infra"):
        out[key] = sorted(out[key])
    out["sources"] = sorted(set(out["sources"]))
    out["file_count"] = sum(ext_counts.values())
    out["stage"] = "greenfield" if out["file_count"] < 5 else "existing codebase"
    return out


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--target", default=".")
    ap.add_argument("--out", help="write the JSON here instead of stdout")
    ap.add_argument("--max-depth", type=int, default=4)
    args = ap.parse_args(argv)
    root = Path(args.target).resolve()
    if not root.is_dir():
        sys.stderr.write(f"discover: '{root}' is not a folder.\n")
        return 1
    result = scan(root, args.max_depth)
    text = json.dumps(result, indent=2) + "\n"
    if args.out:
        Path(args.out).write_text(text)
        print(f"Wrote {args.out}: {result['stage']}, {result['file_count']} files, {len(result['languages'])} languages, {len(result['frameworks'])} frameworks.")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
