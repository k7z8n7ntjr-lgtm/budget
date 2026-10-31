"""Build a test copy of the app from src/app.html into beta/, to try changes on the iPhone before a release.

    python3 beta.py          # then commit beta/ to main; the copy opens at …/budget/beta/

The copy keeps its data under its own key (monthly-budget-beta), registers no service worker and has an amber icon,
so it never touches the real app or its data. Delete beta/ in the release commit.
"""
import json, pathlib, re
from PIL import Image

ROOT = pathlib.Path(__file__).parent
OUT = ROOT / 'beta'
OUT.mkdir(exist_ok=True)
app = (ROOT / 'src/app.html').read_text()

def sub(a, b):
    global app
    assert app.count(a) == 1, a
    app = app.replace(a, b)

sub("const KEY = 'monthly-budget-v1';", "const KEY = 'monthly-budget-beta'; // test copy: never touches the real data")
sub("if ('serviceWorker' in navigator && document.documentElement.classList.contains('pwa')) {", "if (false) { // test copy: no service worker")
sub("<title>Месячный бюджет</title>", "<title>Бюджет β</title>")

# the same <head> as build.py, with the test copy's name and icons
build = (ROOT / 'build.py').read_text()
i = build.index("head = '''") + len("head = '''")
head = build[i:build.index("'''", i)]
head = head.replace('content="Бюджет"', 'content="Бюджет β"').replace('href="icon-', 'href="beta-icon-')
split = re.search(r'</style>', app).end()
(OUT / 'index.html').write_text(head + app[:split] + '\n</head>\n<body>\n' + app[split:] + '\n</body>\n</html>\n')

(OUT / 'manifest.json').write_text(json.dumps({
    "name": "Бюджет β (тест)", "short_name": "Бюджет β", "id": "./", "lang": "ru", "start_url": "./", "scope": "./",
    "display": "standalone", "background_color": "#F3F4F1", "theme_color": "#F3F4F1",
    "icons": [{"src": "beta-icon-192.png", "sizes": "192x192", "type": "image/png"},
              {"src": "beta-icon-512.png", "sizes": "512x512", "type": "image/png", "purpose": "any maskable"}]},
    ensure_ascii=False, indent=1))

for n in (180, 192, 512):  # the app icon with its green turned amber
    h, s, v = Image.open(ROOT / f'icon-{n}.png').convert('RGB').convert('HSV').split()
    Image.merge('HSV', (h.point(lambda x: (x - 85) % 256), s, v)).convert('RGB').save(OUT / f'beta-icon-{n}.png')
print('built beta/')
