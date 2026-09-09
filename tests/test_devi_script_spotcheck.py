#!/usr/bin/env python3
import sys,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from iast_to_devanagari import transliterate

def compact(s):
    return re.sub(r'[\s।॥]+','',s)
# Ancient-text spot checks against independently displayed Devanagari witnesses.
cases=[
 ('sāvarṇiḥ sūryatanayo yo manuḥ kathyate\'ṣṭamaḥ / niśāmaya tadutpattiṃ vistarādgadato mama', 'सावर्णिः सूर्यतनयो यो मनुः कथ्यतेऽष्टमः । निशामय तदुत्पत्तिं विस्तराद्गदतो मम'),
 ('devāsuramabhūdyuddhaṃ pūrṇamabdaśataṃ purā / mahiṣe\'surāṇāmadhipe devānāṃ ca purandare', 'देवासुरमभूद्युद्धं पूर्णमब्दशतं पुरा । महिषेऽसुराणामधिपे देवानां च पुरन्दरे'),
]
for iast,dev in cases:
    got=transliterate(iast)
    assert compact(got)==compact(dev),(got,dev)
print('Devi script normalization spot checks: GREEN')
