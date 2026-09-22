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

DOC_META = {
    'cathay_skill_guide.md': ('스킬트리', '군주·영웅 스킬트리 압축 메모', 20),
    'cathay_units_melee.md': ('근접 보병', '전열·방진·대형 대응', 30),
    'cathay_units_ranged.md': ('원거리 보병', '석궁·총·특수사격 운용', 40),
    'cathay_units_cavalry.md': ('기병', '기동전·측후방·비행 타격', 50),
    'cathay_units_artillery.md': ('포병·지원', '대포·화우·나침반·전쟁북', 60),
    'bretonnia_campaign_guide.md': ('캠페인 운영', '기사도·농민 경제·확장 판단', 10),
    'bretonnia_early_game_economy_armies.md': ('초반 경제·군단', '경제 투자·군단 규모·추가 군주', 20),
    'bretonnia_lords_heroes.md': ('군주·영웅', '루앙·예언자·팔라딘·시녀 역할', 30),
    'bretonnia_skill_guide.md': ('스킬트리', '루앙·플로렌스·생명 예언자 성장', 40),
    'bretonnia_cavalry_controls.md': ('기병 전투 조작', '사이클 차지·랜스·그룹·단축키', 50),
}


def git_updated_date(path):
    """Return YYYY-MM-DD for the last Git commit touching path; fall back to mtime."""
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

def slugify(s):
    s = re.sub(r'[^0-9A-Za-z가-힣]+', '-', s).strip('-').lower()
    return s or 'section'

def add_heading_ids(rendered, headings):
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
    base_ctx = {'factions': FACTIONS, 'today': date.today().isoformat()}
    articles = []

    for faction_key, faction in FACTIONS.items():
        for path in sorted((CONTENT / faction_key).glob('*.md')):
            raw = path.read_text(encoding='utf-8')
            title = get_title(raw, path.stem)
            label, desc, order = DOC_META.get(path.name, (title, '', 999))
            render_raw = re.sub(r'^#\s+.+\n+', '', raw, count=1, flags=re.M)
            html_body = add_heading_ids(markdown(render_raw), get_headings(render_raw))
            plain = strip_md(raw)
            excerpt = plain[:180] + ('…' if len(plain) > 180 else '')
            slug = path.stem
            rel = f'articles/{slug}.html'
            article = {
                'faction': faction_key, 'faction_name': faction['name'], 'faction_short': faction['short'],
                'title': title, 'label': label, 'description': desc, 'order': order,
                'slug': slug, 'url': rel, 'excerpt': excerpt,
                'content_text': plain[:12000], 'headings': get_headings(raw),
                'source_file': path.name,
                'updated': git_updated_date(path),
                'toc': get_toc(render_raw),
            }
            articles.append(article)
            tmpl = env.get_template('article.html')
            (DOCS / rel).write_text(tmpl.render(**base_ctx, article=article, content=html_body, articles=articles), encoding='utf-8')

    # Re-render article pages now that full article list exists (for complete nav)
    tmpl = env.get_template('article.html')
    for article in articles:
        raw = (CONTENT / article['faction'] / article['source_file']).read_text(encoding='utf-8')
        render_raw = re.sub(r'^#\s+.+\n+', '', raw, count=1, flags=re.M)
        html_body = add_heading_ids(markdown(render_raw), get_headings(render_raw))
        (DOCS / article['url']).write_text(tmpl.render(**base_ctx, article=article, content=html_body, articles=articles), encoding='utf-8')

    # home + faction pages
    home = env.get_template('index.html')
    (DOCS / 'index.html').write_text(home.render(**base_ctx, articles=articles), encoding='utf-8')
    faction_t = env.get_template('faction.html')
    for key, faction in FACTIONS.items():
        subset = sorted([a for a in articles if a['faction']==key], key=lambda a: (a['order'], a['label']))
        (DOCS / f'{key}.html').write_text(faction_t.render(**base_ctx, faction_key=key, faction=faction, articles=subset), encoding='utf-8')

    search = [{k:a[k] for k in ['faction','faction_name','title','label','description','url','excerpt','content_text','headings']} for a in articles]
    (DOCS / 'search-index.json').write_text(json.dumps(search, ensure_ascii=False), encoding='utf-8')
    print(f'Built {len(articles)} articles into {DOCS}')

if __name__ == '__main__':
    build()
