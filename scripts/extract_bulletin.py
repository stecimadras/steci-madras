#!/usr/bin/env python3
"""Extract the parish's current *text-based, two-column-style* bulletin layout.
Fail closed if format differs; never publish fabricated or partially parsed data.
"""
import json, re, sys, calendar
from pathlib import Path
from datetime import date
import fitz
ROOT=Path(__file__).resolve().parents[1]
PDF=ROOT/'current-bulletin.pdf'
OUT=ROOT/'bulletin-data.json'
MONTHS={m.upper():i for i,m in enumerate(calendar.month_name) if m}
MONTHS.update({m[:3].upper():i for m,i in list(MONTHS.items())})
def fail(msg): raise ValueError(msg)
def clean(s): return ' '.join(s.split())
def parse():
    pdf=fitz.open(PDF)
    if not pdf or len(pdf)<2: fail('Expected a searchable parish bulletin with at least 2 pages')
    pages=[p.get_text(sort=False) for p in pdf]
    if any(len(s.strip())<100 for s in pages): fail('PDF is scanned/image-only; text extraction unavailable')
    first, second=pages[0].splitlines(),pages[1].splitlines()
    alltext='\n'.join(pages)
    m=re.search(r'PARISH BULLETIN\s*[·:-]\s*([A-Z]+)\s*[–-]\s*([A-Z]+)\s+(20\d\d)',alltext,re.I)
    if not m: fail('Cannot identify bulletin period')
    start,end,year=MONTHS.get(m[1].upper()),MONTHS.get(m[2].upper()),int(m[3]);
    if not start or not end or end<start: fail('Unsupported bulletin period')
    def datekey(d,mon):
        n=MONTHS.get(mon.upper());
        if n is None or not start<=n<=end: fail(f'Date outside bulletin: {d} {mon}')
        return f'{year}-{n:02}-{int(d):02}'
    def dated_pairs(lines,heading,stop):
        try: i=next(i for i,x in enumerate(lines) if x.strip().lower()==heading.lower())
        except StopIteration: fail(f'Missing heading: {heading}')
        sub=lines[i+1:]
        stopat=next((i for i,x in enumerate(sub) if stop(x.strip())),len(sub))
        sub=[x.strip() for x in sub[:stopat] if x.strip()]
        result={}; tba=[]; j=0
        while j<len(sub):
            mm=re.fullmatch(r'(\d{1,2})\s+([A-Za-z]{3})',sub[j])
            if mm:
                if j+1>=len(sub): fail(f'Missing entry after {sub[j]}')
                result.setdefault(datekey(*mm.groups()),[]).append(sub[j+1]); j+=2
            elif sub[j].upper()=='TBA':
                if j+1>=len(sub): fail('Missing TBA description')
                tba.append(sub[j+1]);j+=2
            else: j+=1
        return result,tba
    birthdays,_=dated_pairs(second,'Birthdays',lambda s:s.upper()=='O R D E R  O F  W O R S H I P' or 'O R D E R' in s)
    anniversaries,_=dated_pairs(first,'Wedding Anniversaries',lambda s:False)
    events,tba=dated_pairs(first,'Upcoming Events',lambda s:s.startswith('St. Thomas Evangelical'))
    try: idx=next(i for i,x in enumerate(second) if x.strip()=='Service Schedule')
    except StopIteration: fail('Missing Service Schedule')
    lines=[x.strip() for x in second[idx+1:] if x.strip()]
    services={}; j=0; active_month=None
    while j<len(lines):
        mh=re.fullmatch(r'(JANUARY|FEBRUARY|MARCH|APRIL|MAY|JUNE|JULY|AUGUST|SEPTEMBER|OCTOBER|NOVEMBER|DECEMBER)\s+(20\d\d)',lines[j])
        if mh:
            if int(mh[2])!=year: fail('Inconsistent year in service schedule')
            active_month=MONTHS[mh[1]];j+=1;continue
        if active_month and re.fullmatch(r'\d{1,2}',lines[j]) and j+1<len(lines) and lines[j+1].upper()==calendar.month_abbr[active_month].upper():
            day=int(lines[j]); key=f'{year}-{active_month:02}-{day:02}';j+=2
            block=[]
            while j<len(lines):
                if re.fullmatch(r'\d{1,2}',lines[j]) and j+1<len(lines) and lines[j+1].upper() in [calendar.month_abbr[k].upper() for k in range(start,end+1)]:break
                if re.fullmatch(r'('+ '|'.join(calendar.month_name[k].upper() for k in range(1,13))+r')\s+20\d\d',lines[j]):break
                block.append(lines[j]);j+=1
            theme_idx=next((k for k,s in enumerate(block) if s.startswith('THEME ')),None)
            if theme_idx is None: fail(f'Missing theme for {key}')
            prefix=block[:theme_idx]; after=block[theme_idx+1:]
            service={'title':' · '.join(prefix[1:]),'service':next((s.title() for s in prefix if 'SERVICE' in s.upper()),prefix[-1].title() if prefix else 'Worship Service'),'theme':block[theme_idx][6:]}
            k=0
            while k<len(after):
                x=after[k]
                if x=='Praise & Worship':
                    if k+1>=len(after):fail(f'Missing praise leader on {key}')
                    service['praise']=after[k+1];k+=2;continue
                if x=='Intercessory Prayer':
                    if k+1>=len(after):fail(f'Missing intercessory name on {key}')
                    service['prayer']=' '.join(after[k+1:]);break
                rm=re.match(r'Reading ([12])\s+(.+)',x)
                if rm:
                    n=rm[1]; reading=rm[2]
                    if k+2>=len(after):fail(f'Missing reading details on {key}')
                    mv=after[k+1]
                    if not mv.startswith('MV '):fail(f'Missing MV for {key} reading {n}')
                    # Some layouts put the name on the same line as MV.
                    mv_match=re.fullmatch(r'(MV\s+\d+(?:,\s*\d+)*)(?:\s+(.+))?',mv)
                    if not mv_match:fail(f'Unrecognized MV: {mv}')
                    name=mv_match[2] or after[k+2]
                    if not mv_match[2] and k+3<len(after) and after[k+3] not in ('Intercessory Prayer','Praise & Worship') and not after[k+3].startswith('Reading '):
                        name += ' '+after[k+3]
                        k+=1
                    service['r'+n]=reading+' · '+mv_match[1].strip();service['r'+n+'by']=name
                    k+=2 if mv_match[2] else 3;continue
                k+=1
            if not all(service.get(z) for z in ['theme','r1','r1by','r2','r2by']):fail(f'Incomplete service {key}')
            services[key]=service
        else:j+=1
    if not services:fail('No worship services extracted')
    # All service dates should fall within declared period.
    if any(not start<=int(d[5:7])<=end for d in services):fail('Out-of-period service found')
    if not birthdays or not anniversaries:fail('Birthdays or anniversaries missing: manual review required')
    if len(services)<4:fail('Too few services extracted: manual review required')
    # Read the recurring schedule from the PDF rather than retaining stale HTML values.
    def between(start_heading,end_heading):
        try: a=next(i for i,x in enumerate(first) if x.strip()==start_heading)
        except StopIteration: fail(f'Missing meeting heading: {start_heading}')
        b=next((i for i in range(a+1,len(first)) if first[i].strip()==end_heading),len(first))
        return [x.strip() for x in first[a+1:b] if x.strip()]
    sunday=between('Sunday Services','Weekday Meetings')
    weekday=between('Weekday Meetings','Cottage Prayer Meeting')
    if len(sunday)<8 or len(weekday)<4:fail('Meeting schedule format changed')
    meetings={'sunday':[{'name':sunday[i],'time':sunday[i+1]} for i in range(0,8,2)],'weekday':[{'name':weekday[i],'time':weekday[i+1]} for i in range(0,4,2)]}
    cottage=between('Cottage Prayer Meeting','Upcoming Events')
    if not cottage:fail('Cottage prayer schedule missing')
    meetings['weekday'].append({'name':'Cottage Prayer Meeting','time':cottage[0]})
    cottage_dates=[]
    for i,line in enumerate(cottage[1:],1):
        m=re.fullmatch(r'(\d{1,2})\s+([A-Za-z]{3})',line)
        if m and i+1<len(cottage):
            cottage_dates.append({'date':datekey(*m.groups()),'person':cottage[i+1]})
    meetings['cottageDates']=cottage_dates
    return {'period':f'{calendar.month_name[start]} – {calendar.month_name[end]} {year}', 'year':year,'start':f'{year}-{start:02}-01','end':f'{year}-{end:02}-{calendar.monthrange(year,end)[1]}','birthdays':birthdays,'anniversaries':anniversaries,'services':services,'events':events,'undatedEvents':tba,'meetings':meetings}
