"""Read-only evidence/hash and heuristic secret checks; prints paths, never matches."""
import hashlib,json,pathlib,re,subprocess
ROOT=pathlib.Path(__file__).resolve().parents[1]
PATTERNS=[r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----',r'gh[pousr]_[A-Za-z0-9]{20,}',r'github_pat_[A-Za-z0-9_]{20,}',r'AKIA[A-Z0-9]{16}',r'''(?i)(?:api[_-]?key|token|password|secret)\s*[:=]\s*["'][a-zA-Z0-9_/-]{20,}["']''']
def main():
    findings=[];count=0
    for manifest in ['probes.json','software_sources.json']:
        for row in json.loads((ROOT/'data/evidence'/manifest).read_text()):
            p=ROOT/row['evidence'];count+=1
            if hashlib.sha256(p.read_bytes()).hexdigest()!=row['sha256']: findings.append({'file':str(p.relative_to(ROOT)),'kind':'hash_mismatch'})
    raw=subprocess.check_output(['git','ls-files','--cached','--others','--exclude-standard','-z'],cwd=ROOT)
    files=sorted(set(x for x in raw.decode().split('\0') if x))
    for name in files:
        p=ROOT/name
        if p.is_symlink(): findings.append({'file':name,'kind':'symlink_requires_review'});continue
        if not p.exists(): findings.append({'file':name,'kind':'missing_tracked_file'});continue
        body=p.read_text(errors='replace')
        if any(re.search(pattern,body) for pattern in PATTERNS): findings.append({'file':name,'kind':'possible_secret'})
    print(json.dumps({'historical_hashes_checked':count,'files_scanned':len(files),'findings':findings,'limit':'Heuristic scan plus manual review, not a proof of absence.'},ensure_ascii=False,indent=2))
    return bool(findings)
if __name__=='__main__': raise SystemExit(main())
