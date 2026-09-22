from pathlib import Path
import json, re, shutil, html, subprocess
from datetime import date, datetime
import mistune
from jinja2 import Environment, FileSystemLoader, select_autoescape

ROOT = Path(__file__).resolve().parent
CONTENT = ROOT / 'content'
DOCS = ROOT / 'docs'
TEMPLATES = ROOT / 'templates'
STATIC = ROOT / 'static'
DEPLOY = ROOT / 'deploy'

FACTIONS = {
    'cathay': {
        'name': '대 캐세이', 'short': '캐세이', 'icon': '龍',
        'tagline': '방진 · 음양조화 · 정밀한 화력 분업',
        'accent': '#d6b15f'
    },
    'bretonnia': {
        'name': '브레토니아', 'short': '브레토니아', 'icon': '⚜',
        'tagline': '기사도 · 기병기동 · 망치와 모루',
        'accent': '#8cb3d9'
    },
}

CATEGORY_LABELS = {
    'campaign': '캠페인·내정',
    'characters': '군주·영웅',
    'units': '병종',
    'battle': '전투 운영',
    'reference': '빠른참조',
}

DOC_META = {
    'cathay_skill_guide.md': dict(label='스킬트리', desc='군주·영웅 스킬트리 압축 메모', order=20, category='characters', quick=True),
    'cathay_units_melee.md': dict(label='근접 보병', desc='전열·방진·대형 대응', order=30, category='units'),
    'cathay_units_ranged.md': dict(label='원거리 보병', desc='석궁·총·특수사격 운용', order=40, category='units'),
    'cathay_units_cavalry.md': dict(label='기병', desc='기동전·측후방·비행 타격', order=50, category='units'),
    'cathay_units_artillery.md': dict(label='포병·지원', desc='대포·화우·나침반·전쟁북', order=60, category='units'),

    'bretonnia_campaign_guide.md': dict(label='캠페인 운영', desc='기사도·농민 경제·확장 판단', order=10, category='campaign'),
    'bretonnia_early_game_economy_armies.md': dict(label='초반 경제·군단', desc='경제 투자·군단 규모·추가 군주', order=20, category='campaign'),
    'bretonnia_research_guide.md': dict(label='연구', desc='농업·기병·상황별 연구 우선순위', order=30, category='campaign', quick=True),
    'bretonnia_lords_heroes.md': dict(label='군주·영웅', desc='루앙·예언자·팔라딘·시녀 역할', order=40, category='characters'),
    'bretonnia_skill_guide.md': dict(label='스킬트리', desc='루앙·플로렌스·생명 예언자 성장', order=50, category='characters'),
    'bretonnia_cavalry_controls.md': dict(label='기병 조작', desc='사이클 차지·랜스·그룹·단축키', order=60, category='battle', quick=True),
    'bretonnia_advanced_battle.md': dict(label='고급 전투', desc='양익 배치·망치와 모루·측후방·브레이싱', order=70, category='battle'),
    'bretonnia_healing_fatigue.md': dict(label='회복·피로', desc='모델 수와 HP·힐 타이밍·피로 관리', order=80, category='battle', quick=True),
    'bretonnia_siege_flying.md': dict(label='공성·비행', desc='좁은 지형과 페가서스·히포그리프 운용', order=90, category='battle'),
    'bretonnia_cheatsheet.md': dict(label='전투 치트시트', desc='전투 중 30초 만에 다시 보는 핵심 명령', order=100, category='reference', quick=True),
}

def git_updated_date(path):
    try:
        rel = path.relative_to(ROOT)
        result = subprocess.run(
            ['git', 'log', '-1', '--format=%cs', '--', str(rel)],
            cwd=ROOT, capture_output=True, text=True, check=False
        )
        value = result.stdout.strip()
        if re.fullmatch(r'\d{4}-\d{2}-\d{2}', value):
            return value
    except Exception:
        pass
    return datetime.fromtimestamp(path.stat().st_mtime).date().isoformat()

markdown = mistune.create_markdown(
    escape=False,
    plugins=['table', 'strikethrough', 'task_lists', 'url']
)

def strip_md(text):
    text = re.sub(r'```.*?```', ' ', text, flags=re.S)
    text = re.sub(r'`([^`]*)`', r'\1', text)
    text = re.sub(r'!\[[^\]]*\]\([^\)]*\)', ' ', text)
    text = re.sub(r'\[([^\]]+)\]\([^\)]*\)', r'\1', text)
    text = re.sub(r'[#>*_~|\-]+', ' ', text)
    return re.sub(r'\s+', ' ', text).strip()

def get_title(text, fallback):
    m = re.search(r'^#\s+(.+)$', text, flags=re.M)
    return m.group(1).strip() if m else fallback

def get_headings(text):
    return [m.group(2).strip() for m in re.finditer(r'^(#{2,3})\s+(.+)$', text, flags=re.M)]

def slugify(s):
    s = re.sub(r'[^0-9A-Za-z가-힣]+', '-', s).strip('-').lower()
    return s or 'section'

