#!/usr/bin/env python3
"""Deterministic README-list ingestion with persistent entity identities."""
import argparse, collections, hashlib, json, re, secrets, time, uuid
import yaml
from pathlib import Path
from urllib.parse import urljoin

ROOT = Path(__file__).resolve().parent.parent
CONFIG = json.loads((ROOT/"ingest-config.json").read_text()) if (ROOT/"ingest-config.json").exists() else {}

def mint_uid():
    if hasattr(uuid,"uuid7"):
        return str(uuid.uuid7())
    value = (int(time.time()*1000)<<80) | (7<<76) | (secrets.randbits(12)<<64) | (2<<62) | secrets.randbits(62)
    return str(uuid.UUID(int=value))

def slug(value):
    return re.sub(r"[^a-z0-9]+","-",value.lower()).strip("-") or "entry"

def plain(value):
    value=re.sub(r"\[([^\]]+)\]\([^)]+\)",r"\1",value)
    return re.sub(r"[*_`]", "", value).strip()

def summary(value):
    value=plain(value)
    return value if len(value)<=160 else value[:157].rsplit(" ",1)[0].rstrip(",;:")+"…"

def parse_list(path):
    entries=[]; headings={}; subgroup=None; section=None; active=False
    link=re.compile(r"^(\s*)[-*] \[([^\]]+)\]\((https?://[^\s)]+(?:\([^)]*\)[^)]*)?)\)(.*)$")
    for number,line in enumerate(path.read_text().splitlines(),1):
        h=re.match(r"^(#{1,4}) (.+)$",line)
        if h:
            level=len(h[1]); name=plain(h[2]); subgroup=None
            for k in list(headings):
                if k>=level: del headings[k]
            headings[level]=name
            if CONFIG["parser"]=="python":
                if level==2: section=name
                active=section in {"Projects","Resources"} and level>=2
                category=" / ".join(headings[k] for k in sorted(headings) if k>=3)
            else:
                if level==2: section=name
                active=section not in {None,"Contents","Contribution","License"}
                category=" / ".join(headings[k] for k in sorted(headings) if k>=2)
            continue
        if not active or not category:
            continue
        m=link.match(line)
        if m:
            indent,title,url,tail=m.groups()
            description=tail.strip()
            if description.startswith(" - "): description=description[3:]
            elif description.startswith("- "): description=description[2:]
            elif description.startswith("— "): description=description[2:]
            itemcat=category
            if CONFIG["parser"]=="python" and indent and subgroup:
                itemcat += " / "+subgroup
            description=description.strip()
            entries.append({"title":title,"url":url,"category":itemcat,"list_summary":description,"source_line":number})
        elif CONFIG["parser"]=="python" and re.match(r"^- [^\[]",line):
            subgroup=plain(line[2:])
        elif re.match(r"^\s*[-*] \[",line) and not re.match(r"^\s*[-*] \[[^\]]+\]\(#",line):
            raise ValueError(f"Unparsed listed link at line {number}: {line}")
    if not entries: raise ValueError("Empty ingest refused")
    return entries

def split_page(text):
    if not text.startswith("---\n"): return {},text
    end=text.index("\n---\n",4)
    data=json.loads(json.dumps(yaml.safe_load(text[4:end]) or {}, default=str))
    return data,text[end+5:]

def identity(e):
    return (e["title"], e["url"].rstrip("/").lower(), e["category"])

