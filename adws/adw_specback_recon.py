#!/usr/bin/env python3
"""ADW — Phase 1: Reconnaissance & Template selection.

Scans a codebase to identify languages, frameworks, and structure, then
selects a spec template. This is the entry point for code-first spec
generation — it answers "what are we looking at?".

Usage:
    uv run adws/adw_specback_recon.py --target /path/to/codebase
    uv run adws/adw_specback_recon.py --target /path --non-interactive
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_ROOT))

from adws.adw_modules import session  # noqa: E402
from adws.adw_modules.utils import (  # noqa: E402
    add_common_args,
    resolve_specback_dir,
)
from scripts.data_types import ReconOutput  # noqa: E402


# ── Language / Framework detection patterns ──────────────────────────────

_LANG_DETECT: dict[str, list[str]] = {
    ".py": ["python"],
    ".js": ["javascript"],
    ".jsx": ["javascript"],
    ".ts": ["typescript"],
    ".tsx": ["typescript"],
    ".java": ["java"],
    ".kt": ["kotlin"],
    ".kts": ["kotlin"],
    ".go": ["go"],
    ".rs": ["rust"],
    ".rb": ["ruby"],
    ".php": ["php"],
    ".swift": ["swift"],
    ".c": ["c"],
    ".h": ["c"],
    ".cpp": ["cpp"],
    ".cxx": ["cpp"],
    ".hpp": ["cpp"],
    ".cs": ["csharp"],
    ".dart": ["dart"],
    ".sql": ["sql"],
    ".sh": ["shell"],
    ".bash": ["shell"],
    ".zsh": ["shell"],
    ".R": ["r"],
    ".r": ["r"],
    ".scala": ["scala"],
    ".ex": ["elixir"],
    ".exs": ["elixir"],
    ".erl": ["erlang"],
    ".hrl": ["erlang"],
    ".clj": ["clojure"],
    ".cljs": ["clojure"],
    ".cljc": ["clojure"],
    ".lua": ["lua"],
    ".hs": ["haskell"],
    ".ml": ["ocaml"],
    ".mli": ["ocaml"],
    ".zig": ["zig"],
    ".nim": ["nim"],
    ".vue": ["vue"],
    ".svelte": ["svelte"],
    ".astro": ["astro"],
    ".pl": ["perl"],
    ".pm": ["perl"],
    ".t": ["perl"],
    ".ps1": ["powershell"],
    ".tf": ["terraform"],
    ".yaml": ["yaml"],
    ".yml": ["yaml"],
    ".json": ["json"],
    ".toml": ["toml"],
    ".md": ["markdown"],
    ".rst": ["restructuredtext"],
    ".tex": ["latex"],
}

_FRAMEWORK_PATTERNS: dict[str, list[dict[str, Any]]] = {
    "python": [
        {"name": "Django", "re": r"^import django|^from django|django"},
        {"name": "Flask", "re": r"^import flask|^from flask|flask"},
        {"name": "FastAPI", "re": r"^import fastapi|^from fastapi|fastapi"},
        {"name": "PyTorch", "re": r"^import torch|^from torch|torch"},
        {"name": "TensorFlow", "re": r"^import tensorflow|^from tensorflow|tensorflow"},
        {"name": "SQLAlchemy", "re": r"^import sqlalchemy|^from sqlalchemy|sqlalchemy"},
        {"name": "Celery", "re": r"^import celery|^from celery|celery"},
        {"name": "Pydantic", "re": r"^import pydantic|^from pydantic|pydantic"},
    ],
    "javascript": [
        {"name": "React", "re": r"from ['\"]react['\"]|require\(['\"]react['\"]\)"},
        {"name": "Vue", "re": r"from ['\"]vue['\"]|require\(['\"]vue['\"]\)|import.*from ['\"]vue['\"]"},
        {"name": "Express", "re": r"require\(['\"]express['\"]\)|from ['\"]express['\"]"},
        {"name": "Next.js", "re": r"next|^import.*next/|next/link|next/router"},
        {"name": "Nuxt", "re": r"nuxt|^import.*nuxt/"},
        {"name": "SvelteKit", "re": r"sveltekit|^import.*@sveltejs/"},
    ],
    "typescript": [
        {"name": "Angular", "re": r"@angular|from ['\"]@angular/|angular"},
        {"name": "NestJS", "re": r"@nestjs|from ['\"]@nestjs/|nestjs"},
        {"name": "TypeORM", "re": r"typeorm|from ['\"]typeorm['\"]"},
        {"name": "Prisma", "re": r"prisma|@prisma/client"},
    ],
    "java": [
        {"name": "Spring Boot", "re": r"org\.springframework\.boot|spring-boot-starter"},
        {"name": "Spring MVC", "re": r"org\.springframework\.web|@Controller|@RestController"},
        {"name": "Hibernate", "re": r"org\.hibernate|javax\.persistence|jakarta\.persistence"},
        {"name": "JUnit", "re": r"org\.junit|junit"},
        {"name": "Micronaut", "re": r"io\.micronaut"},
        {"name": "Quarkus", "re": r"io\.quarkus"},
    ],
    "go": [
        {"name": "Gin", "re": r"gin-gonic|github\.com/gin-gonic/gin"},
        {"name": "Echo", "re": r"github\.com/labstack/echo"},
        {"name": "Fiber", "re": r"github\.com/gofiber/fiber"},
        {"name": "GORM", "re": r"gorm\.io|gorm\.io/gorm"},
        {"name": "Chi", "re": r"github\.com/go-chi/chi"},
    ],
    "ruby": [
        {"name": "Ruby on Rails", "re": r"rails|Rails\.application|ActiveRecord::|ActionController::"},
        {"name": "Sinatra", "re": r"sinatra|require ['\"]sinatra['\"]"},
        {"name": "RSpec", "re": r"rspec|RSpec\.describe"},
    ],
    "rust": [
        {"name": "Actix", "re": r"actix-web|actix_web"},
        {"name": "Rocket", "re": r"rocket::|rocket_ms?"},
        {"name": "Axum", "re": r"axum::|axum-"},
        {"name": "Tokio", "re": r"tokio::|tokio-"},
        {"name": "Serde", "re": r"serde::|serde-"},
    ],
    "php": [
        {"name": "Laravel", "re": r"Laravel|Illuminate\\|Illuminate/"},
        {"name": "Symfony", "re": r"Symfony\\|Symfony/"},
        {"name": "CakePHP", "re": r"Cake\\|CakePHP"},
        {"name": "CodeIgniter", "re": r"CodeIgniter|CI_"},
    ],
}

# ── Framework file markers (quick check without reading) ────────────────

_FRAMEWORK_FILE_MARKERS: dict[str, list[dict[str, Any]]] = {
    "React": [{"files": ["package.json"], "re": r'"react"'}, {"files": ["package.json"], "re": r'"next"'}],
    "Vue": [{"files": ["package.json"], "re": r'"vue"'}],
    "Angular": [{"files": ["angular.json", ".angular-cli.json"]}],
    "Django": [{"files": ["manage.py", "django/__init__.py"], "dirs": ["django"]}],
    "Flask": [{"files": ["app.py"], "dirs": ["flask"]}],
    "Laravel": [{"files": ["artisan"]}],
    "Rails": [{"files": ["Gemfile", "config/application.rb"]}],
    "Spring Boot": [{"files": ["pom.xml"], "re": r"spring-boot"}, {"files": ["build.gradle"], "re": r"spring-boot"}],
    "Gin": [{"files": ["go.mod"], "re": r"gin"}],
    "Prisma": [{"files": ["prisma/schema.prisma"]}],
}

# ── Exclusion: directories/files to skip ─────────────────────────────────

_SKIP_DIRS: set[str] = {
    ".git", ".svn", ".hg", "__pycache__", "node_modules", ".venv",
    "venv", "env", ".tox", ".eggs", "eggs", ".mypy_cache",
    ".pytest_cache", ".ruff_cache", ".hypothesis", ".nox",
    ".direnv", ".bundle", "vendor/bundle", ".gradle", "build",
    "dist", ".next", ".nuxt", ".output", "target",
    ".specback", "specs", ".hermes",
}

_SKIP_FILES: set[str] = {
    "package-lock.json", "yarn.lock", "pnpm-lock.yaml",
    ".DS_Store", "Thumbs.db",
}

_COMPLEXITY_WEIGHTS: dict[str, int] = {
    # More languages → more complex
    "per_language": 2,
    # Frameworks add complexity
    "per_framework": 1,
    # File counts
    "files_per_100": 1,  # per 100 files
    # Config files suggest infrastructure
    "config_dir_boost": 2,
}


# ══════════════════════════════════════════════════════════════════════════
# Public API
# ══════════════════════════════════════════════════════════════════════════


def scan_languages(target: Path) -> dict[str, Any]:
    """Scan a codebase directory to identify languages and frameworks.

    Walks the target directory, counts files by extension, picks up
    common framework markers, and returns a structured summary.

    Args:
        target: Path to the target codebase directory.

    Returns:
        A dict with:
            - languages: dict[str, int] — extension → file count
            - language_names: list[str] — unique language names (pretty)
            - frameworks: list[str] — detected framework names
            - total_files: int
            - has_config_dir: bool
            - top_level_dirs: list[str]
    """
    target = Path(target).resolve()
    if not target.is_dir():
        return {
            "languages": {},
            "language_names": [],
            "frameworks": [],
            "total_files": 0,
            "has_config_dir": False,
            "top_level_dirs": [],
        }

    ext_counter: Counter = Counter()
    total_files = 0
    has_config = False
    top_level_dirs: list[str] = []
    found_frameworks: set[str] = set()

    # First pass: count files and collect shell info
    for root, dirs, files in os.walk(str(target)):
        rel = Path(root).relative_to(target)
        # Prune skip dirs in-place
        dirs[:] = [d for d in dirs if d not in _SKIP_DIRS]

        # Track top-level dirs
        if rel == Path("."):
            top_level_dirs = sorted(dirs)
            # Check for config dirs
            if "config" in dirs or "conf" in dirs:
                has_config = True

        for f in files:
            if f in _SKIP_FILES:
                continue
            total_files += 1
            ext = Path(f).suffix.lower()
            if ext in _LANG_DETECT:
                for lang in _LANG_DETECT[ext]:
                    ext_counter[lang] += 1

            # Check file-name-based framework markers
            for fw_name, markers in _FRAMEWORK_FILE_MARKERS.items():
                for marker in markers:
                    marker_files = marker.get("files", [])
                    for mf in marker_files:
                        if Path(f).match(mf):
                            if marker.get("re"):
                                # Quick file-name only — full content check
                                pass
                            else:
                                found_frameworks.add(fw_name)

    # Second pass: sample key files for framework content patterns
    _detect_frameworks_from_content(target, found_frameworks)

    # Pretty language names
    lang_names: list[str] = []
    for lang_key in sorted(ext_counter.keys(), key=lambda k: ext_counter[k], reverse=True):
        pretty = _pretty_lang(lang_key)
        if pretty not in lang_names:
            lang_names.append(pretty)

    return {
        "languages": dict(ext_counter.most_common()),
        "language_names": lang_names,
        "frameworks": sorted(found_frameworks),
        "total_files": total_files,
        "has_config_dir": has_config,
        "top_level_dirs": top_level_dirs,
    }


def _detect_frameworks_from_content(target: Path, found: set[str]) -> None:
    """Sample key package manifests to detect frameworks by content patterns."""
    manifest_paths = [
        target / "package.json",
        target / "setup.py",
        target / "pyproject.toml",
        target / "Cargo.toml",
        target / "go.mod",
        target / "Gemfile",
        target / "composer.json",
        target / "pom.xml",
        target / "build.gradle",
        target / "Mix.exs",
        target / "Package.swift",
    ]

    for mp in manifest_paths:
        if not mp.is_file():
            continue
        try:
            text = mp.read_text(encoding="utf-8", errors="replace")
            for fw_name, markers in _FRAMEWORK_FILE_MARKERS.items():
                for marker in markers:
                    marker_files = marker.get("files", [])
                    for mf in marker_files:
                        if mp.name == mf or mp.match(mf):
                            if marker.get("re"):
                                if re.search(marker["re"], text, re.IGNORECASE):
                                    found.add(fw_name)
            # Also check content for import/require patterns
            ext = mp.suffix.lower()
            langs_for_manifest = _LANG_DETECT.get(ext, [])
            for lang in langs_for_manifest:
                patterns = _FRAMEWORK_PATTERNS.get(lang, [])
                for p in patterns:
                    if re.search(p["re"], text, re.IGNORECASE):
                        found.add(p["name"])
        except (OSError, PermissionError):
            continue


def estimate_complexity(
    target: Path,
    languages: dict[str, int],
    frameworks: list[str],
) -> Literal["low", "medium", "high"]:
    """Estimate codebase complexity level based on scan results.

    Args:
        target: Path to the target codebase directory.
        languages: Mapping of language key → file count.
        frameworks: List of detected framework names.

    Returns:
        "low", "medium", or "high".
    """
    score = 0
    total_files = sum(languages.values())

    # Language diversity
    lang_count = len(languages)
    score += lang_count * _COMPLEXITY_WEIGHTS["per_language"]

    # Framework count
    score += len(frameworks) * _COMPLEXITY_WEIGHTS["per_framework"]

    # File volume
    score += (total_files // 100) * _COMPLEXITY_WEIGHTS["files_per_100"]

    # Check for infra/config directories
    try:
        conf_dir = target / "config"
        if conf_dir.is_dir():
            sub_items = list(conf_dir.iterdir())
            if len(sub_items) > 5:
                score += _COMPLEXITY_WEIGHTS["config_dir_boost"]
    except (OSError, PermissionError):
        pass

    if score <= 3:
        return "low"
    elif score <= 8:
        return "medium"
    else:
        return "high"


def recommend_template(
    languages: dict[str, int],
    frameworks: list[str],
    complexity: str,
    templates_dir: Path,
) -> str:
    """Recommend the best spec template for the detected codebase.

    Heuristic ranking based on:
    1. Framework-specific templates (web-app, api-service, cli-tool, etc.)
    2. Language-based fallback
    3. Generic default

    Args:
        languages: Mapping of language key → file count.
        frameworks: List of detected framework names.
        complexity: "low", "medium", or "high".
        templates_dir: Path to the templates directory.

    Returns:
        Template name (stem of the file, e.g. "web-app").
    """
    # Available template names
    available: list[str] = sorted([
        p.stem for p in templates_dir.glob("*.md")
        if p.is_file() and not p.stem.startswith("_")
    ]) if templates_dir.is_dir() else []

    if not available:
        return "api-service"  # fallback

    # Scoring: template → score
    scores: dict[str, int] = {t: 0 for t in available}

    lang_names = {_pretty_lang(k).lower() for k in languages}
    fw_lower = {f.lower() for f in frameworks}

    # web-app: web frameworks or web-related dirs
    web_fws = {"react", "vue", "angular", "django", "flask", "rails",
               "laravel", "next.js", "nuxt", "sveltekit", "symfony",
               "cakephp", "express", "spring mvc", "spring boot"}
    if fw_lower & web_fws:
        scores["web-app"] = scores.get("web-app", 0) + 10
    if {"javascript", "typescript", "php", "ruby", "python"} & lang_names:
        scores["web-app"] = scores.get("web-app", 0) + 3

    # api-service: API frameworks
    api_fws = {"fastapi", "express", "gin", "echo", "fiber", "actix",
               "rocket", "axum", "nestjs", "spring boot", "micronaut",
               "quarkus", "sinatra"}
    if fw_lower & api_fws:
        scores["api-service"] = scores.get("api-service", 0) + 10
    if {"go", "rust"} & lang_names:
        scores["api-service"] = scores.get("api-service", 0) + 5

    # cli-tool: shell scripts or CLI frameworks
    cli_fws = {"click", "typer", "clap", "cobra", "commander.js", "yargs",
               "argparse", "docopt"}
    if fw_lower & cli_fws:
        scores["cli-tool"] = scores.get("cli-tool", 0) + 10
    if {"shell"} & lang_names:
        scores["cli-tool"] = scores.get("cli-tool", 0) + 8
    if "shell" in langs_flat(languages):
        scores["cli-tool"] = scores.get("cli-tool", 0) + 3

    # library-sdk: libraries, SDKs
    lib_fws = {"pydantic", "sqlalchemy", "serde", "typeorm", "prisma"}
    if fw_lower & lib_fws:
        scores["library-sdk"] = scores.get("library-sdk", 0) + 5

    # desktop-app: desktop frameworks
    desktop_fws = {"electron", "tauri", "qt", "gtk", "wpf", "winforms",
                   "swiftui", "javafx"}
    if fw_lower & desktop_fws or {"dart", "swift", "csharp"} & lang_names:
        scores["desktop-app"] = scores.get("desktop-app", 0) + 8

    # mobile-app: mobile frameworks
    mobile_fws = {"flutter", "react native", "swiftui", "jetpack compose",
                  "xamarin", "ionic", "cordova"}
    if fw_lower & mobile_fws:
        scores["mobile-app"] = scores.get("mobile-app", 0) + 12
    if {"kotlin", "swift", "dart"} & lang_names:
        scores["mobile-app"] = scores.get("mobile-app", 0) + 3

    # infrastructure: Terraform, Docker, k8s
    infra_fws = {"terraform", "pulumi", "ansible", "chef", "puppet"}
    if fw_lower & infra_fws or "terraform" in lang_names:
        scores["infrastructure"] = scores.get("infrastructure", 0) + 10

    # event-driven: message queue patterns
    event_fws = {"celery", "kafka", "rabbitmq", "nats", "pulsar", "dramatiq"}
    if fw_lower & event_fws:
        scores["event-driven"] = scores.get("event-driven", 0) + 8

    # batch-system: batch jobs
    batch_fws = {"spring batch", "celery", "dramatiq", "huey"}
    if fw_lower & batch_fws:
        scores["batch-system"] = scores.get("batch-system", 0) + 6

    # Pick best-scored template that actually exists
    best = max(
        ((t, s) for t, s in scores.items() if t in available),
        key=lambda x: x[1],
        default=(None, 0),
    )

    if best[0] and best[1] > 0:
        return best[0]

    # Fallback: by dominant language
    dominant = dominant_language(languages)
    lang_to_template: dict[str, str] = {
        "python": "cli-tool",
        "javascript": "web-app", "typescript": "web-app",
        "go": "api-service", "rust": "cli-tool",
        "ruby": "web-app", "php": "web-app",
        "java": "api-service", "kotlin": "mobile-app",
        "swift": "mobile-app", "dart": "mobile-app",
        "shell": "cli-tool", "terraform": "infrastructure",
    }
    fallback = lang_to_template.get(dominant, "api-service")
    if fallback in available:
        return fallback

    # Ultimate fallback
    return available[0] if available else "api-service"


def dominant_language(languages: dict[str, int]) -> str:
    """Return the language key with the highest file count."""
    if not languages:
        return "unknown"
    return max(languages, key=languages.get)


def langs_flat(languages: dict[str, int]) -> set[str]:
    """Return set of all detected language names (pretty-lowered)."""
    return {_pretty_lang(k).lower() for k in languages}


def total_file_count(languages: dict[str, int]) -> int:
    """Return total file count from language dict."""
    return sum(languages.values())


def _pretty_lang(lang: str) -> str:
    """Pretty-print a language name."""
    mapping = {
        "python": "Python", "javascript": "JavaScript", "typescript": "TypeScript",
        "java": "Java", "go": "Go", "rust": "Rust", "ruby": "Ruby",
        "php": "PHP", "csharp": "C#", "swift": "Swift", "kotlin": "Kotlin",
        "cpp": "C++", "c": "C", "dart": "Dart", "sql": "SQL", "shell": "Shell",
        "terraform": "Terraform", "yaml": "YAML", "json": "JSON",
        "toml": "TOML", "markdown": "Markdown", "vue": "Vue",
        "svelte": "Svelte", "astro": "Astro",
    }
    return mapping.get(lang, lang.capitalize())


# ── CLI ──────────────────────────────────────────────────────────────────


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI argument parser."""
    parser = argparse.ArgumentParser(
        description="specback ADW — Phase 1: Reconnaissance & Template"
    )
    add_common_args(parser)
    parser.add_argument(
        "--non-interactive",
        action="store_true",
        help="Use defaults instead of prompting",
    )
    parser.add_argument(
        "--goal",
        type=str, default=None,
        help="Path to an existing goal.json (optional)",
    )
    parser.add_argument(
        "--envelope-out",
        type=str, default=None,
        help="Path to write the ReconOutput envelope JSON",
    )
    return parser


