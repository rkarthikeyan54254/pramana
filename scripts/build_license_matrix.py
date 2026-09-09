#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,re
from pathlib import Path


def classify(s):
    key=s['key']; status=s.get('status',''); terms=s.get('terms','')
    low=(status+' '+terms).lower()
    if key.startswith('pm-'):
        return {
            'classification':'conditional_redistribution',
            'redistribution':'conditional',
            'allowed_profiles':[],
            'requirements':['preserve Project Madurai header/source terms','legal/curatorial review before row-level dataset redistribution'],
            'reason':'Project Madurai permits redistribution with source-header conditions; extracted row datasets need an explicit packaging policy before release.'
        }
    if key in {'gretil-markandeya-1-93','gretil-bhagavata-1-12'} or 'creative commons attribution-noncommercial-sharealike 4.0' in low:
        return {
            'classification':'CC-BY-NC-SA-4.0',
            'redistribution':'noncommercial_sharealike',
            'allowed_profiles':['research-nc'],
            'requirements':['attribution','non-commercial use','share alike','preserve source provenance'],
            'reason':'Exact source file has pinned CC BY-NC-SA 4.0 terms.'
        }
    if 'verification-only' in low or 'verification/reference only' in low or 'all rights reserved' in low or 'do not redistribute' in low:
        return {
            'classification':'verification_only_or_restricted',
            'redistribution':'no_source_text_release',
            'allowed_profiles':[],
            'requirements':['retain only verification metadata/locus mappings unless permission is obtained'],
            'reason':'Source is used as a witness/reference; its text is not authorized for dataset redistribution under current policy.'
        }
    if 'metadata' in status:
        return {
            'classification':'metadata_only',
            'redistribution':'metadata_only',
            'allowed_profiles':[],
            'requirements':['do not infer e-text reuse rights from institutional metadata'],
            'reason':'Metadata/discovery source, not a text-release source.'
        }
    if 'needs-terms' in status or 'file-terms-required' in status or 'terms' in low and ('pin' in low or 'required' in low):
        return {
            'classification':'terms_unresolved',
            'redistribution':'blocked_pending_terms',
            'allowed_profiles':[],
            'requirements':['pin exact file-level reuse terms before redistribution'],
            'reason':'Reuse/publication terms are not sufficiently pinned.'
        }
    if 'parent-file' in status or '(c) bhandarkar' in low:
        return {
            'classification':'copyright_or_terms_unresolved',
            'redistribution':'blocked_pending_permission_or_terms',
            'allowed_profiles':[],
            'requirements':['do not redistribute source text until rights are resolved'],
            'reason':'Electronic critical-edition source is not assumed redistributable.'
        }
    return {
        'classification':'unresolved',
        'redistribution':'blocked',
        'allowed_profiles':[],
        'requirements':['manual rights review'],
        'reason':'No sufficiently explicit file-level redistribution policy is recorded.'
    }


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--manifest',default='sources/manifest.json'); ap.add_argument('--output',default='sources/LICENSE_MATRIX.json'); args=ap.parse_args()
    m=json.loads(Path(args.manifest).read_text(encoding='utf-8'))
    rows=[]
    for s in m['sources']:
        c=classify(s)
        rows.append({
            'key':s['key'],'url':s.get('url'),'path':s.get('path'),'covers':s.get('covers'),
            'source_status':s.get('status'),'recorded_terms':s.get('terms'),**c
        })
    out={'version':'1.0','policy':{
        'open':'Only source text with licenses allowing redistribution without a non-commercial restriction; verification metadata may cite restricted witnesses but may not reproduce their protected text.',
        'research-nc':'Allows source rows under licenses such as CC BY-NC-SA 4.0, preserving attribution/share-alike/non-commercial conditions.',
        'blocked_default':'Unknown, copyrighted, verification-only, reference-only, and conditional-header sources are excluded unless a source-specific release policy explicitly admits them.'
    },'sources':rows}
    Path(args.output).write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    from collections import Counter
    print('license-matrix',len(rows),'sources',dict(Counter(r['classification'] for r in rows)))
if __name__=='__main__': main()
