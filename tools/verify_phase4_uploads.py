"""Read-only shared-volume inventory, without printing pre-existing filenames."""

import argparse
import json
from pathlib import Path

from verify_runtime import command

SCRIPT = r"""
const fs=require('fs'),path=require('path'),crypto=require('crypto');
const root='/app/uploads', result={};
function visit(dir) {
 for (const entry of fs.readdirSync(dir,{withFileTypes:true})) {
  const filename=path.join(dir,entry.name), relative=path.relative(root,filename);
  if (entry.isDirectory()) visit(filename);
  else if (entry.isFile()) {
   const data=fs.readFileSync(filename);
   result[relative]={size:data.length,sha256:crypto.createHash('sha256').update(data).digest('hex')};
  } else if (entry.isSymbolicLink()) result[relative]={symlink:fs.readlinkSync(filename)};
 }
}
visit(root); process.stdout.write(JSON.stringify(result));
"""


def inventory():
    # Post remains the canonical static server through Review's Phase 5 cutover.
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
