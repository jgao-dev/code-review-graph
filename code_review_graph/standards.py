"""Code review standards discovery and loading.

Supports:
- User-defined .code-review-standards.md in repo root
- Package defaults (standards/default-standards.md)
- XML-style section markers: <section name="phase-1">...</section>
- Smart section selection based on file patterns
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from .incremental import find_project_root


# Section name constants
SECTION_PHASE_0 = "phase-0"  # Structural Integrity & Anti-Bloat
SECTION_PHASE_0_5 = "phase-0.5"  # Anti-Defensive Bloat Rule
SECTION_PHASE_0_6 = "phase-0.6"  # Recipe Readability Rule
SECTION_PHASE_1 = "phase-1"  # Financial Integrity
SECTION_PHASE_2 = "phase-2"  # Time & Frontend Authority
SECTION_PHASE_3 = "phase-3"  # API Contracts & Transport
SECTION_PHASE_4 = "phase-4"  # Utility Purge
SECTION_SUMMARY = "summary"  # Pre-Submit Checklist

ALL_SECTIONS = [
    SECTION_PHASE_0,
    SECTION_PHASE_0_5,
    SECTION_PHASE_0_6,
    SECTION_PHASE_1,
    SECTION_PHASE_2,
    SECTION_PHASE_3,
    SECTION_PHASE_4,
    SECTION_SUMMARY,
]

# File pattern -> sections mapping for smart selection
# Keys are regex patterns, values are list of applicable sections
FILE_PATTERN_SECTIONS: dict[str, list[str]] = {
    # Financial/billing/payment files get phase-1
    r"(financial|money|payment|billing|invoice|transaction|price|cost|fee|balance)": [
        SECTION_PHASE_1,
    ],
    # Time/date/schedule files get phase-2
    r"(time|date|schedule|calendar|deadline|expiry|period)": [
        SECTION_PHASE_2,
    ],
    # API/route/handler files get phase-3
    r"(api|route|handler|controller|endpoint|resolver)": [
        SECTION_PHASE_3,
    ],
    # Utility/helper/lib files get phase-0 and phase-4
    r"(util|helper|lib|common|shared)": [
        SECTION_PHASE_0,
        SECTION_PHASE_4,
    ],
    # Constants/config files get phase-0
    r"(constant|config|env)": [
        SECTION_PHASE_0,
    ],
}

# Standards file locations
_USER_STANDARDS_FILE = ".code-review-standards.md"
_DEFAULT_STANDARDS_PATHS = [
    "standards/default-standards.md",
    "docs/DEFAULT-STANDARDS.md",
]


def find_standards_file(repo_root: Path | None = None) -> Path | None:
    """Find the standards file to use.

    Priority:
    1. User's .code-review-standards.md in repo root
    2. Package defaults (standards/default-standards.md)

    Args:
        repo_root: Repository root path. Auto-detected if omitted.

    Returns:
        Path to standards file, or None if not found.
    """
    # Try to get repo root
    if repo_root is None:
        try:
            repo_root = find_project_root()
        except RuntimeError:
            repo_root = None

    # Check for user's custom standards file
    if repo_root:
        user_file = repo_root / _USER_STANDARDS_FILE
        if user_file.exists():
            return user_file

    # Try package-relative paths for defaults
    pkg_dir = Path(__file__).resolve().parent.parent

    for rel_path in _DEFAULT_STANDARDS_PATHS:
        default_file = pkg_dir / rel_path
        if default_file.exists():
            return default_file

    return None


def parse_sections(content: str) -> dict[str, str]:
    """Parse XML-style section markers from markdown content.

    Args:
        content: Raw markdown content with <section name="..."> markers.

    Returns:
        Dict mapping section names to their content.
    """
    sections = {}
    pattern = re.compile(
        r'<section\s+name="([^"]+)">(.*?)</section>',
        re.DOTALL | re.IGNORECASE
    )

    for match in pattern.finditer(content):
        section_name = match.group(1)
        section_content = match.group(2).strip()
        sections[section_name] = section_content

    return sections


def get_applicable_sections(file_paths: list[str]) -> list[str]:
    """Determine which standards sections apply to given files.

    Uses file pattern matching to identify relevant sections.
    Always includes the summary section as it contains the checklist.

    Args:
        file_paths: List of file paths (relative or absolute).

    Returns:
        List of applicable section names, deduplicated.
    """
    applicable = {SECTION_SUMMARY}  # Always include summary

    for file_path in file_paths:
        file_lower = file_path.lower()

        for pattern, sections in FILE_PATTERN_SECTIONS.items():
            if re.search(pattern, file_lower):
                applicable.update(sections)

    return sorted(applicable, key=lambda s: ALL_SECTIONS.index(s) if s in ALL_SECTIONS else 999)


def get_review_standards(
    section_name: str | None = None,
    repo_root: str | None = None,
    list_sections: bool = False,
) -> dict[str, Any]:
    """Load code review standards from user file or package defaults.

    Auto-discovers from .code-review-standards.md or uses package defaults.
    Loads only the requested section for token efficiency.

    Args:
        section_name: Section to load (e.g., "phase-0", "phase-1").
                      If None, returns metadata and available sections.
        repo_root: Repository root path. Auto-detected if omitted.
        list_sections: If True, only list available sections without content.

    Returns:
        Dict with status, section name, content (if requested), and available sections.
    """
    root = Path(repo_root) if repo_root else None

    # Find standards file
    standards_file = find_standards_file(root)

    if not standards_file:
        return {
            "status": "not_found",
            "error": (
                "No standards file found. "
                f"Create {_USER_STANDARDS_FILE} in your repo root, "
                "or ensure package defaults are installed."
            ),
            "available_sections": [],
        }

    # Read and parse
    try:
        content = standards_file.read_text(encoding="utf-8")
        sections = parse_sections(content)
    except Exception as e:
        return {
            "status": "error",
            "error": f"Failed to parse standards file: {e}",
            "available_sections": [],
        }

    # Determine source type
    is_user_file = standards_file.name == _USER_STANDARDS_FILE

    # List sections only
    if list_sections:
        return {
            "status": "ok",
            "source": "user" if is_user_file else "default",
            "file": str(standards_file),
            "available_sections": list(sections.keys()),
        }

    # Return metadata if no section requested
    if section_name is None:
        return {
            "status": "ok",
            "source": "user" if is_user_file else "default",
            "file": str(standards_file),
            "available_sections": list(sections.keys()),
            "usage_hint": (
                f"Call get_review_standards_tool(section_name='<section>') "
                f"to load a specific section. Available: {', '.join(sections.keys())}"
            ),
        }

    # Load specific section
    if section_name not in sections:
        return {
            "status": "not_found",
            "error": (
                f"Section '{section_name}' not found. "
                f"Available: {', '.join(sections.keys())}"
            ),
            "available_sections": list(sections.keys()),
        }

    return {
        "status": "ok",
        "source": "user" if is_user_file else "default",
        "section": section_name,
        "content": sections[section_name],
        "available_sections": list(sections.keys()),
    }


def get_standards_for_files(
    file_paths: list[str],
    repo_root: str | None = None,
) -> dict[str, Any]:
    """Load applicable standards sections for a set of files.

    Smart selection based on file patterns. Always includes summary.

    Args:
        file_paths: List of file paths to analyze.
        repo_root: Repository root path. Auto-detected if omitted.

    Returns:
        Dict with applicable sections and their content.
    """
    applicable = get_applicable_sections(file_paths)

    result: dict[str, Any] = {
        "status": "ok",
        "files_analyzed": file_paths,
        "applicable_sections": applicable,
        "standards": {},
    }

    for section in applicable:
        std_result = get_review_standards(section_name=section, repo_root=repo_root)
        if std_result["status"] == "ok":
            result["standards"][section] = std_result["content"]

    return result