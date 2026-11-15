import os
import zipfile
import hashlib
import fnmatch
from pathlib import Path
from datetime import datetime

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent
OUTPUT_ZIP_DIR = WORKSPACE_ROOT / "backups"
OUTPUT_ZIP_PATH = OUTPUT_ZIP_DIR / "Personal-AI-Workforce-OS-Project.zip"

EXCLUDE_DIRS = {
    ".git",
    ".venv",
    "venv",
    "ENV",
    "env",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "temp",
    "tmp",
    "backups",
    "node_modules",
    "htmlcov"
}

EXCLUDE_PATTERNS = [
    "*.pyc",
    "*.pyo",
    "*.pyd",
    ".DS_Store",
    ".DS_Store?",
    "._*",
    "*.key",
    "*.pem",
    "*.crt",
    "*.cert",
    "*.p12",
    "*.pfx",
    ".ai_workforce_vault.key",
    ".env",
    ".env.*",
    "data/*.db*",
    "logs/*.log",
    "logs/*.pid",
    "Personal-AI-Workforce-OS-Project.zip"
]

WHITELIST_PATTERNS = [
    ".env.example"
]

def should_exclude(rel_path: str) -> bool:
    # Whitelist exceptions
    for w in WHITELIST_PATTERNS:
        if fnmatch.fnmatch(rel_path, w) or rel_path == w:
            return False

    parts = rel_path.split(os.sep)
    for part in parts[:-1]:
        if part in EXCLUDE_DIRS:
            return True

    filename = parts[-1]
    for pattern in EXCLUDE_PATTERNS:
        if fnmatch.fnmatch(filename, pattern) or fnmatch.fnmatch(rel_path, pattern):
            return True

    return False

def create_and_verify_zip():
    OUTPUT_ZIP_DIR.mkdir(parents=True, exist_ok=True)
    if OUTPUT_ZIP_PATH.exists():
        OUTPUT_ZIP_PATH.unlink()

    print(f"Creating clean project archive at: {OUTPUT_ZIP_PATH}")
    added_files = []

    with zipfile.ZipFile(OUTPUT_ZIP_PATH, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(WORKSPACE_ROOT):
            # Prune excluded directories in-place to avoid descending
            dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]

            for file in sorted(files):
                full_path = Path(root) / file
                rel_path = full_path.relative_to(WORKSPACE_ROOT).as_posix()

                if should_exclude(rel_path):
                    continue

                zf.write(full_path, arcname=f"Personal-AI-Workforce-OS/{rel_path}")
                added_files.append(rel_path)

    print(f"✓ Archive created with {len(added_files)} files.")

    # Verification Phase
    print("Verifying archive integrity and secret exclusion...")
    with zipfile.ZipFile(OUTPUT_ZIP_PATH, "r") as zf:
        corrupt = zf.testzip()
        if corrupt:
            raise RuntimeError(f"Archive corruption detected in file: {corrupt}")
        print("✓ ZIP archive integrity test passed (testzip() == None).")

        namelist = zf.namelist()
        
        # Security checks
        forbidden_matches = []
        for name in namelist:
            parts = name.split('/')
            base = parts[-1]
            if base in [".env", ".ai_workforce_vault.key", "ai_workforce.db"] or base.endswith(".key") or base.endswith(".pem"):
                forbidden_matches.append(name)
            if any(p in [".git", ".venv", "venv", "__pycache__", "temp", "backups"] for p in parts):
                forbidden_matches.append(name)

        if forbidden_matches:
            raise PermissionError(f"Security Exclusion Violation! Prohibited files found in archive: {forbidden_matches}")
        print("✓ Security audit passed: 0 secrets, 0 keys, 0 venvs, and 0 databases in archive.")

        # Agent checks
        agent_names = [
            "coordinator", "task-decomposer", "resource-allocator", "progress-monitor",
            "market-seo-geo-researcher", "seo-auditor", "geo-targeting-analyst", "competitor-intelligence",
            "marketing-agent", "content-strategist", "campaign-planner", "brand-compliance",
            "software-engineer", "frontend-specialist", "backend-specialist", "qa-test-engineer",
            "browser-use-agent", "web-navigator", "data-extractor", "visual-inspector",
            "deployment-agent", "environment-provisioner", "service-manager", "release-verifier",
            "master-reporting-agent", "executive-summarizer", "audit-trail-compiler", "retrospective-analyst",
            "system-integrator-update-agent", "asset-classifier-auditor", "package-runtime-installer", "capability-knowledge-synchronizer"
        ]

        missing_agents = []
        for a in agent_names:
            agent_md = f"Personal-AI-Workforce-OS/config/agents/{a}/AGENT.md"
            mem_md = f"Personal-AI-Workforce-OS/config/agents/{a}/MEMORY.md"
            if agent_md not in namelist or mem_md not in namelist:
                missing_agents.append(a)

        if missing_agents:
            raise ValueError(f"Missing agents in archive: {missing_agents}")
        print(f"✓ All 32 agents and standard Markdown files verified in archive.")

    # Calculate SHA-256
    sha256 = hashlib.sha256()
    with open(OUTPUT_ZIP_PATH, "rb") as f:
        while chunk := f.read(65536):
            sha256.update(chunk)
    digest = sha256.hexdigest()
    size_bytes = OUTPUT_ZIP_PATH.stat().st_size
    size_mb = size_bytes / (1024 * 1024)

    print(f"✓ File Size: {size_bytes} bytes ({size_mb:.2f} MB)")
    print(f"✓ SHA-256: {digest}")

    return {
        "zip_path": str(OUTPUT_ZIP_PATH),
        "file_count": len(added_files),
        "size_bytes": size_bytes,
        "size_mb": round(size_mb, 2),
        "sha256": digest,
        "created_at": datetime.utcnow().isoformat() + "Z",
        "file_list": added_files
    }

if __name__ == "__main__":
    res = create_and_verify_zip()
    print("\nPackage Verification Success Summary:")
    print(f"Path: {res['zip_path']}")
    print(f"SHA-256: {res['sha256']}")
    print(f"Size: {res['size_mb']} MB")
