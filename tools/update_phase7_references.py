"""Retain separate parity/rollback assets using immutable Git source after retirement."""

from pathlib import Path

from legacy_reference import SERVICES, export

ROOT = Path(__file__).resolve().parents[1]


def main():
    assert (ROOT / ".artifacts/phase7/retirement-completed.json").exists()
    export(ROOT / ".artifacts/phase7/legacy")
    modified = []
    for path in ROOT.glob("docker-compose.phase*.yml"):
        if path.name == "docker-compose.phase7.rollback-test.yml":
            continue  # already isolated and parameterized
        source = path.read_text(encoding="utf-8")
        result = source.replace("Dockerfile.python", "Dockerfile")
        for service in SERVICES:
            for suffix in ("src", "server.js"):
                result = result.replace(
                    f"./{service}/{suffix}:",
                    f"./.artifacts/phase7/legacy/{service}/{suffix}:",
                )
            if path.name.endswith((".test.yml", ".rollback.yml")):
                result = result.replace(
                    f"context: ./{service}", f"context: ./.artifacts/phase7/legacy/{service}"
                )
        if path.name.endswith(".rollback.yml"):
            result = (
                "# Historical recovery asset; immutable Git export required.\n"
                "# Do not apply to canonical data; see docs/migration/phase-7-rollback.md.\n"
                + result
            )
        if result != source:
            path.write_text(result, encoding="utf-8")
            modified.append(path.name)
    regression = ROOT / "tools/verify_phase6_regressions.ps1"
    source = regression.read_text(encoding="utf-8-sig")
    start = source.index("# Credentials")
    end = source.index("$phase6Extras")
    replacement = (
        "# Private root .env or deployment environment is validated by Compose.\n"
        "& .\\.venv\\Scripts\\python.exe tools/legacy_reference.py "
        "--export .artifacts/phase7/legacy\n"
        "if ($LASTEXITCODE -ne 0) { throw 'Immutable reference export failed' }\n"
        "$phase6Stack = @('-f','docker-compose.yml')\n"
    )
    regression.write_text(source[:start] + replacement + source[end:], encoding="utf-8")
    integration = ROOT / "tools/verify_phase7_integration.ps1"
    source = integration.read_text(encoding="utf-8")
    start = source.index("if (-not $Canonical)")
    end = source.index("try {", start)
    integration.write_text(
        source[:start]
        + "# -Canonical is retained for CLI compatibility; root Compose is always canonical.\n"
        + source[end:],
        encoding="utf-8",
    )
    print(f"Updated {len(modified)} test/rollback overlays and two wrappers; assertions unchanged")


if __name__ == "__main__":
    main()
