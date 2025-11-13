# AI Powered SmartSearch Frontend

Интеллектуальный пользовательский интерфейс с умной строкой поиска для работы с корпоративными данными на естественном языке.
Поддерживает диалоговый режим, выбор аккаунта, SSE-стриминг и обработку больших ответов.

## Технологии

- HTML5 + CSS3 + JavaScript (ES6)
- Font Awesome 6 — иконки
- Highlight.js — подсветка синтаксиса
- Markdown-it — рендеринг markdown
- SSE (Server-Sent Events) — потоковые ответы от бэкенда

## Структура папок

```
frontend
├───static
│   ├───css
│   │   └───style.css
│   └───js
│       └───script.js
└───templates
    └───index.html
```

## Основной функционал

- Выбор аккаунта (модальное окно, cookies, logout)
- Чат с AI (стриминговые ответы через SSE)
- Поддержка Markdown + подсветка кода
- Интерфейс выбора при больших данных (скачать JSON или продолжить генерацию)
- Адаптивная верстка

## а что по картинкам?

главный экран

<p>
 <img width="500px" src="/media/front_main.png" alt="qr"/>
</p>

выбор пользователя

<p>
 <img width="500px" src="/media/front_auth.png" alt="qr"/>
</p>

чат

<p>
 <img width="500px" src="/media/front_chat.png" alt="qr"/>
</p>

возможность скачать ответ если он большой

<p>
 <img width="500px" src="/media/front_bigreq.png" alt="qr"/>
</p>

## **[На главную](../../README.md)** 