"""Read-only shared-volume inventory, without printing pre-existing filenames."""

import argparse
import json
from pathlib import Path

from verify_runtime import command


def inventory():
    script = """
import hashlib,json,pathlib
root=pathlib.Path('/app/uploads'); result={}
def visit(folder):
 for entry in folder.iterdir():
  name=str(entry.relative_to(root))
  if entry.is_symlink(): result[name]={'symlink':str(entry.readlink())}
  elif entry.is_dir(): visit(entry)
  elif entry.is_file():
   data=entry.read_bytes()
   result[name]={'size':len(data),'sha256':hashlib.sha256(data).hexdigest()}
visit(root); print(json.dumps(result))
"""
    return json.loads(command(["docker", "exec", "post-service", "python", "-c", script]))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--snapshot", type=Path)
    parser.add_argument("--compare", type=Path)
    arguments = parser.parse_args()
    current = inventory()
    if arguments.snapshot:
        arguments.snapshot.parent.mkdir(parents=True, exist_ok=True)
        arguments.snapshot.write_text(json.dumps(current, indent=2) + "\n", encoding="utf-8")
        print(f"Recorded {len(current)} existing upload entries; filenames withheld")
    if arguments.compare:
        before = json.loads(arguments.compare.read_text(encoding="utf-8"))
        assert current == before, "Upload inventory changed; inspect owned fixtures before cleanup"
        print(
            f"PASS: all {len(current)} existing upload entries and bytes unchanged; no extra files"
        )


if __name__ == "__main__":
    main()
