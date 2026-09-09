#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, sqlite3
from pathlib import Path

SCHEMA='''
PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS records(
 id TEXT PRIMARY KEY, corpus TEXT, work TEXT, unit_no TEXT, text_original TEXT,
 text_iast TEXT, source TEXT, verification_source TEXT, verified INTEGER NOT NULL,
 source_license TEXT, payload TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS nodes(
 id TEXT PRIMARY KEY, kind TEXT NOT NULL, label TEXT NOT NULL, derivation TEXT NOT NULL,
 reviewed_by TEXT, payload TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS edges(
 id TEXT PRIMARY KEY, kind TEXT NOT NULL, subject TEXT NOT NULL, predicate TEXT NOT NULL,
 object TEXT NOT NULL, derivation TEXT NOT NULL, status TEXT NOT NULL, reviewed_by TEXT,
 payload TEXT NOT NULL,
 FOREIGN KEY(subject) REFERENCES nodes(id), FOREIGN KEY(object) REFERENCES nodes(id)
);
CREATE TABLE IF NOT EXISTS node_evidence(node_id TEXT NOT NULL, evidence_id TEXT NOT NULL,
 PRIMARY KEY(node_id,evidence_id), FOREIGN KEY(node_id) REFERENCES nodes(id), FOREIGN KEY(evidence_id) REFERENCES records(id));
CREATE TABLE IF NOT EXISTS edge_evidence(edge_id TEXT NOT NULL, evidence_id TEXT NOT NULL,
 PRIMARY KEY(edge_id,evidence_id), FOREIGN KEY(edge_id) REFERENCES edges(id), FOREIGN KEY(evidence_id) REFERENCES records(id));
CREATE INDEX IF NOT EXISTS idx_records_work ON records(work);
CREATE INDEX IF NOT EXISTS idx_nodes_kind ON nodes(kind);
CREATE INDEX IF NOT EXISTS idx_edges_subject ON edges(subject);
CREATE INDEX IF NOT EXISTS idx_edges_object ON edges(object);
CREATE INDEX IF NOT EXISTS idx_edges_predicate ON edges(predicate);
'''

def iter_jsonl(paths):
    for p in paths:
        for line in Path(p).read_text(encoding='utf-8').splitlines():
            if line.strip(): yield json.loads(line)

def discover_rows(root: Path):
    return sorted(root.glob('data/public/**/*.jsonl'))

def build(root: Path, db: Path, graph_path: Path):
    if db.exists(): db.unlink()
    con=sqlite3.connect(db); con.executescript(SCHEMA)
    rows=list(iter_jsonl(discover_rows(root)))
    verified={r['id']:r for r in rows if r.get('verified') and r.get('verification_source')}
    for r in verified.values():
        con.execute('INSERT INTO records VALUES(?,?,?,?,?,?,?,?,?,?,?)',(
            r['id'],r.get('corpus'),r.get('work'),str(r.get('unit_no','')),r.get('text_original'),r.get('text_iast'),
            r.get('source'),r.get('verification_source'),1,r.get('source_license'),json.dumps(r,ensure_ascii=False)))
    raw=json.loads(graph_path.read_text(encoding='utf-8')); g=raw.get('graph',raw)
    for n in g['nodes']:
        missing=[e for e in n.get('evidence_ids',[]) if e not in verified]
        if missing: raise ValueError(f"node {n['id']} missing verified evidence: {missing}")
        con.execute('INSERT INTO nodes VALUES(?,?,?,?,?,?)',(n['id'],n['kind'],n['label'],n['derivation'],n.get('reviewed_by'),json.dumps(n,ensure_ascii=False)))
    for e in g['edges']:
        missing=[x for x in e.get('evidence_ids',[]) if x not in verified]
        if missing: raise ValueError(f"edge {e['id']} missing verified evidence: {missing}")
        con.execute('INSERT INTO edges VALUES(?,?,?,?,?,?,?,?,?)',(e['id'],e['kind'],e['subject'],e['predicate'],e['object'],e['derivation'],e['status'],e.get('reviewed_by'),json.dumps(e,ensure_ascii=False)))
    for n in g['nodes']:
        for ev in n['evidence_ids']: con.execute('INSERT INTO node_evidence VALUES(?,?)',(n['id'],ev))
    for e in g['edges']:
        for ev in e['evidence_ids']: con.execute('INSERT INTO edge_evidence VALUES(?,?)',(e['id'],ev))
    con.commit(); counts={t:con.execute(f'SELECT COUNT(*) FROM {t}').fetchone()[0] for t in ['records','nodes','edges','node_evidence','edge_evidence']}; con.close(); return counts

def query_node(db:Path,node_id:str,depth:int=1):
    con=sqlite3.connect(db); con.row_factory=sqlite3.Row
    seen={node_id}; frontier={node_id}; edges=[]
    for _ in range(depth):
        if not frontier: break
        marks=','.join('?'*len(frontier)); params=list(frontier)*2
        got=con.execute(f'SELECT payload FROM edges WHERE subject IN ({marks}) OR object IN ({marks})',params).fetchall()
        nxt=set()
        for row in got:
            e=json.loads(row['payload'])
            if e['id'] not in {x['id'] for x in edges}: edges.append(e)
            for nid in (e['subject'],e['object']):
                if nid not in seen: nxt.add(nid); seen.add(nid)
        frontier=nxt
    nodes=[]
    for nid in seen:
        r=con.execute('SELECT payload FROM nodes WHERE id=?',(nid,)).fetchone()
        if r: nodes.append(json.loads(r['payload']))
    ev_ids=sorted({x for e in edges for x in e.get('evidence_ids',[])} | {x for n in nodes for x in n.get('evidence_ids',[])})
    evidence=[]
    for x in ev_ids:
        r=con.execute('SELECT payload FROM records WHERE id=?',(x,)).fetchone()
        if r: evidence.append(json.loads(r['payload']))
    con.close(); return {'root':node_id,'depth':depth,'nodes':nodes,'edges':edges,'evidence':evidence}

def main():
    ap=argparse.ArgumentParser(); sub=ap.add_subparsers(dest='cmd',required=True)
    b=sub.add_parser('build'); b.add_argument('--db',default='dist/pramana.sqlite'); b.add_argument('--graph',default='data/public/graph/global_evidence_graph.json')
    q=sub.add_parser('query'); q.add_argument('--db',default='dist/pramana.sqlite'); q.add_argument('node'); q.add_argument('--depth',type=int,default=1)
    a=ap.parse_args(); root=Path(__file__).resolve().parents[1]
    if a.cmd=='build':
        db=root/a.db; db.parent.mkdir(parents=True,exist_ok=True); print(json.dumps(build(root,db,root/a.graph),indent=2))
    else: print(json.dumps(query_node(root/a.db,a.node,a.depth),ensure_ascii=False,indent=2))
if __name__=='__main__': main()
