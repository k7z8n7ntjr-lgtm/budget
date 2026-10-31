# Месячный бюджет

Минималистичное приложение учёта расходов для iPhone: общий бюджет на месяц, лимиты по категориям, быстрый ввод трат, теги. PWA, работает офлайн, данные хранятся только на телефоне.

**Открыть:** https://k7z8n7ntjr-lgtm.github.io/budget/

<img src="docs/screens/01-main.png" width="240"> <img src="docs/screens/07-expense-ready.png" width="240"> <img src="docs/screens/09-tags-menu.png" width="240">

## Документация

- [Спецификация](docs/SPEC.md) — как всё работает, по экранам
- [Дизайн](docs/DESIGN.md) — цвета, шрифты, размеры, анимации
- [Решения](docs/DECISIONS.md) — почему так и от чего отказались
- [История версий](docs/CHANGELOG.md)
- [CLAUDE.md](CLAUDE.md) — как вести разработку

## Установка на iPhone

1. Откройте ссылку выше **в Safari**.
2. «Поделиться» → «На экран „Домой“».
3. Запускайте с иконки. Данные приложения с иконки и данные во вкладке Safari — разные.

Резервная копия: Настройки → «Сохранить копию данных» → «Сохранить в Файлы». Делайте раз в пару недель: iOS может очистить данные веб-приложения.

## Разработка

```bash
python3 build.py        # src/app.html → index.html, sw.js, manifest.json
python3 docs/shoot.py   # скриншоты в docs/screens (нужен Playwright + Chromium)
```

Правится только `src/app.html`. При каждом выпуске поднимается `VERSION` в `build.py`, иначе телефоны не получат обновление.

Иконки: [Lucide](https://lucide.dev) (ISC).
