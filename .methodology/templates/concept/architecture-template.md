# Архитектура системы

> Высокоуровневое описание компонентов, потоков данных и ссылок на детали.
> Продуктовое видение и роли — в [vision.md](vision.md). Домен — в [data-model.md](data-model.md).

---

## Контекст системы

[1–2 предложения: кто пользователи, через что работают, где живёт бизнес-логика.]

```mermaid
flowchart TB
    subgraph users["Пользователи"]
        U1["[Роль 1]"]
        U2["[Роль 2]"]
    end

    subgraph clients["Клиенты"]
        C1["[Клиент 1]"]
        C2["[Клиент 2]"]
    end

    subgraph core["Ядро"]
        API["[Backend / Core]"]
    end

    subgraph data["Данные и внешние сервисы"]
        DB[("[БД]")]
        E1["[Внешний сервис]"]
    end

    U1 --> C1
    U2 --> C2
    C1 -->|"REST JSON"| API
    C2 -->|"REST JSON"| API
    API --> DB
    API --> E1
```

---

## Контейнеры и ответственность

| Компонент | Назначение | Технологии | Документация |
|-----------|-----------|-----------|-------------|
| **[Компонент 1]** | [Что делает] | [Стек] | [README или ADR] |
| **[Компонент 2]** | [Что делает] | [Стек] | [README или ADR] |

---

## Взаимодействие клиентов с ядром

```mermaid
sequenceDiagram
    participant U as Пользователь
    participant C as [Клиент]
    participant B as [Backend]
    participant DB as [БД]
    participant E as [Внешний сервис]

    U->>C: действие / запрос
    C->>B: HTTP POST/GET /api/v1/...
    B->>DB: чтение/запись
    opt при необходимости
        B->>E: вызов внешнего сервиса
        E-->>B: ответ
    end
    B-->>C: JSON
    C-->>U: ответ в UI
```

Контракты путей и схем — в [api-contracts.md](api-contracts.md).

---

## [Компонент 1] — внутренняя структура

```mermaid
flowchart LR
    subgraph entry["Точка входа"]
        M[main.py / index.ts]
    end

    subgraph http["HTTP"]
        R["routers/ или routes/"]
    end

    subgraph logic["Логика"]
        S["services/"]
    end

    subgraph data_layer["Данные"]
        REP["repositories/"]
        MOD["models/"]
    end

    M --> R
    R --> S
    S --> REP
    REP --> MOD
```

[Краткое описание: что в роутерах, что в сервисах, что в репозиториях.]

---

## [Компонент 2] — внутренняя структура

[Аналогичный раздел для второго компонента, если нужен.]

---

## Деплой — локально

[Описание: как поднять весь стек локально. Ссылка на docker-compose или README.]

---

## Деплой — production

[Описание: где живёт production, как деплоится (CI/CD), ссылка на deploy-документ.]

---

## Связанные документы

- [vision.md](vision.md) — сценарии и принципы
- [data-model.md](data-model.md) — сущности БД
- [api-contracts.md](api-contracts.md) — REST-контракты
- [integrations.md](integrations.md) — внешние сервисы
- [decisions/](../decisions/) — архитектурные решения (ADR)
