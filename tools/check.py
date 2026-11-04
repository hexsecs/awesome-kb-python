#!/usr/bin/env python3
"""Check inventory completeness, identities, links, source integrity and idempotency."""
import collections, hashlib, json, re, shutil, subprocess, sys, tempfile, uuid
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import ingest
ROOT=ingest.ROOT
def hashes(root):
 return {str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in root.rglob("*") if p.is_file() and "__pycache__" not in str(p)}
def main():
 from render_readme import render_readme
 render_readme(ROOT, check=True)
 entries=ingest.parse_list(ROOT/"raw/2026-11-04/README.md"); pages=[]; ids=set()
 for p in (ROOT/"wiki").glob("*.md"):
  f,b=ingest.split_page(p.read_text())
  if f.get("type")!="entity": continue
  uuid.UUID(f["uid"]); assert f["uid"] not in ids; ids.add(f["uid"])
  assert 0<len(f["summary"])<=160
  assert f["depth"] in {"stub","brief","full","deep"}
  pages.append((p,f))
 assert collections.Counter(ingest.identity(e) for e in entries)==collections.Counter(ingest.identity(f) for p,f in pages)
 for p,f in pages: assert f["url"].startswith(("https://","http://"))
 visited=set(); pending=[ROOT/"index.md"]
 while pending:
  p=pending.pop().resolve()
  if p in visited: continue
  visited.add(p)
  for target in re.findall(r"\]\(([^)]+)\)",p.read_text()):
   if "://" in target or target.startswith("#"): continue
   t=(p.parent/target.split("#")[0]).resolve()
   assert t.exists() and t.is_relative_to(ROOT.resolve()),(p,target)
   if t.suffix==".md": pending.append(t)
 assert all(p.resolve() in visited for p,f in pages)
 for line in (ROOT/"raw/MANIFEST.sha256").read_text().splitlines():
  expected,path=line.split("  ",1)
  assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==expected
 with tempfile.TemporaryDirectory() as temp:
  work=Path(temp)/"kb"; shutil.copytree(ROOT,work,ignore=shutil.ignore_patterns("__pycache__",".git"))
  command=[sys.executable,str(work/"tools/ingest.py"),"--date","2026-11-04"]
  before=hashes(work); subprocess.run(command,check=True); assert hashes(work)==before,"ingest drift"
  ep=work/pages[0][0].relative_to(ROOT); original=ep.read_text()
  for depth in ("brief","full","deep"):
   f,b=ingest.split_page(original); f["depth"]=depth; marker="\nAuthored body preserved.\n"
   ep.write_text(ingest.frontmatter(f)+marker)
   subprocess.run(command,check=True)
   nf,nb=ingest.split_page(ep.read_text())
   assert nb==marker and nf["depth"]==depth and nf["uid"]==f["uid"] and nf["created"]==f["created"]
 print(f"PASS {len(entries)} entries; complete inventory, unique UUIDs, summaries, links, hashes, idempotency, authored depth preservation")
if __name__=="__main__": main()

