#!/usr/bin/env python3
import json,subprocess,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory() as td:
    td=Path(td); st=td/'staging.jsonl'; vr=td/'verify.jsonl'; cert=td/'cert.jsonl'
    s=[]; v=[]; c=[]
    for ch in range(81,94):
        rid=f'purana.devi_mahatmya.c{ch}.v1'
        base={'id':rid,'corpus':'purana','work':'devi_mahatmya','tradition':'shakta','author':'unknown','language':'sanskrit','section':{'parent_work':'markandeya_purana','chapter':ch},'unit_no':1,'text_original':'देवी','text_iast':'devī','source':'gretil','source_license':'CC BY-NC-SA 4.0','verified':False,'flags':['needs_second_source']}
        s.append(base)
        v.append({'id':rid,'primary_locus':f'MarkP_{ch}.1','secondary_locus':f'{ch-80}.2','score':1.0,'status':'match'})
        good=dict(base); good.update({'verified':True,'verification_source':'vedpath','flags':[]}); c.append(good)
    for p,rows in [(st,s),(vr,v),(cert,c)]: p.write_text('\n'.join(json.dumps(x,ensure_ascii=False) for x in rows)+'\n',encoding='utf-8')
    subprocess.run(['python3',str(ROOT/'scripts/audit_devi_certification.py'),str(st),str(vr),'--certified-jsonl',str(cert)],check=True)
print('Devi full certification audit fixture: GREEN')
