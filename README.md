# UtmCraft
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

## Dev
1) Настроить окружение

```bash
make dev-env
```

Команда поднимает окружение в Docker (Postgres и Redis), устанавливает Python-зависимости, 
применяет миграции и фикстуры, создает пользователя `utmcraft` с паролем `12345`.

2) Запустить проект

```bash
make run-dev
```

## Prod

1) Заполнить файл с переменными окружения deploy/.env
2) Запустить сборку и запуск проекта в Docker

```bash
cd deploy && ./run.sh
```

3) Пользователь всегда будет `utmcraft`. Пароль – значение переменной окружения `DJANGO_USER_PASSWORD`.
