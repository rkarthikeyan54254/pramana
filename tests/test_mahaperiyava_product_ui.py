from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1];UI=ROOT/'apps'/'mahaperiyava-mobile-web'
def test_assets_and_local_only():
 for n in ('index.html','styles.css','app.js','manifest.webmanifest'): assert (UI/n).exists(),n
 html=(UI/'index.html').read_text(encoding='utf-8');js=(UI/'app.js').read_text(encoding='utf-8')
 assert '/v1/mahaperiyava/answer' in js
 assert 'http://' not in html and 'https://' not in html and 'http://' not in js and 'https://' not in js
 assert 'speechSynthesis' not in js
def test_voice_never_auto_submits():
 js=(UI/'app.js').read_text(encoding='utf-8')
 assert 'SpeechRecognition' in js and 'recognition.onresult' in js and 'questionInput.value' in js
 assert "askForm.addEventListener('submit'" in js
 assert 'requestSubmit' not in js and 'Voice input only edits the transcript' in js
def test_ui_evidence_and_views():
 html=(UI/'index.html').read_text(encoding='utf-8');js=(UI/'app.js').read_text(encoding='utf-8')
 for v in ('homeView','askView','exploreView','savedView'): assert v in html
 assert '<details class="evidence-card">' in html
 assert 'support_id' in js and 'evidence_status' in js and 'localStorage' in js
def test_manifest():
 m=json.loads((UI/'manifest.webmanifest').read_text(encoding='utf-8'));assert m['start_url']=='/mahaperiyava' and m['display']=='standalone'
def test_no_restricted_markers():
 blob='\n'.join((UI/n).read_text(encoding='utf-8') for n in ('index.html','styles.css','app.js','manifest.webmanifest'))
 for token in ('exact_text_restricted','private_curation_blocks:','private_curation_paragraphs:'): assert token not in blob
