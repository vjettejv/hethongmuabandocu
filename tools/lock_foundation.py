"""Pin installed dependency graphs; run with the isolated Python 3.12 development env."""

import importlib.metadata as metadata
from pathlib import Path

from packaging.markers import default_environment
from packaging.requirements import Requirement
from packaging.utils import canonicalize_name

ROOT = Path(__file__).resolve().parents[1]
SERVICES = [
    "api-gateway",
    "auth-service",
    "user-service",
    "post-service",
    "category-service",
    "message-service",
    "notification-service",
    "review-service",
    "search-service",
    "favorite-service",
]


def dependency_graph(roots, environment):
    selected = {}

    def visit(name):
        name = canonicalize_name(name)
        if name in selected:
            return
        distribution = metadata.distribution(name)
        selected[name] = distribution.version
        for raw in distribution.requires or []:
            requirement = Requirement(raw)
            if requirement.marker is None or requirement.marker.evaluate(environment):
                visit(requirement.name)

    for root in roots:
        visit(root)
    return selected


def main():
    linux = dict(
        default_environment(),
        sys_platform="linux",
        os_name="posix",
        platform_system="Linux",
        python_version="3.12",
        python_full_version="3.12.14",
        extra="",
    )
    windows = dict(linux, sys_platform="win32", os_name="nt", platform_system="Windows")
    all_roots = []
    for service in SERVICES:
        roots = [
            Requirement(line).name
            for line in (ROOT / service / "requirements.txt").read_text().splitlines()
            if line
        ]
        all_roots.extend(roots)
        selected = dependency_graph(roots, linux)
        output = (
            "# Python 3.12 / Linux runtime. Exact transitive pins; "
            "regenerate with tools/lock_foundation.py.\n"
        )
        output += "".join(f"{name}=={version}\n" for name, version in sorted(selected.items()))
        (ROOT / service / "requirements.lock.txt").write_text(output, encoding="utf-8")
    roots = all_roots + ["pytest", "pytest-django", "ruff"]
    linux_deps = dependency_graph(roots, linux)
    windows_deps = dependency_graph(roots, windows)
    output = "# Python 3.12 foundation development lock (Linux and Windows).\n"
    for name, version in sorted((linux_deps | windows_deps).items()):
        marker = '; sys_platform == "win32"' if name not in linux_deps else ""
        output += f"{name}=={version}{marker}\n"
    (ROOT / "requirements-dev.lock.txt").write_text(output, encoding="utf-8")
    print("Locked runtime dependencies for ten services and the development environment.")


if __name__ == "__main__":
    main()
