from __future__ import annotations

import ast
import hashlib
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


def git(root: Path, *args: str) -> str:
    return subprocess.check_output(("git", *args), cwd=root, text=True, encoding="utf-8", errors="replace")


@dataclass(frozen=True)
class PathLifecycle:
    path: str
    first_commit: str
    last_commit: str
    change_count: int
    statuses: tuple[str, ...]


def commit_history(root: Path) -> list[dict[str, object]]:
    rows=[]
    for index,line in enumerate(git(root,"rev-list","--all","--reverse","--topo-order").splitlines()):
        meta=git(root,"show","-s","--format=%H%x00%P%x00%aI%x00%cI%x00%s",line).rstrip("\n").split("\x00")
        rows.append({"chronological_index":index,"commit":meta[0],"parents":meta[1].split() if meta[1] else [],"author_time":meta[2],"commit_time":meta[3],"subject":meta[4]})
    return rows


def path_lifecycles(root: Path) -> list[PathLifecycle]:
    data:dict[str,dict[str,object]]={}
    stream=git(root,"log","--all","--reverse","--format=@@%H","--name-status","--find-renames")
    commit=None
    for line in stream.splitlines():
        if line.startswith("@@"): commit=line[2:]; continue
        if not line or commit is None: continue
        parts=line.split("\t"); status=parts[0]; path=parts[-1]
        row=data.setdefault(path,{"first":commit,"last":commit,"count":0,"statuses":set()})
        row["last"]=commit; row["count"]=int(row["count"])+1; row["statuses"].add(status[0])
    return [PathLifecycle(p,str(v['first']),str(v['last']),int(v['count']),tuple(sorted(v['statuses']))) for p,v in sorted(data.items())]


IDENTIFIER=re.compile(r"(?i)(batch\d{3}[a-z]?|v\d+\.\d+|\d+\.\d+\.\d+(?:[a-z0-9.]*)?)")


def historical_denominator(commits: Iterable[dict[str,object]], paths: Iterable[PathLifecycle]) -> list[dict[str,object]]:
    found:dict[str,dict[str,object]]={}
    for row in commits:
        for match in IDENTIFIER.findall(str(row['subject'])):
            key=match.lower(); found.setdefault(key,{"historical_id":key,"kinds":set(),"first_commit":row['commit'],"last_commit":row['commit'],"paths":set()}); found[key]['last_commit']=row['commit']; found[key]['kinds'].add('commit_subject')
    for life in paths:
        for match in IDENTIFIER.findall(life.path):
            key=match.lower(); item=found.setdefault(key,{"historical_id":key,"kinds":set(),"first_commit":life.first_commit,"last_commit":life.last_commit,"paths":set()}); item['last_commit']=life.last_commit; item['paths'].add(life.path); item['kinds'].add('repository_path')
    rows=[]
    for key,item in sorted(found.items()):
        rows.append({"historical_id":key,"kind":"batch_or_campaign" if key.startswith('batch') else "protocol_or_version","first_commit":item['first_commit'],"last_commit":item['last_commit'],"source_paths":sorted(item['paths']),"discovery_sources":sorted(item['kinds']),"disposition":"PRESERVED_HISTORICAL","migration_proof":None,"current_authority":False,"open_blocker":"capability-specific equivalence required before MIGRATED"})
    return rows


def python_call_graph(root: Path, roots: Iterable[str]) -> dict[str,object]:
    nodes=[]; edges=[]; parse_failures=[]
    for rel in roots:
        path=root/rel
        if not path.is_file(): continue
        try: tree=ast.parse(path.read_text(encoding='utf-8',errors='replace'))
        except SyntaxError as exc: parse_failures.append({"path":rel,"error":str(exc)}); continue
        nodes.append({"path":rel,"sha256":hashlib.sha256(path.read_bytes()).hexdigest()})
        for node in ast.walk(tree):
            if isinstance(node,ast.Import):
                for alias in node.names: edges.append({"source":rel,"target":alias.name,"type":"import"})
            elif isinstance(node,ast.ImportFrom) and node.module: edges.append({"source":rel,"target":node.module,"type":"import_from"})
    return {"nodes":nodes,"edges":edges,"parse_failures":parse_failures}
