#!/usr/bin/env python3
"""Build a deterministic, text-only FreeCAD documentation corpus."""
from __future__ import annotations
import argparse, hashlib, json, os, re, shutil, subprocess, sys, tempfile, urllib.error, urllib.parse, urllib.request
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any, Iterable
PROJECT_ROOT=Path(__file__).resolve().parents[1]
CONFIG_PATH=PROJECT_ROOT/"source-config.json"; MANIFEST_PATH=PROJECT_ROOT/"manifest.json"; CORPUS_INFO_PATH=PROJECT_ROOT/"CORPUS_INFO.md"
REPORT_JSON_PATH=PROJECT_ROOT/"reports"/"inventory.json"; REPORT_MD_PATH=PROJECT_ROOT/"reports"/"inventory.md"
USER_AGENT="freecad-agent-docs-sync/2.0"; SYNC_FORMAT_VERSION=2; WIKI_BATCH_SIZE=50
class SyncError(RuntimeError): pass

def parse_args():
    p=argparse.ArgumentParser(description=__doc__); p.add_argument("--force",action="store_true"); p.add_argument("--ref"); return p.parse_args()
def load_json(path):
    try: return json.loads(path.read_text(encoding="utf-8"))
    except (OSError,json.JSONDecodeError) as exc: raise SyncError(f"Cannot read valid JSON from {path}: {exc}") from exc
def write_json(path,payload):
    path.parent.mkdir(parents=True,exist_ok=True); path.write_text(json.dumps(payload,indent=2,ensure_ascii=False,sort_keys=True)+"\n",encoding="utf-8",newline="\n")
def sha256(content): return hashlib.sha256(content).hexdigest()
def compile_glob(pattern):
    pattern=pattern.lstrip("/"); i=0; out=["^"]
    while i<len(pattern):
        char=pattern[i]
        if char=="*":
            if i+1<len(pattern) and pattern[i+1]=="*":
                i+=2
                if i<len(pattern) and pattern[i]=="/": out.append("(?:.*/)?"); i+=1
                else: out.append(".*")
                continue
            out.append("[^/]*")
        elif char=="?": out.append("[^/]")
        else: out.append(re.escape(char))
        i+=1
    out.append("$"); return re.compile("".join(out))
def matches(path,patterns): return any(pattern.fullmatch(path) for pattern in patterns)
def github_headers():
    h={"Accept":"application/vnd.github+json","User-Agent":USER_AGENT,"X-GitHub-Api-Version":"2022-11-28"}; token=os.environ.get("GITHUB_TOKEN")
    if token: h["Authorization"]=f"Bearer {token}"
    return h
def fetch_json(url,headers=None):
    try:
        with urllib.request.urlopen(urllib.request.Request(url,headers=headers or {"User-Agent":USER_AGENT}),timeout=90) as response: payload=json.load(response)
    except (urllib.error.URLError,TimeoutError,json.JSONDecodeError) as exc: raise SyncError(f"Request failed for {url}: {exc}") from exc
    if not isinstance(payload,dict): raise SyncError(f"Request did not return a JSON object: {url}")
    return payload
def api_url(base,params): return f"{base}?{urllib.parse.urlencode(params)}"
def fetch_github_blob(repo,commit,path):
    url=f"https://raw.githubusercontent.com/{repo}/{commit}/{urllib.parse.quote(path,safe='/')}"
    try:
        with urllib.request.urlopen(urllib.request.Request(url,headers={"User-Agent":USER_AGENT}),timeout=90) as response: return response.read()
    except (urllib.error.URLError,TimeoutError) as exc: raise SyncError(f"Cannot download {repo}:{path}: {exc}") from exc
def resolve_github_commit(repo,ref):
    c=fetch_json(f"https://api.github.com/repos/{repo}/commits/{urllib.parse.quote(ref,safe='')}",github_headers())
    try: return c["sha"],c["commit"]["tree"]["sha"]
    except (KeyError,TypeError) as exc: raise SyncError(f"Incomplete commit response for {repo}@{ref}") from exc
