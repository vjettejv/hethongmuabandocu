import re
import sys
from pathlib import Path
from uuid import uuid4

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from verify_ci import assert_isolated, configuration, synthetic_schema  # noqa: E402
from verify_runtime import container_name  # noqa: E402


@pytest.mark.parametrize(
    "kind", ["auth", "user", "post", "category", "message", "review", "search", "favorite"]
)
def test_ci_schema_never_imports_legacy_user_rows(kind):
    ddl = synthetic_schema(kind)
    assert "CREATE TABLE" in ddl
    assert "@" not in ddl and "$2" not in ddl
    if kind != "category":
        assert "INSERT INTO" not in ddl
    else:
        assert "INSERT INTO categories" in ddl and "CI category" in ddl


def test_ci_resources_are_isolated_and_preserve_canonical_compose():
    original = (ROOT / "docker-compose.yml").read_bytes()
    project = "marketplace-ci-" + uuid4().hex[:12]
    folder = ROOT / ".artifacts/phase8/tool-tests" / project
    folder.mkdir(parents=True)
    config = configuration(project, folder)
    assert_isolated(config, project)
    assert (ROOT / "docker-compose.yml").read_bytes() == original
    assert len(config["volumes"]) == 9
    assert list(config["services"]["frontend"]["ports"])[0]["published"] == "0"
    assert all(
        "ports" not in value for key, value in config["services"].items() if key != "frontend"
    )
    assert all("healthcheck" in value for value in config["services"].values())


@pytest.mark.parametrize("project", ["kientrucpm", "marketplace-ci-production", "../other"])
def test_ci_rejects_unowned_project_name(project):
    with pytest.raises(ValueError):
        configuration(project, ROOT)


def test_test_prefix_maps_only_known_containers(monkeypatch):
    monkeypatch.setenv("CANONICAL_TEST_PREFIX", "marketplace-ci-123456abcdef-")
    assert container_name("post-service") == "marketplace-ci-123456abcdef-post-service"
    assert container_name("do-cu-auth-db") == "marketplace-ci-123456abcdef-do-cu-auth-db"
    assert container_name("unrelated-app") == "unrelated-app"
    monkeypatch.setenv("CANONICAL_TEST_PREFIX", "kientrucpm-")
    with pytest.raises(RuntimeError):
        container_name("post-service")


def test_workflows_use_read_only_ci_and_explicit_release_publication():
    def read(name):
        return yaml.load((ROOT / ".github/workflows" / name).read_text(), Loader=yaml.BaseLoader)

    ci = read("ci.yml")
    publish = read("docker-publish.yml")
    assert ci["on"]["push"]["branches"] == ["develop", "main"]
    assert ci["permissions"] == {"contents": "read"}
    assert ci["jobs"]["quality-python"]["steps"][0]["with"]["fetch-depth"] == "0"
    assert publish["on"]["push"]["tags"] == ["v*"]
    assert publish["on"]["workflow_dispatch"]["inputs"]["publish"]["default"] == "false"
    assert publish["jobs"]["images"]["needs"] == "validate"
    assert len(publish["jobs"]["images"]["strategy"]["matrix"]["include"]) == 11
    for workflow in (ci, publish):
        for job in workflow["jobs"].values():
            for step in job.get("steps", []):
                if "uses" in step:
                    assert re.search(r"@[0-9a-f]{40}$", step["uses"])