def frontmatter(fields,extra=""):
    return "---\n"+"\n".join(k+": "+json.dumps(v,ensure_ascii=False) for k,v in fields.items())+("\n"+extra if extra else "")+"\n---\n"

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--source",default=str(ROOT/"raw/2026-11-04"))
    ap.add_argument("--date",default=time.strftime("%Y-%m-%d",time.gmtime()))
    args=ap.parse_args(); src=Path(args.source)
    capture=json.loads((src/"capture.json").read_text())
    commit=capture["source_commit"]; source="https://github.com/"+CONFIG["source"]
    entries=parse_list(src/"README.md")
    wiki=ROOT/"wiki"; wiki.mkdir(exist_ok=True)
    existing={}; byname={}
    for p in sorted(wiki.glob("*.md")):
        f,b=split_page(p.read_text())
        if f.get("type")=="entity":
            existing[identity(f)]=(p,f,b)
            byname[(f["title"],f["category"])]=(p,f,b)
    taken={p.stem for p in wiki.glob("*.md")}
    groups=collections.OrderedDict(); matched=set(); created=changed=0
    for e in entries:
        key=identity(e); old=existing.get(key) or byname.get((e["title"],e["category"]))
        if old:
            p,f,body=old
            if p in matched: old=None
        if not old:
            stem=slug(e["title"]); candidate=stem; n=2
            while candidate in taken: candidate=f"{stem}-{n}"; n+=1
            taken.add(candidate); p=wiki/(candidate+".md"); f={}; body=""; created+=1
        matched.add(p)
        desc=e["list_summary"] or f'{e["title"]}, listed under {e["category"]} in {CONFIG["source"]}.'
        values={"uid":f.get("uid",mint_uid()),"title":e["title"],"summary":summary(desc),"type":"entity","category":e["category"],"url":e["url"],
                "status":f.get("status","published" if "e-books" in e["category"].lower() else "unknown"),
                "created":f.get("created",args.date),"updated":f.get("updated",args.date),"depth":f.get("depth","stub"),
                "source_list":CONFIG["source"],"source_commit":f.get("source_commit",commit),"list_summary":e["list_summary"],
                "sources":f.get("sources",[{"url":source+"/blob/"+commit+"/README.md","retrieved":capture["retrieved"]}])}
        for k,v in f.items():
            if k not in values: values[k]=v
        # Preserve arbitrary nested YAML blocks from authored pages verbatim.
        extra=""
        if old:
            oldtext=p.read_text(); fm=oldtext[4:oldtext.index("\n---\n",4)]
            blocks=re.split(r"\n(?=[A-Za-z_][\w-]*:)",fm)
            for block in blocks:
                k=block.split(":",1)[0]
                if "\n" in block and k not in {"sources"}:
                    values.pop(k,None); extra += block+"\n"
            if f.get("list_summary")!=e["list_summary"] or f.get("url")!=e["url"]:
                values["updated"]=args.date; values["source_commit"]=commit; changed+=1
        if values["depth"]=="stub":
            # Descriptions may contain source-relative links; qualify those.
            description=re.sub(r"\]\((?![a-z]+://)([^)]+)\)",lambda m:"]("+urljoin(source+"/blob/"+commit+"/README.md",m[1])+")",desc)
            body="\n"+description+"\n\n"
            if not e["list_summary"]: body+="The source provides a bare link; the orientation above is generated from its title and category.\n\n"
            body+=f'- **Resource:** {e["url"]}\n- **Source:** [{CONFIG["source"]}]({source}/blob/{commit}/README.md#L{e["source_line"]})\n- **Depth:** Generated stub; no independent resource verification.\n'
        text=frontmatter(values,extra.rstrip())+body
        if not p.exists() or p.read_text()!=text: p.write_text(text)
        groups.setdefault(e["category"],[]).append((p,values))
    for p,f,b in existing.values():
        if p not in matched:
            f["status"]="archived"
            if "Delisted from canon" not in b: b+="\n> Delisted from canon; retained as a historical entry.\n"
            p.write_text(frontmatter(f)+b); groups.setdefault(f["category"],[]).append((p,f))
    catnames=set(); index=[f'# {CONFIG["title"]}',"","Generated from the canon list. Entries remain at their recorded depth.","","## Categories",""]
    for category,items in groups.items():
        cs=slug(category); base=cs; n=2
        while cs in catnames: cs=f"{base}-{n}"; n+=1
        catnames.add(cs)
        lines=["---","type: index","title: "+json.dumps(category),"---","",f"# {category}",""]
        for p,f in items: lines.append(f'- [{f["title"]}]({p.name}) — {f["summary"]}')
        (wiki/f"index-{cs}.md").write_text("\n".join(lines)+"\n")
        index.append(f"- [{category}](wiki/index-{cs}.md) — {len(items)} entries")
    (ROOT/"index.md").write_text("\n".join(index)+"\n")
    from render_readme import render_readme
    render_readme(ROOT)
    print(f'ingest {CONFIG["id"]}: {len(entries)} entries, {len(groups)} categories, {created} created, {changed} changed')

if __name__=="__main__": main()