def fetch_github_tree(repo,tree_sha):
    p=fetch_json(f"https://api.github.com/repos/{repo}/git/trees/{tree_sha}?recursive=1",github_headers())
    if p.get("truncated"): raise SyncError(f"Truncated GitHub tree for {repo}")
    if not isinstance(p.get("tree"),list): raise SyncError(f"Missing GitHub tree for {repo}")
    return p["tree"]
def fetch_tree_with_git(repo,ref):
    parent=PROJECT_ROOT/".sync-tmp"; parent.mkdir(parents=True,exist_ok=True)
    try:
        with tempfile.TemporaryDirectory(dir=parent) as temporary:
            checkout=Path(temporary)/"metadata"; subprocess.run(["git","clone","--quiet","--depth","1","--filter=blob:none","--no-checkout","--branch",ref,f"https://github.com/{repo}.git",str(checkout)],check=True,text=True,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
            commit=subprocess.check_output(["git","-C",str(checkout),"rev-parse","HEAD^{commit}"],text=True).strip(); tree_sha=subprocess.check_output(["git","-C",str(checkout),"rev-parse","HEAD^{tree}"],text=True).strip(); raw=subprocess.check_output(["git","-C",str(checkout),"ls-tree","-r","-z","HEAD"]); entries=[]
            for record in raw.split(b"\0"):
                if record:
                    header,path=record.split(b"\t",1); _mode,kind,obj_sha=header.decode("ascii").split(); entries.append({"path":path.decode("utf-8"),"type":kind,"sha":obj_sha,"size":None})
            return commit,tree_sha,entries
    except (FileNotFoundError,subprocess.CalledProcessError,ValueError,UnicodeDecodeError) as exc: raise SyncError(f"Git metadata fallback failed for {repo}@{ref}: {exc}") from exc
    finally:
        try: parent.rmdir()
        except OSError: pass
def document_extension(path,extensions):
    lowered=path.lower()
    for ext in sorted(extensions,key=len,reverse=True):
        if lowered.endswith(ext.lower()): return ext.lower()
    return "README" if PurePosixPath(path).name.lower().startswith("readme") else None
def safe_destination(root,relative):
    destination=(root/PurePosixPath(relative)).resolve()
    try: destination.relative_to(root.resolve())
    except ValueError as exc: raise SyncError(f"Unsafe output path: {relative}") from exc
    return destination
def batched(values,size):
    for index in range(0,len(values),size): yield values[index:index+size]
def discover_github(source,ref_override):
    sid=source["id"]; repo=source["repository"]; ref=ref_override if sid=="freecad-source" and ref_override else source["ref"]
    try: commit,tree_sha=resolve_github_commit(repo,ref); tree=fetch_github_tree(repo,tree_sha)
    except SyncError as api_error: print(f"GitHub API failed for {repo}; trying git: {api_error}",file=sys.stderr); commit,tree_sha,tree=fetch_tree_with_git(repo,ref)
    blobs=[e for e in tree if e.get("type")=="blob"]; includes=[compile_glob(v) for v in source["include_patterns"]]; excludes=[compile_glob(v) for v in source["exclude_patterns"]]; max_bytes=int(source["max_file_bytes"]); selected=[]; skipped=[]
    for entry in blobs:
        path=entry["path"]
        if not matches(path,includes): continue
        if matches(path,excludes): skipped.append({"path":path,"reason":"matched an exclude pattern"}); continue
        size=entry.get("size")
        if size is not None and int(size)>max_bytes: skipped.append({"path":path,"reason":f"larger than {max_bytes} bytes"}); continue
        selected.append({"path":path,"sha":entry["sha"],"size":None if size is None else int(size)})
    selected.sort(key=lambda e:e["path"]); counts=Counter(); sizes=Counter(); unknown=Counter()
    for entry in blobs:
        ext=document_extension(entry["path"],list(source["inventory_extensions"]))
        if ext:
            counts[ext]+=1
            if entry.get("size") is None: unknown[ext]+=1
            else: sizes[ext]+=int(entry["size"])
    stats={ext:{"files":counts[ext],"bytes":None if unknown[ext] else sizes[ext]} for ext in sorted(counts)}
    return {"id":sid,"type":"github","config":source,"metadata":{"repository":repo,"ref":ref,"commit":commit,"tree":tree_sha,"web_url":source["web_url"]},"entries":selected,"skipped":sorted(skipped,key=lambda e:e["path"]),"total_upstream_files":len(blobs),"candidate_extension_stats":stats}
def mediawiki_query(source,params):
    common={"format":"json","formatversion":2}; common.update(params); return fetch_json(api_url(source["api_url"],common),{"User-Agent":USER_AGENT})
def discover_mediawiki(source):
    members={}; namespace=int(source["namespace"])
    for category in source["categories"]:
        continuation=None
        while True:
            params={"action":"query","list":"categorymembers","cmtitle":f"Category:{category}","cmtype":"page","cmnamespace":namespace,"cmlimit":"max"}
            if continuation: params["cmcontinue"]=continuation
            payload=mediawiki_query(source,params)
            try: category_members=payload["query"]["categorymembers"]
            except (KeyError,TypeError) as exc: raise SyncError(f"Incomplete MediaWiki category response for {category}") from exc
            for member in category_members:
                pageid=int(member["pageid"]); record=members.setdefault(pageid,{"pageid":pageid,"title":member["title"],"categories":set()}); record["categories"].add(category)
            continuation=payload.get("continue",{}).get("cmcontinue")
            if not continuation: break
    pages=[]
    for batch in batched(sorted(members),WIKI_BATCH_SIZE):
        payload=mediawiki_query(source,{"action":"query","prop":"info","pageids":"|".join(str(v) for v in batch)})
        try: pages.extend(payload["query"]["pages"])
        except (KeyError,TypeError) as exc: raise SyncError("Incomplete MediaWiki page-info response") from exc
    excludes=[re.compile(v) for v in source["exclude_title_patterns"]]; language=source["language"]; max_bytes=int(source["max_page_bytes"]); selected=[]; skipped=[]
    for page in pages:
        title=page.get("title",""); pageid=int(page.get("pageid",0)); reason=None
        if page.get("missing"): reason="page is missing"
        elif int(page.get("ns",-1))!=namespace: reason="outside the selected namespace"
        elif page.get("contentmodel")!="wikitext": reason=f"content model is {page.get('contentmodel')}"
        elif page.get("pagelanguage")!=language: reason=f"page language is {page.get('pagelanguage')}"
        elif any(pattern.search(title) for pattern in excludes): reason="title matched an exclude pattern"
        elif int(page.get("length",0))>max_bytes: reason=f"larger than {max_bytes} bytes"
        if reason: skipped.append({"path":title or str(pageid),"reason":reason})
        else: selected.append({"pageid":pageid,"title":title,"lastrevid":int(page["lastrevid"]),"length":int(page.get("length",0)),"categories":sorted(members[pageid]["categories"])})
    selected.sort(key=lambda e:(e["title"].casefold(),e["pageid"])); rights=mediawiki_query(source,{"action":"query","meta":"siteinfo","siprop":"general|rightsinfo"})
    try: general=rights["query"]["general"]; rightsinfo=rights["query"]["rightsinfo"]
    except (KeyError,TypeError) as exc: raise SyncError("Incomplete MediaWiki site-info response") from exc
    metadata={"api_url":source["api_url"],"web_url":source["web_url"],"site_name":general.get("sitename","FreeCAD Documentation"),"generator":general.get("generator"),"language":language,"categories":list(source["categories"]),"license_name":rightsinfo.get("text"),"license_url":rightsinfo.get("url")}
    return {"id":source["id"],"type":"mediawiki","config":source,"metadata":metadata,"entries":selected,"skipped":sorted(skipped,key=lambda e:e["path"].casefold()),"total_upstream_files":len(members)}
def selection_fingerprint(config,discoveries):
    lines=[f"sync-format\0{SYNC_FORMAT_VERSION}",json.dumps(config,ensure_ascii=False,sort_keys=True,separators=(",",":"))]
    for discovery in discoveries:
        lines.append(f"source\0{discovery['id']}\0{discovery['type']}")
        for entry in discovery["entries"]:
            lines.append(f"{entry['path']}\0{entry['sha']}" if discovery["type"]=="github" else f"{entry['pageid']}\0{entry['title']}\0{entry['lastrevid']}")
    return sha256("\n".join(lines).encode("utf-8"))
def manifest_entry(discovery,source_path,output_path,content,**extra):
    entry={"source_id":discovery["id"],"source_type":discovery["type"],"source_path":source_path,"output_path":str(output_path),"sha256":sha256(content),"size":len(content)}; entry.update(extra); return entry
def download_github(discovery,staging):
    source=discovery["config"]; metadata=discovery["metadata"]; name=source["destination"]; destination=staging/name; max_bytes=int(source["max_file_bytes"]); downloaded=[]; skipped=list(discovery["skipped"])
    for index,entry in enumerate(discovery["entries"],start=1):
        path=entry["path"]; print(f"[{discovery['id']} {index}/{len(discovery['entries'])}] {path}"); content=fetch_github_blob(metadata["repository"],metadata["commit"],path)
        if len(content)>max_bytes: skipped.append({"path":path,"reason":f"larger than {max_bytes} bytes"}); continue
        try: content.decode("utf-8")
        except UnicodeDecodeError: skipped.append({"path":path,"reason":"not valid UTF-8 text"}); continue
        output=safe_destination(destination,path); output.parent.mkdir(parents=True,exist_ok=True); output.write_bytes(content); url=f"https://github.com/{metadata['repository']}/blob/{metadata['commit']}/{urllib.parse.quote(path,safe='/')}"
        downloaded.append(manifest_entry(discovery,path,PurePosixPath("corpus")/name/PurePosixPath(path),content,source_url=url,source_revision=metadata["commit"],git_blob_sha=entry["sha"]))
    return downloaded,sorted(skipped,key=lambda i:i["path"])
def wiki_filename(title,pageid):
    stem=re.sub(r'[<>:"/\\|?*\x00-\x1f]',"_",title.replace(" ","_")); stem=re.sub(r"_+","_",stem).strip(" ._") or "page"; stem=stem[:120].rstrip(" ._") or "page"; first=stem[0].upper(); bucket=first if "A"<=first<="Z" else "_"; return PurePosixPath("pages")/bucket/f"{stem}--{pageid}.wiki"
def download_mediawiki(discovery,staging):
    source=discovery["config"]; name=source["destination"]; destination=staging/name; max_bytes=int(source["max_page_bytes"]); by_id={e["pageid"]:e for e in discovery["entries"]}; downloaded=[]; skipped=list(discovery["skipped"]); completed=0
    for batch in batched(sorted(by_id),WIKI_BATCH_SIZE):
        payload=mediawiki_query(source,{"action":"query","prop":"info|revisions","pageids":"|".join(str(v) for v in batch),"rvprop":"ids|timestamp|content|contentmodel","rvslots":"main"})
        try: pages=payload["query"]["pages"]
        except (KeyError,TypeError) as exc: raise SyncError("Incomplete MediaWiki revision response") from exc
        for page in pages:
            pageid=int(page["pageid"]); expected=by_id.get(pageid)
            if expected is None: raise SyncError(f"Unexpected MediaWiki page ID: {pageid}")
            try: revision=page["revisions"][0]; text=revision["slots"]["main"]["content"]
            except (KeyError,IndexError,TypeError) as exc: raise SyncError(f"No readable revision for {page['title']}") from exc
            if int(revision["revid"])!=expected["lastrevid"]: raise SyncError(f"MediaWiki page changed during sync; retry: {page['title']}")
            content=text.encode("utf-8")
            if len(content)>max_bytes: skipped.append({"path":page["title"],"reason":f"larger than {max_bytes} bytes"}); continue
            relative=wiki_filename(page["title"],pageid); output=safe_destination(destination,str(relative)); output.parent.mkdir(parents=True,exist_ok=True); output.write_bytes(content); slug=urllib.parse.quote(page["title"].replace(" ","_"),safe="()_-/")
            downloaded.append(manifest_entry(discovery,page["title"],PurePosixPath("corpus")/name/relative,content,source_url=f"{source['web_url']}/{slug}",source_revision=str(revision["revid"]),revision_timestamp=revision["timestamp"],page_id=pageid,categories=expected["categories"])); completed+=1
        print(f"[{discovery['id']}] downloaded {completed}/{len(by_id)} pages")
    readme=("# FreeCAD Wiki corpus\n\nRaw English MediaWiki source selected from the live FreeCAD Documentation wiki.\n\n"+f"- API: `{source['api_url']}`\n- Categories: {', '.join(f'`{v}`' for v in source['categories'])}\n- Pages: {len(downloaded):,}\n- License: [{discovery['metadata']['license_name']}]({discovery['metadata']['license_url']})\n\nThe `--<pageid>` suffix keeps filenames unique. Revision IDs and original URLs are in `manifest.json`. MediaWiki templates and translation markers are preserved as source evidence.\n").encode("utf-8")
    readme_path=destination/"README.md"; readme_path.parent.mkdir(parents=True,exist_ok=True); readme_path.write_bytes(readme); downloaded.append(manifest_entry({"id":"generated","type":"generated"},"freecad-wiki/README.md",PurePosixPath("corpus")/name/"README.md",readme,source_revision=str(SYNC_FORMAT_VERSION)))
    return downloaded,sorted(skipped,key=lambda i:i["path"].casefold())
def ensure_replaceable_corpus(path):
    expected=(PROJECT_ROOT/"corpus").resolve()
    if path.resolve()!=expected: raise SyncError(f"Refusing to replace unexpected corpus directory: {path.resolve()}")
def write_inventory_markdown(report):
    lines=["# FreeCAD documentation inventory","",f"- Sources: {len(report['sources']):,}",f"- Selected text files: {report['selected_files']:,}",f"- Selected bytes: {report['selected_bytes']:,}",f"- Rough token estimate: {report['estimated_tokens']:,}",f"- Corpus byte limit: {report['max_corpus_bytes']:,}","","## Source summary","","| Source | Type | Revision | Files | Bytes | Skipped |","|---|---|---|---:|---:|---:|"]
    for source in report["sources"]: lines.append(f"| `{source['id']}` | {source['type']} | `{source['revision']}` | {source['selected_files']:,} | {source['selected_bytes']:,} | {len(source['skipped']):,} |")
    for source in report["sources"]:
        lines.extend(["",f"## `{source['id']}` selected files",""])
        for entry in source["included"]: lines.append(f"- `{entry['source_path']}` ({entry['size']:,} bytes)")
        lines.extend(["",f"### `{source['id']}` skipped files",""])
        if source["skipped"]:
            for entry in source["skipped"]: lines.append(f"- `{entry['path']}`: {entry['reason']}")
        else: lines.append("None.")
    REPORT_MD_PATH.parent.mkdir(parents=True,exist_ok=True); REPORT_MD_PATH.write_text("\n".join(lines)+"\n",encoding="utf-8",newline="\n")
def write_corpus_info(discoveries,downloaded,generated_at):
    counts=Counter(e["source_id"] for e in downloaded); sizes=Counter()
    for entry in downloaded: sizes[entry["source_id"]]+=int(entry["size"])
    lines=["# Corpus snapshot","",f"- Generated at: `{generated_at}`",f"- UTF-8 files: {len(downloaded):,}",f"- Corpus bytes: {sum(e['size'] for e in downloaded):,}","","## Sources",""]
    for discovery in discoveries:
        meta=discovery["metadata"]
        if discovery["type"]=="github": revision=meta["commit"]; label=f"[{meta['repository']}]({meta['web_url']})"
        else: revision=f"{len(discovery['entries']):,} selected page revisions"; label=f"[{meta['site_name']}]({meta['web_url']})"
        lines.append(f"- `{discovery['id']}`: {label}; `{revision}`; {counts[discovery['id']]:,} files; {sizes[discovery['id']]:,} bytes")
    lines.extend(["","GitHub files preserve upstream blobs byte-for-byte. Wiki files preserve the UTF-8 wikitext returned for the recorded MediaWiki revision IDs. Detailed paths, revisions, URLs, hashes, and selection reports are stored in `manifest.json` and `reports/inventory.md`."])
    CORPUS_INFO_PATH.write_text("\n".join(lines)+"\n",encoding="utf-8",newline="\n")
def main():
    args=parse_args(); config=load_json(CONFIG_PATH)
    if int(config.get("schema_version",0))!=2: raise SyncError("source-config.json must use schema version 2")
    corpus_root=(PROJECT_ROOT/config["destination"]).resolve(); ensure_replaceable_corpus(corpus_root); discoveries=[]
    for source in config["sources"]:
        print(f"Discovering {source['id']} ({source['type']})...")
        if source["type"]=="github": discoveries.append(discover_github(source,args.ref))
        elif source["type"]=="mediawiki": discoveries.append(discover_mediawiki(source))
        else: raise SyncError(f"Unsupported source type: {source['type']}")
    fingerprint=selection_fingerprint(config,discoveries)
    if MANIFEST_PATH.exists() and not args.force:
        existing=load_json(MANIFEST_PATH)
        if existing.get("schema_version")==2 and existing.get("selection_fingerprint")==fingerprint and corpus_root.exists() and CORPUS_INFO_PATH.exists() and REPORT_JSON_PATH.exists() and REPORT_MD_PATH.exists(): print("No selected documentation changes across configured sources."); return 0
    predicted=sum(int(e.get("size") or e.get("length") or 0) for d in discoveries for e in d["entries"]); limit=int(config["max_corpus_bytes"])
    if predicted>limit: raise SyncError(f"Selected upstream text is {predicted:,} bytes, above the {limit:,}-byte corpus budget")
    parent=PROJECT_ROOT/".sync-tmp"; parent.mkdir(parents=True,exist_ok=True); downloaded=[]; source_reports=[]
    try:
        with tempfile.TemporaryDirectory(dir=parent) as temporary:
            staging=Path(temporary)/"corpus"; staging.mkdir(parents=True)
            for discovery in discoveries:
                if discovery["type"]=="github": files,skipped=download_github(discovery,staging); revision=discovery["metadata"]["commit"]
                else: files,skipped=download_mediawiki(discovery,staging); revision=f"{len(discovery['entries'])} page revisions"
                downloaded.extend(files); source_reports.append({"id":discovery["id"],"type":discovery["type"],"revision":revision,"metadata":discovery["metadata"],"selected_files":len(files),"selected_bytes":sum(e["size"] for e in files),"included":files,"skipped":skipped,"total_upstream_files":discovery["total_upstream_files"],"candidate_extension_stats":discovery.get("candidate_extension_stats",{})})
            actual=sum(e["size"] for e in downloaded)
            if actual>limit: raise SyncError(f"Generated corpus is {actual:,} bytes, above the {limit:,}-byte limit")
            if corpus_root.exists(): shutil.rmtree(corpus_root)
            shutil.move(str(staging),str(corpus_root))
    finally:
        try: parent.rmdir()
        except OSError: pass
    generated_at=datetime.now(timezone.utc).replace(microsecond=0).isoformat(); downloaded.sort(key=lambda e:e["output_path"])
    manifest={"schema_version":2,"generated_at":generated_at,"selection_fingerprint":fingerprint,"max_corpus_bytes":limit,"selected_bytes":sum(e["size"] for e in downloaded),"sources":[{"id":d["id"],"type":d["type"],**d["metadata"]} for d in discoveries],"files":downloaded}
    report={"schema_version":2,"generated_at":generated_at,"max_corpus_bytes":limit,"selected_files":len(downloaded),"selected_bytes":manifest["selected_bytes"],"estimated_tokens":round(manifest["selected_bytes"]/4),"sources":source_reports}
    write_json(MANIFEST_PATH,manifest); write_json(REPORT_JSON_PATH,report); write_inventory_markdown(report); write_corpus_info(discoveries,downloaded,generated_at)
    upstream_license=corpus_root/"freecad-source"/"LICENSE"
    if upstream_license.exists(): shutil.copyfile(upstream_license,PROJECT_ROOT/"LICENSE")
    print(f"Synced {len(downloaded):,} UTF-8 files ({manifest['selected_bytes']:,} bytes) from {len(discoveries)} sources."); return 0
if __name__=="__main__":
    try: raise SystemExit(main())
    except SyncError as error: print(f"sync error: {error}",file=sys.stderr); raise SystemExit(1) from error