if __name__=='__main__':
    try:
        data=parse()
        OUT.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        OUT.with_suffix('.js').write_text('window.BULLETIN_DATA = '+json.dumps(data,ensure_ascii=False)+';\n',encoding='utf-8')
        # Embed refreshed data in HTML so local file previews work without fetch or external scripts.
        html_path=ROOT/'index.html'
        html=html_path.read_text(encoding='utf-8')
        start_marker='<!-- BULLETIN_DATA_START -->'
        end_marker='<!-- BULLETIN_DATA_END -->'
        if html.count(start_marker)!=1 or html.count(end_marker)!=1:fail('Missing unique HTML data markers')
        inline=start_marker+'\n<script>window.BULLETIN_DATA = '+json.dumps(data,ensure_ascii=False).replace('<','\\u003c')+';</script>\n'+end_marker
        html=html[:html.index(start_marker)]+inline+html[html.index(end_marker)+len(end_marker):]
        html_path.write_text(html,encoding='utf-8')
        print(f"Extracted {len(data['services'])} services, {sum(map(len,data['birthdays'].values()))} birthdays, {sum(map(len,data['anniversaries'].values()))} anniversaries, {sum(map(len,data['events'].values()))} events")
    except Exception as e:
        print(f'BULLETIN EXTRACTION FAILED — no data published: {e}',file=sys.stderr);sys.exit(1)
