#!/usr/bin/env python3
import argparse, json, pathlib, re
ROOT=pathlib.Path(__file__).resolve().parents[1]
PAT=re.compile(r'^MBh_(\d{2})\.(\d{3})(?:\.(\d{3}))?$')

def parse_locus(s):
    m=PAT.match(s or '')
    if not m: raise ValueError(f'unsupported Mahabharata locus: {s}')
    p,c,v=m.groups(); return int(p),int(c),(int(v) if v is not None else None)

def rec_pcv(r):
    sec=r.get('section') or {}
    p=sec.get('parva'); c=sec.get('chapter'); v=r.get('unit_no')
    if p is None or c is None or v is None: raise ValueError(f"record lacks parva/chapter/verse: {r.get('id')}")
    return int(p),int(c),int(v)

def in_range(rec, lo, hi):
    p,c,v=rec; lp,lc,lv=lo; hp,hc,hv=hi
    if p < lp or p > hp: return False
    if p==lp and c < lc: return False
    if p==hp and c > hc: return False
    if lv is not None and (p,c)==(lp,lc) and v < lv: return False
    if hv is not None and (p,c)==(hp,hc) and v > hv: return False
    return True

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('parent_jsonl'); ap.add_argument('--outdir',required=True)
    args=ap.parse_args()
    episodes=json.loads((ROOT/'schema/episode_catalog.json').read_text())['episodes']
    targets=[e for e in episodes if e['parent_work']=='mahabharata_critical_edition' and e['status']!='needs_locus_verification']
    rows=[]
    for ln,line in enumerate(pathlib.Path(args.parent_jsonl).read_text().splitlines(),1):
        if not line.strip(): continue
        r=json.loads(line); rec_pcv(r); rows.append(r)
    outdir=pathlib.Path(args.outdir); outdir.mkdir(parents=True,exist_ok=True)
    summary=[]
    for e in targets:
        lo=parse_locus(e['start_locus']); hi=parse_locus(e['end_locus'])
        if lo[0]!=hi[0]: raise ValueError(f"cross-parva slice unsupported: {e['key']}")
        chosen=[r for r in rows if in_range(rec_pcv(r),lo,hi)]
        if not chosen: raise SystemExit(f"FAIL {e['key']}: no rows in {e['start_locus']}..{e['end_locus']}")
        pcs={(rec_pcv(r)[0],rec_pcv(r)[1]) for r in chosen}
        expected={(lo[0],c) for c in range(lo[1],hi[1]+1)}
        missing=sorted(expected-pcs)
        if missing: raise SystemExit(f"FAIL {e['key']}: missing chapters {missing}")
        # exact endpoint integrity
        first,last=rec_pcv(chosen[0]),rec_pcv(chosen[-1])
        if lo[2] is not None and first != lo: raise SystemExit(f"FAIL {e['key']}: exact start missing; got {first}, expected {lo}")
        if hi[2] is not None and last != hi: raise SystemExit(f"FAIL {e['key']}: exact end missing; got {last}, expected {hi}")
        path=outdir/(e['key']+'.jsonl')
        path.write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in chosen))
        summary.append((e['key'],len(chosen),len(expected)))
    for k,n,c in summary: print(f'{k}: {n} rows across {c} chapters')
    print(f'materialized {len(summary)} Mahabharata slices')
if __name__=='__main__': main()
