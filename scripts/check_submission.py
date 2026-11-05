"""Check classroom submission deliverables, exports and source manifests."""
import csv
import hashlib
import json
import re
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]


def main():
    docs=ROOT/'docs'
    required=['LICENSE','README.md','docs/业务挖掘.md','docs/访谈记录.md','docs/访谈记录.json',
              'docs/访谈记录.csv','docs/现场调研分析.md','docs/diagrams/as-is-no-ai.svg',
              'docs/diagrams/as-is-no-ai.png','docs/diagrams/as-is-no-ai.html','src/engine.py']
    for name in required:
        assert (ROOT/name).is_file() and (ROOT/name).stat().st_size>0,name
    license_text=(ROOT/'LICENSE').read_text(encoding='utf8')
    assert 'MIT License' in license_text and 'Permission is hereby granted' in license_text
    records=json.loads((docs/'访谈记录.json').read_text(encoding='utf8'))['records']
    with (docs/'访谈记录.csv').open(encoding='utf-8-sig',newline='') as f:rows=list(csv.DictReader(f))
    assert len(records)==len(rows)==45
    for j,c in zip(records,rows):
        assert j['id']==c['id'] and j['question']==c['question'] and j['answer']==c['answer']
    assert len(re.findall(r'^## INT-\d+', (docs/'访谈记录.md').read_text(encoding='utf8'),re.M))==45
    manifest=json.loads((docs/'original-materials/manifest.json').read_text(encoding='utf8'))
    assert len(manifest['documents'])==4
    for d in manifest['documents']:
        assert hashlib.sha256((docs/'original-materials'/d['file']).read_bytes()).hexdigest()==d['sha256']
    assert hashlib.sha256((docs/'evidence/original-materials-source.json').read_bytes()).hexdigest()==manifest['sourceSHA256']
    tree=ET.parse(docs/'diagrams/as-is-no-ai.svg');ns={'s':'http://www.w3.org/2000/svg'}
    assert len(tree.findall('.//s:g[@class="decision"]',ns))==6
    assert tree.getroot().attrib['viewBox']=='0 0 2080 1580'
    links=[]
    for p in ROOT.rglob('*.md'):
        if '.git' in p.parts:continue
        for link in re.findall(r'\]\(([^)]+)\)',p.read_text(encoding='utf8')):
            if '://' not in link and not link.startswith('#'):
                assert (p.parent/link.split('#')[0]).exists(),(str(p),link)
                links.append(link)
    print(f'PASS: MIT + required files; 45 matching MD/JSON/CSV interviews; 4 source-verified materials; 6 decisions; {len(links)} local links')


if __name__=='__main__':main()
