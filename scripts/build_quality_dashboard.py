#!/usr/bin/env python3
from __future__ import annotations
import json,glob,subprocess,sys,html
from collections import Counter,defaultdict
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def load_rows():
    rows=[]
    for p in glob.glob(str(ROOT/'data/public/**/*.jsonl'),recursive=True):
        for line in open(p,encoding='utf-8'):
            if line.strip(): rows.append(json.loads(line))
    return rows

def main():
    rows=load_rows(); verified=[r for r in rows if r.get('verified') and r.get('verification_source')]
    graph_raw=json.loads((ROOT/'data/public/graph/global_evidence_graph.json').read_text(encoding='utf-8')); g=graph_raw.get('graph',graph_raw)
    bench=json.loads((ROOT/'benchmark/native_baseline.json').read_text(encoding='utf-8'))
    catalog=json.loads((ROOT/'schema/work_catalog.json').read_text(encoding='utf-8'))
    planned_tamil=catalog['divya_prabandham']['expected_total']+sum(x['expected_units'] for x in catalog['tevaram']['tirumurai'])
    by_work=Counter(r.get('work','unknown') for r in rows); verified_by_work=Counter(r.get('work','unknown') for r in verified)
    licenses=Counter(r.get('source_license','UNKNOWN') for r in verified)
    node_kinds=Counter(n['kind'] for n in g['nodes']); edge_kinds=Counter(e['kind'] for e in g['edges'])
    data={
      'summary':{
        'repository_rows':len(rows),'verified_rows':len(verified),'verification_rate_pct':round(100*len(verified)/len(rows),1) if rows else 0,
        'graph_nodes':len(g['nodes']),'graph_edges':len(g['edges']),
        'planned_mapped_tamil_units':planned_tamil,'materialized_vs_planned_tamil_pct':round(100*len(rows)/planned_tamil,2) if planned_tamil else 0,
        'benchmark_cases':bench.get('cases_total'),'benchmark_cases_passed':bench.get('cases_passed'),'benchmark_checks':bench.get('checks_total'),'benchmark_checks_passed':bench.get('checks_passed'),'benchmark_score':bench.get('score')
      },
      'works':[{ 'work':w,'rows':by_work[w],'verified':verified_by_work[w],'pct':round(100*verified_by_work[w]/by_work[w],1) if by_work[w] else 0} for w in sorted(by_work)],
      'licenses':dict(sorted(licenses.items())), 'node_kinds':dict(sorted(node_kinds.items())), 'edge_kinds':dict(sorted(edge_kinds.items())),
      'moat':{'authority':'verified corpus evidence only','unverified_as_authority':'forbidden','silent_harmonization':False,'generated_graph_facts_without_evidence':'forbidden'}
    }
    outdir=ROOT/'dist/dashboard'; outdir.mkdir(parents=True,exist_ok=True)
    (outdir/'quality.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
    s=data['summary']
    rows_html=''.join(f"<tr><td>{html.escape(x['work'])}</td><td>{x['rows']}</td><td>{x['verified']}</td><td>{x['pct']}%</td></tr>" for x in data['works'])
    page=f'''<!doctype html><meta charset="utf-8"><title>Pramāṇa quality checkpoint</title><style>body{{font-family:system-ui;max-width:1050px;margin:40px auto;padding:0 20px}}.cards{{display:grid;grid-template-columns:repeat(4,1fr);gap:12px}}.card{{border:1px solid #ddd;border-radius:12px;padding:16px}}.n{{font-size:28px;font-weight:700}}table{{width:100%;border-collapse:collapse;margin-top:24px}}td,th{{padding:8px;border-bottom:1px solid #ddd;text-align:left}}code{{background:#eee;padding:2px 4px}}@media(max-width:700px){{.cards{{grid-template-columns:1fr 1fr}}}}</style>
<h1>Pramāṇa quality checkpoint</h1><p>Generated from the local repository. This measures corpus/graph contract health, not market superiority.</p>
<div class="cards"><div class="card"><div class="n">{s['verified_rows']}</div>verified materialized records</div><div class="card"><div class="n">{s['graph_nodes']}</div>graph nodes</div><div class="card"><div class="n">{s['graph_edges']}</div>graph edges</div><div class="card"><div class="n">{s['benchmark_score']}%</div>native moat checks</div></div><p><strong>Depth warning:</strong> only {s['materialized_vs_planned_tamil_pct']}% of the already mapped 12,240 Tamil units are materialized in this local checkpoint. The 100% verification rate applies only to the current 24 seed rows.</p>
<h2>Verification depth</h2><table><thead><tr><th>Work</th><th>Rows</th><th>Verified</th><th>Rate</th></tr></thead><tbody>{rows_html}</tbody></table>
<h2>Licensing</h2><pre>{html.escape(json.dumps(data['licenses'],indent=2))}</pre><h2>Graph coverage</h2><pre>{html.escape(json.dumps({'nodes':data['node_kinds'],'edges':data['edge_kinds']},indent=2))}</pre>
<h2>Moat policy</h2><p><code>verified evidence only</code> → graph/retrieval authority. Unverified rows and generated facts cannot become authority.</p>'''
    (outdir/'index.html').write_text(page,encoding='utf-8')
    print(json.dumps({'output':str(outdir),'summary':s},indent=2))
if __name__=='__main__': main()
