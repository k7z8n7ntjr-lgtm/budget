"""Regenerate docs/screens/*.png from the built app (run `python3 build.py` first).

    python3 docs/shoot.py

Uses fixed example data and a fixed clock (Mon 26 Oct 2026, 13:00 Moscow), so the pictures only change
when the app changes. Viewport 402×800 ≈ iPhone 17 without the system bars.
"""
import functools, http.server, json, pathlib, threading
from PIL import Image
from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / 'docs/screens'
OUT.mkdir(parents=True, exist_ok=True)
W, H = 402, 800
NOW = '2026-10-26T13:00:00+03:00'

def C(i, name, icon, limit, typ='even'):
    return {'id': f'c{i}', 'name': name, 'icon': icon, 'type': typ, 'created': '2026-09', 'limits': {'2026-09': limit}}

CATS = [C(1, 'Транспорт', 'bus', 5000), C(2, 'Еда вне дома', 'utensils', 30000), C(3, 'Продукты', 'shopping-cart', 30000),
        C(4, 'Быт и дом', 'sofa', 8000), C(5, 'Здоровье', 'shield-plus', 23000), C(6, 'Сервисы/ЖКУ', 'house', 18000, 'oneoff'),
        C(7, 'Подарки', 'gift', 3000), C(8, 'Разное', 'package', None), C(9, 'Близкие', 'users', None),
        C(10, 'Поездки', 'plane', None), C(11, 'Одежда', 'shirt', None)]
TAGS = [{'id': 't1', 'name': 'Работа'}, {'id': 't2', 'name': 'Отпуск на море'}, {'id': 't3', 'name': 'Подписки'},
        {'id': 't4', 'name': 'Дети'}, {'id': 't5', 'name': 'К возврату'}]
TX = [
    ('c1', 1840, '03', 'Такси до офиса', ['t1']), ('c1', 466, '12', 'Метро', []),
    ('c2', 5120, '04', 'Ужин с друзьями', []), ('c2', 3980, '11', 'Обеды за неделю', ['t1']), ('c2', 3417, '18', 'Кофе и ланч', []),
    ('c3', 9850, '02', 'Закупка на неделю', []), ('c3', 12340, '09', 'Ашан', []), ('c3', 7310, '15', 'Вкусвилл', []), ('c3', 5137, '20', 'Овощи и молочка', ['t4']),
    ('c4', 6115, '08', 'Хозтовары', []), ('c5', 14200, '06', 'Стоматолог', []), ('c5', 6631, '16', 'Аптека', ['t4']),
    ('c6', 16676, '10', 'Квартплата и интернет', ['t3']), ('c7', 588, '14', 'Открытка и цветы', []),
    ('c8', 8749, '13', '', []), ('c9', 16032, '07', 'Маме на день рождения', []), ('c10', 7270, '17', 'Билеты на поезд', ['t2']),
]
def data(budget=150000, tx=True, tags=True, card='dark'):
    return {'v': 1, 'budget': {'2026-09': budget}, 'categories': CATS, 'settings': {'pace': True, 'card': card},
            'tags': TAGS if tags else [],
            'tx': [{'id': f'x{i}', 'cat': c, 'amount': a, 'date': f'2026-10-{d}', 'comment': cm, 'tags': tg}
                   for i, (c, a, d, cm, tg) in enumerate(TX)] if tx else []}

class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass

srv = http.server.ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(Quiet, directory=str(ROOT)))
threading.Thread(target=srv.serve_forever, daemon=True).start()
URL = f'http://127.0.0.1:{srv.server_address[1]}/index.html'

shots = []
def snap(pg, name, clip=None):
    path = OUT / f'{name}.png'
    pg.screenshot(path=str(path), clip=clip)
    shots.append(name)

