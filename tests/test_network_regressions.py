"""Regression tests for real-source defects; fixture strings are not corpus evidence."""
import hashlib,json,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'scripts'))
from ingest_devi_mahatmya import parse as parse_devi
from verify_devi_mahatmya_secondary import load_primary,parse_secondary_html,align
from ingest_tevaram import parse as parse_tevaram
from ingest_mahabharata_ce import parse_file
from fetch_sources import fetch
from ingest_project_madurai import extract_occurrences
from product.common import evidence_index
from product.verify_claim import run as verify

class RealSourceRegressions(unittest.TestCase):
 def test_full_verse_not_matching_suffix(self):
  raw=''.join(f'<p>first line /<br>last line // MarkP_{ch}.1 //</p>' for ch in range(81,94))
  rows=parse_devi(raw);self.assertEqual(rows[0][2],'first line / last line')
  sec=parse_secondary_html('<p>different first |\nlast line || 1.1||</p>')
  p=[{'id':'fixture','chapter':81,'verse':1,'norm':'first line last line'}]
  self.assertEqual(align(p,sec)[0]['status'],'needs_review')
 def test_inherited_fuzzy_fixture_is_rejected(self):
  p=load_primary(ROOT/'tests/devi_primary_fixture.jsonl')
  s=parse_secondary_html((ROOT/'tests/devi_secondary_fixture.html').read_text())
  r=align(p,s);self.assertEqual([x['status'] for x in r],['match','needs_review'])
  self.assertEqual(r[0]['secondary_locus'],'2.2')
 def test_heading_local_locus_and_legacy_html(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/'source.html'
   p.write_text('<h3>2.6 திருவையாறு</h3><table><tr><td>55<td>தமிழ் உரை<td>01</tr></tr><td>56<td>அடுத்த உரை<td>02</tr></table>பண்: வெளியுரை')
   r=parse_tevaram(p,2);self.assertEqual([(x['patikam'],x['verse']) for x in r],[(6,1),(6,2)])
   self.assertNotIn('வெளியுரை',r[-1]['text'])
   p.write_text(p.read_text().replace('>02<','>01<'))
   with self.assertRaisesRegex(ValueError,'duplicate'):parse_tevaram(p,2)
 def test_prose_markers_and_duplicate_pada(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/'MBh01.txt';p.write_text('01003001  sūta uvāca\n01003001A rāmaḥ\n01003001B hariḥ\n')
   rows=parse_file(p,'fixture');self.assertEqual(len(rows),1);self.assertEqual(rows[0]['text_iast'],'rāmaḥ / hariḥ');self.assertFalse(rows[0]['verified'])
   p.write_text(p.read_text()+'01003001A rāmaḥ\n')
   with self.assertRaisesRegex(ValueError,'duplicate pada'):parse_file(p,'fixture')
 def test_numbered_headings_not_verses(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/'dp.html';p.write_text('<p>1. Contents</p><pre>1. தமிழ்<br>உரை<br>2. ஆண்டாள் (474-503)<br>474 பாடல்</pre>')
   self.assertEqual(extract_occurrences(p,1,1),[(1,'தமிழ் உரை')])
 def test_skip_does_not_bless_tampering(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/'raw';p.write_bytes(b'original');h=hashlib.sha256(p.read_bytes()).hexdigest()
   p.with_suffix('.sha256').write_text(h);p.with_suffix('.meta.json').write_text(json.dumps({'sha256':h,'url':'https://example.org/source'}))
   p.write_bytes(b'changed')
   with self.assertRaisesRegex(ValueError,'checksum mismatch'):fetch({'key':'fixture','path':str(p),'url':'https://example.org/source'})
 def test_revoked_records_never_authenticate(self):
  ids={'purana.devi_mahatmya.82.2','purana.devi_mahatmya.82.13','purana.devi_mahatmya.92.3'}
  self.assertFalse(ids.intersection(evidence_index()))
  self.assertFalse(verify('अष्टम्यां च चतुर्दश्यां नवम्यां')['verified'])
if __name__=='__main__':unittest.main()