def get_toc(text):
    used = {}
    out = []
    for m in re.finditer(r'^(#{2,3})\s+(.+)$', text, flags=re.M):
        label = m.group(2).strip()
        base = slugify(re.sub(r'[`*_~]', '', label))
        n = used.get(base, 0)
        used[base] = n + 1
        ident = base if n == 0 else f'{base}-{n+1}'
        out.append({'label': label, 'id': ident, 'level': len(m.group(1))})
    return out

def add_heading_ids(rendered):
    used = {}
    def repl(m):
        level, inner = m.group(1), m.group(2)
        plain = re.sub('<[^>]+>', '', inner)
        base = slugify(html.unescape(plain))
        n = used.get(base, 0)
        used[base] = n + 1
        ident = base if n == 0 else f'{base}-{n+1}'
        return f'<h{level} id="{ident}">{inner}<a class="heading-anchor" href="#{ident}" aria-label="이 섹션 링크">#</a></h{level}>'
    return re.sub(r'<h([2-3])>(.*?)</h\1>', repl, rendered, flags=re.S)

def category_sections(items):
    sections = []
    for key, label in CATEGORY_LABELS.items():
        docs = sorted([a for a in items if a['category'] == key], key=lambda a: (a['order'], a['label']))
        if docs:
            sections.append({'key': key, 'label': label, 'articles': docs})
    return sections

def build():
    if DOCS.exists():
        shutil.rmtree(DOCS)
    DOCS.mkdir(parents=True)
    (DOCS / 'articles').mkdir()
    shutil.copytree(STATIC, DOCS / 'static')
    (DOCS / '.nojekyll').write_text('', encoding='utf-8')
    if DEPLOY.exists():
        for item in DEPLOY.iterdir():
            target = DOCS / item.name
            if item.is_dir():
                shutil.copytree(item, target, dirs_exist_ok=True)
            else:
                shutil.copy2(item, target)

    env = Environment(
        loader=FileSystemLoader(TEMPLATES),
        autoescape=select_autoescape(['html', 'xml'])
    )
    articles = []

    for faction_key, faction in FACTIONS.items():
        faction_dir = CONTENT / faction_key
        if not faction_dir.exists():
            continue
        for path in sorted(faction_dir.glob('*.md')):
            raw = path.read_text(encoding='utf-8')
            title = get_title(raw, path.stem)
            meta = DOC_META.get(path.name, {})
            label = meta.get('label', title)
            desc = meta.get('desc', '')
            order = meta.get('order', 999)
            category = meta.get('category', 'reference')
            render_raw = re.sub(r'^#\s+.+\n+', '', raw, count=1, flags=re.M)
            html_body = add_heading_ids(markdown(render_raw))
            plain = strip_md(raw)
            excerpt = plain[:180] + ('…' if len(plain) > 180 else '')
            slug = path.stem
            rel = f'articles/{slug}.html'
            articles.append({
                'faction': faction_key, 'faction_name': faction['name'], 'faction_short': faction['short'],
                'title': title, 'label': label, 'description': desc, 'order': order,
                'category': category, 'category_label': CATEGORY_LABELS.get(category, '기타'),
                'quick': bool(meta.get('quick', False)),
                'slug': slug, 'url': rel, 'excerpt': excerpt,
                'content_text': plain[:12000], 'headings': get_headings(raw),
                'source_file': path.name,
                'updated': git_updated_date(path),
                'toc': get_toc(render_raw),
                '_html': html_body,
            })

    nav_sections = {key: category_sections([a for a in articles if a['faction'] == key]) for key in FACTIONS}
    base_ctx = {
        'factions': FACTIONS,
        'today': date.today().isoformat(),
        'category_labels': CATEGORY_LABELS,
        'nav_sections': nav_sections,
    }

    article_t = env.get_template('article.html')
    for article in articles:
        (DOCS / article['url']).write_text(
            article_t.render(**base_ctx, article=article, content=article['_html'], articles=articles),
            encoding='utf-8'
        )

    public_articles = [{k:v for k,v in a.items() if k != '_html'} for a in articles]

    home = env.get_template('index.html')
    recent = sorted(public_articles, key=lambda a: (a['updated'], a['faction'], -a['order']), reverse=True)[:6]
    quick = sorted([a for a in public_articles if a['quick']], key=lambda a: (a['faction'], a['order']))[:8]
    (DOCS / 'index.html').write_text(
        home.render(**base_ctx, articles=public_articles, recent_articles=recent, quick_articles=quick),
        encoding='utf-8'
    )

    faction_t = env.get_template('faction.html')
    for key, faction in FACTIONS.items():
        subset = sorted([a for a in public_articles if a['faction'] == key], key=lambda a: (a['order'], a['label']))
        (DOCS / f'{key}.html').write_text(
            faction_t.render(
                **base_ctx,
                faction_key=key,
                faction=faction,
                articles=public_articles,
                page_articles=subset,
                sections=category_sections(subset)
            ),
            encoding='utf-8'
        )

    search = [{k:a[k] for k in ['faction','faction_name','title','label','description','url','excerpt','content_text','headings']} for a in public_articles]
    (DOCS / 'search-index.json').write_text(json.dumps(search, ensure_ascii=False), encoding='utf-8')
    print(f'Built {len(public_articles)} articles into {DOCS}')

if __name__ == '__main__':
    build()