def run_recon(
    target: Path,
    output_dir: Path,
    goal: str | None = None,
    non_interactive: bool = False,
) -> ReconOutput:
    """Execute Phase 1 reconnaissance and return a ReconOutput envelope.

    Args:
        target: Target codebase directory.
        output_dir: Output directory for artifacts.
        goal: Optional path to goal.json.
        non_interactive: Skip interactive prompts.

    Returns:
        ReconOutput envelope.
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n  🔍 Scanning target: {target}")

    # Scan languages and frameworks
    scan_result = scan_languages(target)
    languages = scan_result["languages"]
    language_names = scan_result["language_names"]
    frameworks = scan_result["frameworks"]
    total_files = scan_result["total_files"]

    print(f"     Languages: {', '.join(language_names) if language_names else '(none detected)'}")
    print(f"     Frameworks: {', '.join(frameworks) if frameworks else '(none detected)'}")
    print(f"     Total source files: {total_files}")

    # Estimate complexity
    complexity = estimate_complexity(target, languages, frameworks)
    print(f"     Estimated complexity: {complexity}")

    # Determine templates directory
    templates_dir = _PROJECT_ROOT / "templates"

    # Recommend template
    template = recommend_template(languages, frameworks, complexity, templates_dir)
    print(f"     Recommended template: {template}\n")

    # Select depth mode based on complexity
    if non_interactive:
        depth_mode: Literal["comprehensive", "outline", "interactive"] = (
            "comprehensive" if complexity == "high" else "outline"
        )
    else:
        # Prompt user (or accept default)
        depth_options = ["outline", "comprehensive", "interactive"]
        print(f"  Select investigation depth (default: {'comprehensive' if complexity == 'high' else 'outline'}):")
        for i, opt in enumerate(depth_options, 1):
            print(f"    {i}. {opt}")
        try:
            raw = input(f"  Enter choice (1-3): ").strip()
            if raw:
                idx = int(raw) - 1
                if 0 <= idx < len(depth_options):
                    depth_mode = depth_options[idx]  # type: ignore[assignment]
                else:
                    depth_mode = "comprehensive" if complexity == "high" else "outline"
            else:
                depth_mode = "comprehensive" if complexity == "high" else "outline"
        except (EOFError, ValueError):
            depth_mode = "comprehensive" if complexity == "high" else "outline"

    print(f"     Depth mode: {depth_mode}")

    # Write recon report
    report_path = output_dir / "recon.json"
    report_data = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "target": str(target),
        "languages": languages,
        "language_names": language_names,
        "frameworks": frameworks,
        "total_files": total_files,
        "estimated_complexity": complexity,
        "recommended_template": template,
        "depth_mode": depth_mode,
        "has_config_dir": scan_result.get("has_config_dir", False),
        "top_level_dirs": scan_result.get("top_level_dirs", []),
    }
    report_path.write_text(
        json.dumps(report_data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"     Report written: {report_path}")

    # Multi-scope detection
    multi_scope_detected = len(scan_result.get("top_level_dirs", [])) > 8
    scopes: list[dict[str, str]] = []
    if multi_scope_detected:
        scopes = [{"name": d, "path": str(target / d)} for d in scan_result.get("top_level_dirs", [])[:5]]

    return ReconOutput(
        frameworks=frameworks,
        total_files=total_files,
        template_selected=template,
        depth_mode=depth_mode,
        tree_sitter_available=False,
        recon_report_path=str(report_path),
        customized_chapters=None,
        summary=f"Recon complete: {', '.join(language_names) if language_names else 'no languages'}, "
                f"{len(frameworks)} framework(s), complexity={complexity}, template={template}",
        artifacts=[str(report_path)],
    )


def main() -> int:
    """CLI entry point for Phase 1: Reconnaissance."""
    parser = build_parser()
    args = parser.parse_args()

    target = Path(args.target).resolve()
    if not target.is_dir():
        print(f"Error: target directory not found: {target}", file=sys.stderr)
        return 1

    output_dir = Path(".").resolve()

    run = session.ensure(adw_id=args.adw_id)

    with run.phase(session.PhaseParams(
        name="recon", kind="code", owner="code",
        description="Codebase reconnaissance and template selection",
    )) as ph:
        envelope = run_recon(
            target=target,
            output_dir=output_dir,
            goal=args.goal,
            non_interactive=args.non_interactive,
        )
        ph.log(envelope=envelope.to_dict())

        if args.envelope_out:
            out_path = Path(args.envelope_out)
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(
                json.dumps(envelope.to_dict(), ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

        print(f"\n  ✅ Recon complete: {envelope.template_selected}")
        return run.finish(accepted=True)


if __name__ == "__main__":
    sys.exit(main())
