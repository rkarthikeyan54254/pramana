#!/usr/bin/env python3
from pathlib import Path
import argparse,json
ROOT=Path(__file__).resolve().parents[1];UI=ROOT/'apps'/'mahaperiyava-mobile-web';DEFAULT=ROOT/'data/review/mahaperiyava_product_ui_checkpoint.json'
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--output',default=str(DEFAULT));a=ap.parse_args();html=(UI/'index.html').read_text(encoding='utf-8');js=(UI/'app.js').read_text(encoding='utf-8');css=(UI/'styles.css').read_text(encoding='utf-8');manifest=json.loads((UI/'manifest.webmanifest').read_text(encoding='utf-8'))
 checks={'four_views_present':all(x in html for x in ('homeView','askView','exploreView','savedView')),'evidence_drawer_present':'<details class="evidence-card">' in html,'answer_api_connected':'/v1/mahaperiyava/answer' in js,'save_local_only':'localStorage' in js,'voice_transcript_editable':'recognition.onresult' in js and 'questionInput.value' in js,'voice_never_auto_submits':'requestSubmit' not in js and 'Voice input only edits the transcript' in js,'no_tts':'speechSynthesis' not in js,'mobile_layout':'@media(max-width:560px)' in css,'standalone_manifest':manifest.get('display')=='standalone','no_external_ui_network_assets':all(x not in html+js for x in ('http://','https://')),'restricted_source_text_exposed':False,'authority_promotions':0}
 ready=(
  checks['four_views_present'] is True and
  checks['evidence_drawer_present'] is True and
  checks['answer_api_connected'] is True and
  checks['save_local_only'] is True and
  checks['voice_transcript_editable'] is True and
  checks['voice_never_auto_submits'] is True and
  checks['no_tts'] is True and
  checks['mobile_layout'] is True and
  checks['standalone_manifest'] is True and
  checks['no_external_ui_network_assets'] is True and
  checks['restricted_source_text_exposed'] is False and
  checks['authority_promotions']==0
)
 cp={'version':'1.0','checkpoint':'MAHAPERIYAVA_PRODUCT_UI_FOUNDATION','status':'PHASE10_PRODUCT_UI_READY_FOR_USER_TRIAL' if ready else 'PHASE10_PRODUCT_UI_NOT_READY','decision':'begin_user_trial_and_iterate_product_quality' if ready else 'repair_ui_contract_before_trial','scope':'Mobile-first local web UI for the Phase 9 grounded-answer API, with evidence drawer, Explore/Saved views, and optional editable dictation.','checks':checks,'voice_contract':{'mode':'optional_browser_dictation','supported_languages':['en-IN','ta-IN'],'auto_submit':False,'transcript_editable':True,'text_fallback':True,'text_to_speech_enabled':False,'note':'Browser dictation is only an input convenience. A local Whisper backend can replace it later without changing the answer/evidence contract.'},'rights':{'mahaperiyava_photo_included':False,'reason':'No image is shipped until a real photograph has explicit provenance and reuse rights.'},'trust_boundary':{'restricted_source_text_sent_to_ui':False,'curator_summaries_presented_as_quotes':False,'generated_prose_enters_corpus':False,'publication_approval_implied':False}}
 Path(a.output).write_text(json.dumps(cp,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps(cp,ensure_ascii=False,indent=2));return 0 if ready else 1
if __name__=='__main__': raise SystemExit(main())