with sync_playwright() as p:
    b = p.chromium.launch()
    def page(d, onboarding=False):
        ctx = b.new_context(viewport={'width': W, 'height': H}, device_scale_factor=2, has_touch=True,
                            locale='ru-RU', timezone_id='Europe/Moscow')
        pg = ctx.new_page()
        pg.clock.set_fixed_time(NOW)
        pg.add_init_script(f"try{{if(!sessionStorage.seeded){{localStorage.setItem('monthly-budget-v1', {json.dumps(json.dumps(d))});{'' if onboarding else "localStorage.setItem('budget-onboarding', JSON.stringify({days: [], done: true}));"}sessionStorage.seeded=1}}}}catch(e){{}}")
        pg.goto(URL); pg.wait_for_timeout(400)
        return pg
    key = lambda pg, k: pg.locator(f'#tx-keys [data-k="{k}"]').dispatch_event('pointerdown')
    cat = lambda pg, cid: pg.locator(f'#tx-cats [data-c="{cid}"]').click(force=True)

    # main screen
    pg = page(data()); snap(pg, '01-main')
    pg = page(data(budget=120000)); snap(pg, '02-main-overrun')
    pg = page(data(tx=False)); snap(pg, '03-main-month-start')
    pg = page(data(card='light')); snap(pg, '23-main-light')
    pg = page(data(), onboarding=True); snap(pg, '24-main-onboarding')

    # drag the budget card onto a category
    pg = page(data())
    s = pg.locator('#budget-src').bounding_box(); t = pg.locator('.cat[data-cat="c3"]').bounding_box()
    pg.mouse.move(s['x'] + 120, s['y'] + 60); pg.mouse.down()
    for i in range(1, 11): pg.mouse.move(s['x'] + 120 + (t['x'] + 80 - s['x'] - 120) * i / 10, s['y'] + 60 + (t['y'] + 35 - s['y'] - 60) * i / 10)
    snap(pg, '04-drag-to-category'); pg.mouse.up(); pg.wait_for_timeout(450)
    snap(pg, '05-expense-preset-category')

    # expense sheet
    pg = page(data()); pg.click('#fab'); pg.wait_for_timeout(450); snap(pg, '06-expense-empty')
    for k in '850': key(pg, k)
    cat(pg, 'c3'); pg.wait_for_timeout(100); snap(pg, '07-expense-ready')
    # date wheel: hold the finger on the date and pull down two rows
    d = pg.locator('#tx-date').bounding_box(); x, y = d['x'] + 70, d['y'] + 28
    pg.mouse.move(x, y); pg.mouse.down()
    for i in range(1, 9): pg.mouse.move(x, y + 68 * i / 8)
    pg.wait_for_timeout(100)
    bb = pg.locator('.amt-row').bounding_box(); snap(pg, '08-date-wheel', clip={'x': 0, 'y': bb['y'] - 76, 'width': W, 'height': 200})
    pg.mouse.up(); pg.wait_for_timeout(900)

    # tags in the form
    pg.click('#tx-tagbtn'); pg.wait_for_timeout(200)
    pg.locator('.trow', has_text='Отпуск на море').click(); pg.locator('.trow', has_text='Дети').click(); pg.wait_for_timeout(100)
    snap(pg, '09-tags-menu')
    pg.click('#tm-new'); pg.fill('#tm-input', 'работа'); pg.wait_for_timeout(100); snap(pg, '10-tags-new-duplicate')
    pg.fill('#tm-input', ''); pg.mouse.click(30, 300); pg.wait_for_timeout(150); snap(pg, '11-tags-button-selected')
    pg = page(data(tags=False)); pg.click('#fab'); pg.wait_for_timeout(450); pg.click('#tx-tagbtn'); pg.wait_for_timeout(200)
    pg.locator('#tm-input').blur(); snap(pg, '12-tags-menu-empty')

    # tags page
    pg = page(data()); pg.click('#settings-btn'); pg.wait_for_timeout(400); snap(pg, '13-settings')
    pg.click('#st-tags'); pg.wait_for_timeout(450); snap(pg, '14-tags-page')
    g = pg.locator('.trow2[data-id] .grip').nth(3).bounding_box(); x, y = g['x'] + 22, g['y'] + 22
    pg.mouse.move(x, y); pg.mouse.down()
    for i in range(1, 9): pg.mouse.move(x, y - 120 * i / 8)
    snap(pg, '15-tags-reorder'); pg.mouse.up(); pg.wait_for_timeout(100)
    pg.locator('.trow2', has_text='Работа').locator('[data-ren]').first.click(); pg.wait_for_timeout(100); snap(pg, '16-tags-rename')
    pg.click('#tp-done'); pg.locator('.trow2', has_text='Подписки').locator('[data-del]').click(); pg.wait_for_timeout(350); snap(pg, '17-tags-delete-confirm')

    # category history, edit, category settings
    pg = page(data()); pg.locator('.cat[data-cat="c3"]').click(); pg.wait_for_timeout(450); snap(pg, '18-category-history')
    pg.locator('.sheet [data-t]').first.click(); pg.wait_for_timeout(500); snap(pg, '19-expense-edit')
    pg = page(data()); pg.locator('.cat[data-cat="c3"]').click(); pg.wait_for_timeout(450); pg.click('#cat-edit'); pg.wait_for_timeout(450); snap(pg, '20-category-settings')

    # save animation: frames on one strip
    pg = page(data()); pg.click('#fab'); pg.wait_for_timeout(450)
    for k in '2000': key(pg, k)
    cat(pg, 'c7'); pg.wait_for_timeout(80)
    frames = []
    key(pg, 'ok'); t0 = 0
    for t in (60, 300, 640, 820, 1700):
        pg.wait_for_timeout(t - t0); t0 = t
        f = OUT / f'_anim_{t}.png'; pg.screenshot(path=str(f)); frames.append((t, f))
    ims = [Image.open(f) for _, f in frames]
    w, h = ims[0].size; gap = 24
    strip = Image.new('RGB', (w * len(ims) + gap * (len(ims) - 1), h), (217, 221, 216))
    for i, im in enumerate(ims): strip.paste(im, (i * (w + gap), 0))
    strip = strip.resize((strip.width // 2, strip.height // 2), Image.LANCZOS)
    strip.save(OUT / '21-save-animation.png'); shots.append('21-save-animation')
    for _, f in frames: f.unlink()

    # toast: expense dated in another month
    pg = page(data()); pg.click('#fab'); pg.wait_for_timeout(450)
    for k in '450': key(pg, k)
    pg.focus('#tx-date')
    for _ in range(40): pg.keyboard.press('ArrowUp'); pg.wait_for_timeout(15)  # to the earliest date: last month
    pg.wait_for_timeout(300)
    cat(pg, 'c1'); key(pg, 'ok'); pg.wait_for_timeout(900); snap(pg, '22-toast-other-month', clip={'x': 0, 'y': 0, 'width': W, 'height': 220})
    b.close()
srv.shutdown()
print('\n'.join(shots))
