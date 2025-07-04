# FastypeBot

FastypeBot — это Telegram-бот, который предоставляет возможности работы с Ии через API для тренировки слепой печати. Данный репозиторий содержит исходный код и инструкции по запуску бота.

## Быстрый старт

1. **Клонируйте репозиторий:**
   ```bash
   git clone https://github.com/MARKeting-715/FastypeBot.git
   cd FastypeBot
   ```

2. **Установите зависимости:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Создайте файл конфигурации `config.py`**

   В корне проекта создайте файл `config.py` и добавьте в него необходимые ключи:

   ```python
   API_KEY = "ваш_telegram_api_key"
   AI_KEY = "ваш_open_router_key"
   ```

4. **Запустите бота:**
   ```bash
   python fastype.py
   ```

## Особенности

- Поддержка интеграции с ИИ через API.
- Простой запуск и настройка.

## Вклад

PR и улучшения приветствуются! Не забудьте создать issue или pull request перед отправкой изменений.

## Заметки

Лучше всего работает модель Llama, так что советую выбрать ее, остальные могут работать неправильно из за некорректного промпта

## Лицензия

Этот проект распространяется под лицензией MIT. Подробности смотрите в файле LICENSE.
