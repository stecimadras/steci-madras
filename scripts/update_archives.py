"""Generate archive links from PDF files under archives/; no manual HTML editing."""
from pathlib import Path
import json, re, html
from urllib.parse import quote

ROOT=Path(__file__).resolve().parent.parent
MONTHS=['January','February','March','April','May','June','July','August','September','October','November','December']
def make_label(path):
    stem=path.stem
    words=re.sub(r'(?i)\b(?:bulletin|newsletter|steci|madras|parish)\b',' ',stem)
    words=re.sub(r'[_\-.]+',' ',words)
    match=re.search(r'(?i)(jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)\s*(?:to|and|&)??\s*(jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)?',words)
    year_match=re.search(r'20\d{2}',words)
    year=year_match.group(0) if year_match else path.parent.name
    if match:
        def month(s):return next((m for m in MONTHS if m.lower().startswith(s.lower()[:3])),s.title())
        label=month(match.group(1))
        if match.group(2):label+=' – '+month(match.group(2))
        return f'{label} {year}'
    cleaned=re.sub(r'\s+',' ',words).strip()
    return (cleaned.title()+' ' if cleaned else 'Bulletin ')+str(year)

def run():
    archive_root=ROOT/'archives'
    paths=sorted(archive_root.rglob('*.pdf')) if archive_root.exists() else []
    records=[]
    for path in paths:
        rel=path.relative_to(ROOT).as_posix()
        year_match=re.search(r'20\d{2}',str(path.relative_to(archive_root)))
        year=int(year_match.group()) if year_match else 0
        records.append({'year':year,'label':make_label(path),'path':'/'.join(quote(part) for part in rel.split('/'))})
    records.sort(key=lambda e:(-e['year'],e['label']))
    source=ROOT/'index.html'
    content=source.read_text(encoding='utf-8')
    a='<!-- ARCHIVE_DATA_START -->';b='<!-- ARCHIVE_DATA_END -->'
    assert content.count(a)==1 and content.count(b)==1,'Missing archive data markers in index.html'
    payload='<script>window.ARCHIVE_DATA = '+json.dumps(records,ensure_ascii=False).replace('<','\\u003c')+';</script>'
    before,rest=content.split(a,1);_,after=rest.split(b,1)
    source.write_text(before+a+'\n'+payload+'\n'+b+after,encoding='utf-8')
    (ROOT/'archives-data.json').write_text(json.dumps(records,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print(f'Indexed {len(records)} archived PDFs')
if __name__=='__main__':run()
