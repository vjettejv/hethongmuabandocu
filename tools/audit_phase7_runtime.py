"""Audit canonical runtime and classify retained Node references without echoing secrets."""

import argparse
import ast
import json
import re
from pathlib import Path

import yaml
from verify_runtime import SERVICES, command

ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / ".artifacts/phase7"
PATTERN = re.compile(
    r"\b(?:node server\.js|npm start|npm run dev|nodemon|sequelize|express|"
    r"http-proxy-middleware|bcryptjs|jsonwebtoken|nodemailer|multer|socket\.io server)\b",
    re.I,
)
SECRET_KEYS = {"SECRET_KEY", "JWT_SECRET", "DB_PASSWORD", "MYSQL_ROOT_PASSWORD", "SMTP_PASS"}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--compose", type=Path, default=ROOT / "docker-compose.yml")
    args = parser.parse_args()
    config = yaml.safe_load(args.compose.read_text(encoding="utf-8"))
    issues = []
    for name, service in config["services"].items():
        for key, value in service.get("environment", {}).items():
            if key in SECRET_KEYS and value and "${" not in str(value):
                issues.append({"path": args.compose.name, "type": "literal " + key})
        if name in SERVICES:
            assert service["build"]["dockerfile"] == "Dockerfile"
            dockerfile = ROOT / name / service["build"]["dockerfile"]
            assert "FROM python:" in dockerfile.read_text()
            assert not re.search(r"npm|node server", json.dumps(service), re.I)
    for service in SERVICES:
        for path in (ROOT / service).rglob("*.py"):
            if any(part in {"tests", ".venv", "node_modules"} for part in path.parts):
                continue
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.Assign) and isinstance(node.value, ast.Constant):
                    for target in node.targets:
                        if isinstance(target, ast.Name) and target.id in SECRET_KEYS:
                            if node.value.value:
                                issues.append(
                                    {
                                        "path": path.relative_to(ROOT).as_posix(),
                                        "type": "literal " + target.id,
                                    }
                                )
    names = command(["git", "ls-files", "--cached", "--others", "--exclude-standard"]).splitlines()
    matches = []
    for name in names:
        path = ROOT / name
        if not path.is_file() or path.suffix.lower() not in {
            ".md",
            ".json",
            ".py",
            ".js",
            ".jsx",
            ".cjs",
            ".yml",
            ".ps1",
            ".sh",
        }:
            continue
        text = path.read_text(encoding="utf-8-sig", errors="replace")
        found = PATTERN.findall(text)
        if not found:
            continue
        if name.startswith("do-cu-frontend/"):
            classification = "frontend"
        elif name.startswith(("docs/", "contracts/", "contract-tests/")) or name in {
            "README.md",
            "walkthrough.md",
            "HUONG_DAN_TRIEN_KHAI.md",
        }:
            classification = "historical/reference documentation or contract oracle"
        elif name.startswith(("tools/", "integration-tests/")) or (
            name.startswith("docker-compose.phase") and not name.endswith(".e2e.yml")
        ):
            classification = "opt-in parity/recovery/test tooling"
        elif name.split("/")[0] in SERVICES and path.suffix == ".py":
            classification = "Python compatibility comments/literals; no Node entrypoint"
        else:
            raise AssertionError("Unclassified Node reference: " + name)
        matches.append({"path": name, "classification": classification, "matches": len(found)})
    (ARTIFACTS / "runtime-reference-audit.json").write_text(
        json.dumps(matches, indent=2), encoding="utf-8"
    )
    (ARTIFACTS / "secret-scan.json").write_text(json.dumps(issues, indent=2), encoding="utf-8")
    for issue in issues:
        print(issue["path"], issue["type"])
    assert not issues, "Potential literal secrets found; values withheld"
    print(
        f"PASS: canonical Python builds, no literal runtime secrets; "
        f"{len(matches)} Node-reference files classified"
    )


if __name__ == "__main__":
    main()
