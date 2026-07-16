from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import urllib.request
import zlib


ARCHIVE_URL = "https://zenodo.org/api/records/21383214/files/reactome-download-directory.zip/content"
RECORD_URL = "https://zenodo.org/api/records/21383214"
ARCHIVE_IDENTITY = {"size": 4732163201, "md5": "78fb7ed15e4df2246a8c95e5c827a90b", "record_id": 21383214, "doi": "10.5281/zenodo.21383214", "release": 97}
MEMBERS = {
    "gk_current.sql.gz": (2391696494, 2510111488, 120801967, "72db64e7", "f3b9c114b5da076cf46e592a3968b76969fd8c5ba78768ad3c494df10f79d9ce", "97/databases/gk_current.sql.gz"),
    "ReactomePathways.txt": (2960785268, 2961177724, 1592393, "8f4c6d3f", "f6d7a2bf89b5bcfe0250a0bc7f51bff94641447911712b8ff129f5b55e52df3a", "97/ReactomePathways.txt"),
    "ReactomePathwaysRelation.txt": (2781723454, 2781847134, 634259, "ebc3d805", "fd49a624d80c14eb37ae57a02e141d574d5ede3f60022bb99edbd909448a3f1e", "97/ReactomePathwaysRelation.txt"),
    "ReactionPMIDS.txt": (2944772874, 2945052954, 1131516, "586349f0", "71400e709ab5a53810ef585d98056f34c9afd0b11fa8dc5737ade3935f559a07", "97/ReactionPMIDS.txt"),
    "disease_variant_ewas_mapping.tsv": (908350015, 908699645, 5547172, "f257bc70", "51e2e018bf76ad32e06a1c63b4510b4435490bbee457667e83acd6610664f41a", "97/disease_variant_ewas_mapping.tsv"),
    "reactome_stable_ids.txt": (4703771966, 4705926513, 7757966, "2b267c63", "4e53af58d7feb050333164c0323c1de5f36ab62b7fce3178bcb93d03c1a7b769", "97/reactome_stable_ids.txt"),
    "reactome_reaction_exporter.txt": (3580267415, 3581262331, 13388144, "665a34c8", "4cb0bb201809920a2400d28a8060f224465b5e4775a763da6c292a5474ee3e26", "97/reactome_reaction_exporter.txt"),
}


def _request(url: str, *, byte_range: tuple[int, int] | None = None):
    headers = {"User-Agent": "ControllerGate/0.2 structured-source-custody"}
    if byte_range:
        headers["Range"] = f"bytes={byte_range[0]}-{byte_range[1]}"
    return urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=900)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", required=True)
    args = parser.parse_args()
    root = pathlib.Path(args.output_root); root.mkdir(parents=True, exist_ok=True)
    with _request(RECORD_URL) as response:
        record_bytes = response.read()
    record = json.loads(record_bytes)
    remote_file = record["files"][0]
    if record["id"] != 21383214 or record["metadata"]["version"] != "v97" or remote_file["size"] != ARCHIVE_IDENTITY["size"] or remote_file["checksum"] != f"md5:{ARCHIVE_IDENTITY['md5']}":
        raise ValueError("Reactome release-97 Zenodo record identity changed")
    rows=[]
    for filename,(start,end,size,crc_expected,sha_expected,member_name) in MEMBERS.items():
        target=root/filename; digest=hashlib.sha256(); crc=0; total=0; decompressor=zlib.decompressobj(-15)
        with _request(ARCHIVE_URL,byte_range=(start,end)) as response, target.open("wb") as stream:
            while True:
                compressed=response.read(1024*1024)
                if not compressed: break
                plain=decompressor.decompress(compressed)
                if plain:
                    stream.write(plain);digest.update(plain);crc=zlib.crc32(plain,crc);total+=len(plain)
            plain=decompressor.flush()
            if plain:
                stream.write(plain);digest.update(plain);crc=zlib.crc32(plain,crc);total+=len(plain)
        observed_sha=digest.hexdigest();observed_crc=f"{crc&0xffffffff:08x}"
        if total != size or observed_crc != crc_expected or observed_sha != sha_expected:
            raise ValueError(f"structured source member mismatch: {filename}")
        rows.append({"name":member_name,"path":str(target.resolve()),"size":total,"sha256":observed_sha,"crc32":observed_crc,"outer_archive_data_range":[start,end],**ARCHIVE_IDENTITY})
    manifest=root/"reactome-release97-structured-source-manifest.json"
    manifest.write_text(json.dumps(rows,indent=2,sort_keys=True)+"\n",encoding="utf-8",newline="\n")
    custody={"status":"PASS","producer":"scripts/acquire_reactome97_structured.py","execution_depth":"official_Zenodo_record_and_verified_member_ranges","semantic_scope":"Reactome release 97 structured source custody","record_metadata_sha256":hashlib.sha256(record_bytes).hexdigest(),"archive_identity":ARCHIVE_IDENTITY,"member_count":len(rows),"members":rows,"raw_sources_outside_git":True,"authority_allowed":"RPIR v2 parsing","authority_forbidden":["software causal authority","repair authorization"]}
    (root/"reactome-release97-acquisition-custody.json").write_text(json.dumps(custody,indent=2,sort_keys=True)+"\n",encoding="utf-8",newline="\n")
    print(json.dumps(custody,sort_keys=True))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
