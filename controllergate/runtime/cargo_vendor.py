from __future__ import annotations

from datetime import datetime
import hashlib
import json
from pathlib import Path
import tarfile
import tomllib
from typing import Any

from .authorized_fetch import authorized_fetch


def parse_cargo_lock(path: Path) -> list[dict[str, Any]]:
    value=tomllib.loads(path.read_text(encoding="utf-8"));rows=[]
    for item in value.get("package",[]):
        source=str(item.get("source") or "")
        if source.startswith("registry+"):
            rows.append({"name":item["name"],"version":item["version"],"source":source,"checksum":item.get("checksum")})
    return rows


def safe_extract_crate(archive: Path, destination: Path, *, package: str, version: str, checksum: str) -> dict[str, Any]:
    expected_root=f"{package}-{version}";seen:set[str]=set();files:dict[str,str]={}
    destination.mkdir(parents=True,exist_ok=True)
    with tarfile.open(archive) as source:
        members=source.getmembers()
        for member in members:
            parts=Path(member.name).parts
            if not parts or parts[0]!=expected_root or member.name.startswith(("/","\\")) or ".." in parts or member.issym() or member.islnk(): return {"status":"BLOCK","blocker":"cargo_vendor_archive_unsafe"}
            relative=Path(*parts[1:]).as_posix()
            if relative in seen:return {"status":"BLOCK","blocker":"cargo_vendor_duplicate_path"}
            seen.add(relative)
            if member.isfile():
                payload=source.extractfile(member).read();target=destination/relative;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(payload);files[relative]=hashlib.sha256(payload).hexdigest()
    if not (destination/"Cargo.toml").is_file():return {"status":"BLOCK","blocker":"cargo_vendor_manifest_missing"}
    checksum_record={"files":dict(sorted(files.items())),"package":checksum};(destination/".cargo-checksum.json").write_text(json.dumps(checksum_record,sort_keys=True,separators=(",",":"))+"\n",encoding="utf-8",newline="\n")
    return {"status":"PASS","file_count":len(files),"package_checksum":checksum,"tree_hash":hashlib.sha256(json.dumps(files,sort_keys=True).encode()).hexdigest()}


def build_vendor_tree(*, lock_path: Path, vendor_root: Path, cutoff: str, phase_id: str, policy: dict[str,Any], ledger_path: Path) -> dict[str,Any]:
    packages=parse_cargo_lock(lock_path);budget={"requests":0,"bytes":0};acquisitions=[]
    cutoff_dt=datetime.fromisoformat(cutoff.replace("Z","+00:00"))
    for item in packages:
        if not item.get("checksum"):return {"status":"BLOCK","blocker":"cargo_lock_checksum_missing","packages":packages,"acquisitions":acquisitions}
        meta_path=vendor_root.parent/f"{item['name']}-{item['version']}.metadata.json"
        metadata=authorized_fetch(url=f"https://crates.io/api/v1/crates/{item['name']}/{item['version']}",destination=meta_path,phase_id=phase_id,policy=policy,ledger_path=ledger_path,budget_state=budget)
        if metadata["status"]!="PASS":return {"status":"BLOCK","blocker":metadata.get("blocker"),"packages":packages,"acquisitions":acquisitions}
        value=json.loads(meta_path.read_text(encoding="utf-8"));version_record=value["version"];published=datetime.fromisoformat(version_record["created_at"].replace("Z","+00:00"))
        if published>cutoff_dt:return {"status":"BLOCK","blocker":"cargo_crate_post_cutoff","package":item}
        if version_record.get("yanked"):return {"status":"BLOCK","blocker":"cargo_crate_yanked","package":item}
        crate=vendor_root.parent/f"{item['name']}-{item['version']}.crate"
        fetched=authorized_fetch(url=f"https://static.crates.io/crates/{item['name']}/{item['name']}-{item['version']}.crate",destination=crate,phase_id=phase_id,policy=policy,ledger_path=ledger_path,expected_sha256=item["checksum"],budget_state=budget)
        if fetched["status"]!="PASS":return {"status":"BLOCK","blocker":fetched.get("blocker"),"packages":packages,"acquisitions":acquisitions}
        extracted=safe_extract_crate(crate,vendor_root/f"{item['name']}-{item['version']}",package=item["name"],version=item["version"],checksum=item["checksum"])
        acquisitions.append({**item,"publication_timestamp":version_record["created_at"],"yanked":False,"crate_sha256":fetched["sha256"],"vendor":extracted})
        if extracted["status"]!="PASS":return {"status":"BLOCK","blocker":extracted.get("blocker"),"packages":packages,"acquisitions":acquisitions}
        meta_path.unlink(missing_ok=True);crate.unlink(missing_ok=True)
    config=vendor_root.parent/".cargo"/"config.toml";config.parent.mkdir(parents=True,exist_ok=True);config.write_text('[source.crates-io]\nreplace-with = "vendored-sources"\n\n[source.vendored-sources]\ndirectory = "'+vendor_root.as_posix()+'"\n',encoding="utf-8",newline="\n")
    manifest=[{"path":p.relative_to(vendor_root).as_posix(),"sha256":hashlib.sha256(p.read_bytes()).hexdigest(),"size":p.stat().st_size} for p in sorted(vendor_root.rglob("*")) if p.is_file()]
    return {"status":"PASS","packages":packages,"acquisitions":acquisitions,"vendor_root":str(vendor_root),"config_path":str(config),"vendor_file_count":len(manifest),"vendor_manifest":manifest,"vendor_hash":hashlib.sha256(json.dumps(manifest,sort_keys=True).encode()).hexdigest(),"request_count":budget["requests"],"download_bytes":budget["bytes"]}
