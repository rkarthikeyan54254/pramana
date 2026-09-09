#!/usr/bin/env python3
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from iast_to_devanagari import transliterate
pairs = [
    ("devāsuramabhūdyuddhaṃ pūrṇamabdaśataṃ purā / mahiṣe'surāṇāmadhipe devānāṃ ca purandare",
     "देवासुरमभूद्युद्धं पूर्णमब्दशतं पुरा । महिषेऽसुराणामधिपे देवानां च पुरन्दरे"),
    ("tatrāsurairmahāvīryairdevasainyaṃ parājitam / jitvā ca sakalān devānindro'bhūnmahiṣāsuraḥ",
     "तत्रासुरैर्महावीर्यैर्देवसैन्यं पराजितम् । जित्वा च सकलान् देवानिन्द्रोऽभून्महिषासुरः"),
]
for src, expected in pairs:
    got = transliterate(src)
    assert got == expected, (src, got, expected)
print(f'transliteration fixtures OK: {len(pairs)}')
