"""Refresh the profile card using public GitHub data; no extra packages needed."""
import json
import os
import re
import time
import html
import urllib.request
from collections import Counter
from datetime import datetime
from html.parser import HTMLParser
from pathlib import Path
from zoneinfo import ZoneInfo

USERNAME = "oshada28nilendra-debug"
BG = '#080f19'
BORDER = '#23415e'
INK = '#dce8fa'
MUTED = '#9fb8d4'

def text(x, y, value, size=13, color=INK, extra=''):
    return f'<text x="{x}" y="{y}" fill="{color}" font-family="Arial, sans-serif" font-size="{size}" {extra}>{html.escape(str(value))}</text>'

def rect(x, y, w, h, fill=BG, stroke=BORDER, r=9):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{fill}" stroke="{stroke}"/>'

class CalendarParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.days = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag != 'td' or 'data-date' not in attrs:
            return
        match = re.fullmatch(r'contribution-day-component-([0-6])-(\d+)', attrs.get('id', ''))
        if not match:
            raise ValueError('Unrecognized contribution calendar cell')
        date = attrs['data-date']
        datetime.strptime(date, '%Y-%m-%d')
        level = int(attrs['data-level'])
        week = int(attrs['data-ix'])
        if not 0 <= level <= 4 or not 0 <= week <= 53:
            raise ValueError('Invalid contribution calendar level or week')
        self.days.append((date, int(match[1]), week, level))

def parse_calendar(page):
    parser = CalendarParser()
    parser.feed(page)
    total = re.search(r'([\d,]+)\s+contributions?\b', html.unescape(re.sub('<[^>]+>', ' ', page)))
    if not total or not parser.days:
        raise ValueError('GitHub calendar unavailable; keeping the previous analytics card')
    return int(total[1].replace(',', '')), parser.days

def fetch(url):
    headers = {'User-Agent': 'Oshada-profile-analytics', 'Accept': 'application/vnd.github+json'}
    token = os.environ.get('GH_TOKEN')
    if token and url.startswith('https://api.github.com/'):
        headers['Authorization'] = 'Bearer ' + token
    for attempt in range(3):
        try:
            request = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(request, timeout=30) as response:
                return response.read().decode('utf-8')
        except (OSError, TimeoutError):
            if attempt == 2:
                raise
            time.sleep(2 ** attempt)

def collect():
    user = json.loads(fetch(f'https://api.github.com/users/{USERNAME}'))
    repos = []
    page = 1
    while True:
        batch = json.loads(fetch(f'https://api.github.com/users/{USERNAME}/repos?type=owner&per_page=100&page={page}'))
        if not isinstance(batch, list):
            raise ValueError('Unexpected repository response')
        repos.extend(repo for repo in batch if not repo.get('private', False))
        if len(batch) < 100:
            break
        page += 1
    calendar = parse_calendar(fetch(f'https://github.com/users/{USERNAME}/contributions'))
    return user, repos, calendar

def render(u, repos, calendar, updated):
    total, days = calendar
    b=rect(1,1,878,269)+text(16,28,'⌁  GitHub Analytics',16,extra='font-weight="bold"')+text(680,27,'Updated · ' + updated,11,MUTED)
    b+=rect(14,43,285,96)
    for x,y,n,label,c in [(27,69,total,'Contributions · past year','#34d399'),(180,69,u['public_repos'],'Public repos','#78baff'),(27,112,u['followers'],'Followers','#78baff'),(180,112,u['following'],'Following','#78baff')]:
        b+=text(x,y,n,18,c)+text(x,y+16,label,10,MUTED)
    b+=rect(312,43,554,96)+text(325,61,'Contribution activity · past year',11,MUTED)
    colors=['#10212c','#0e4948','#087f76','#13b6a2','#57e5c6']
    for date, day, week, level in days:
        b+=f'<rect x="{325+week*10}" y="{69+day*8}" width="7" height="6" rx="1" fill="{colors[level]}"><title>{date}: contribution level {level}</title></rect>'
    b+=rect(14,151,285,105)+text(27,172,'Repository languages',12,extra='font-weight="bold"')
    counts=Counter(r['language'] for r in repos if not r['fork'] and r['language']); palette=['#3572A5','#f1e05a','#178600','#00B4AB','#e34c26','#f34b7d','#3178c6'];start=0
    for i,(lang,num) in enumerate(counts.most_common(4) + ([('Other', sum(n for _, n in counts.most_common()[4:]))] if len(counts) > 4 else [])):
        fraction=num/sum(counts.values());length=fraction*188.496
        b+=f'<circle cx="60" cy="213" r="30" fill="none" stroke="{palette[i % len(palette)]}" stroke-width="12" stroke-dasharray="{length} {188.496-length}" stroke-dashoffset="{-start}" transform="rotate(-90 60 213)"/>';start+=length
        if i<5:b+=f'<circle cx="111" cy="{190+i*13}" r="3" fill="{palette[i % len(palette)]}"/>'+text(121,193+i*13,f'{lang}  {num} repos',10,MUTED)
    b+=rect(312,151,554,105)+text(325,172,'Projects',12,extra='font-weight="bold"')
    for i,(slug,title,desc) in enumerate([('api-contract-watch','API Contract Watch','API tooling'),('smartcanteen-pearl','PEARL Canteen','Campus dining'),('datasetguard','DatasetGuard','Data tooling')]):
        r=next((x for x in repos if x['name']==slug),None);x=325+i*178;b+=rect(x,183,168,61,'#07111d')+text(x+10,202,title,11,'#aaceff')+text(x+10,219,desc,10,MUTED)+text(x+10,235,(f'☆ {r["stargazers_count"]}    Forks {r["forks_count"]}' if r else 'Explore project →'),10,MUTED)
    if not counts:
        b += text(30, 211, 'No language data yet', 12, MUTED)
    title = f'GitHub analytics updated {updated}: {total} contributions in the past year, {u["public_repos"]} public repositories, {u["followers"]} followers and {u["following"]} following. Languages count non-fork repositories by primary language.'
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="880" height="271" viewBox="0 0 880 271" role="img"><title>{html.escape(title)}</title>{b}</svg>\n'

def main():
    user, repos, calendar = collect()
    updated = datetime.now(ZoneInfo('Asia/Colombo')).strftime('%d %b %Y')
    result = render(user, repos, calendar, updated)
    # Validate before atomically replacing the last good card.
    import xml.etree.ElementTree as ET
    ET.fromstring(result)
    target = Path(__file__).resolve().parents[1] / 'analytics.svg'
    temporary = target.with_suffix('.svg.tmp')
    temporary.write_text(result, encoding='utf-8')
    temporary.replace(target)
    print(f'Analytics refreshed: {user["public_repos"]} public repositories; {calendar[0]} contributions.')


if __name__ == '__main__':
    main()
