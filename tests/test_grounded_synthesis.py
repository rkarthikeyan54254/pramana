#!/usr/bin/env python3
import json,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'rag'))
from grounded_synthesis import assemble
rows=[
 {'id':'purana.devi_mahatmya.c82.v12','corpus':'purana','work':'devi_mahatmya','tradition':'shakta','author':'unknown','language':'sanskrit','section':{'chapter':82},'unit_no':12,'text_original':'अतुलं तत्र तत्तेजः सर्वदेवशरीरजम् । एकस्थं तदभून्नारी व्याप्तलोकत्रयं त्विषा ॥','text_iast':'atulaṃ tatra tattejaḥ sarvadevaśarīrajam / ekasthaṃ tadabhūnnārī vyāptalokatrayaṃ tviṣā','source':'gretil','source_license':'CC BY-NC-SA 4.0','verified':True,'verification_source':'vedpath','flags':[]},
 {'id':'purana.devi_mahatmya.c82.v99','corpus':'purana','work':'devi_mahatmya','tradition':'shakta','author':'unknown','language':'sanskrit','section':{'chapter':82},'unit_no':99,'text_original':'कल्पितम्','text_iast':'kalpitam','source':'x','source_license':'PD','verified':False,'flags':[]}
]
claims=[
 {'text':'The text describes the combined divine radiance becoming a woman who pervades the three worlds.','support_ids':['purana.devi_mahatmya.c82.v12']},
 {'text':'Quoted evidence','quote':'एकस्थं तदभून्नारी','support_ids':['purana.devi_mahatmya.c82.v12']},
 {'text':'Bad unverified support','support_ids':['purana.devi_mahatmya.c82.v99']},
 {'text':'No support'},
 {'text':'Invented quote','quote':'यह वाक्य ग्रन्थे नास्ति','support_ids':['purana.devi_mahatmya.c82.v12']}
]
out=assemble(rows,claims)
assert len(out['claims'])==2,out
assert len(out['rejected_claims'])==3,out
assert {x['reason'] for x in out['rejected_claims']}=={'support_not_verified_or_missing','missing_support_ids','quote_not_extractable_from_support'}
assert len(out['evidence'])==1
print('grounded synthesis tests: GREEN')
