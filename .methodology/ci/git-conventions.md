# Git-конвенции

---

## Ветки

### Формат

```
<type>/<scope>-<N>-<short-description>
```

**Типы:**

| Тип | Когда использовать |
|-----|--------------------|
| `feat` | Новая функциональность |
| `fix` | Исправление бага |
| `chore` | Инфраструктура, зависимости, CI/CD |
| `docs` | Только документация |
| `refactor` | Рефакторинг без изменения функциональности |

**Scope** — область кода/продукта: `backend`, `frontend`, `bot`, `infra`, `program` (кросс-продуктовое).

**N** — номер задачи или sprint'а.

**Примеры:**
- `feat/backend-1-auth-endpoint`
- `fix/bot-3-message-timeout`
- `chore/infra-2-ci-setup`
- `docs/program-1-roadmap`
- `refactor/backend-5-repository-pattern`

---

## Commit-сообщения

### Формат

```
<type>(<scope>): <описание в повелительном наклонении>
```

Описание начинается со строчной буквы, без точки в конце.

**Примеры:**
```
feat(backend): add chat history endpoint
fix(bot): handle backend timeout gracefully
chore(infra): add docker health checks
docs(arch): update sequence diagrams
refactor(backend): extract repository layer
test(backend): add integration tests for submissions
```

### Что не писать в commit-сообщениях

- Что сделал (what): ~~"Added endpoint"~~ → "add endpoint"
- Технические детали без контекста: ~~"fix bug"~~
- Ссылки на задачи в теле (используй PR description вместо этого)

---

## Pull Requests

### Процесс

1. Создать ветку от `main`.
2. Сделать коммиты по теме задачи.
3. Открыть PR в `main`.
4. Для cloud-агентов — сначала Draft PR только с `plan.md`.
5. После ревью — **Squash and Merge**.
6. После merge — удалить ветку.

### Шаблон описания PR

```markdown
## Что сделано

[1–3 пункта: что реализовано]

## Как проверить

[Команды для локальной проверки]

## Связанные документы

- Plan: [ссылка на plan.md]
- Summary: [ссылка на summary.md]
- Demo: [ссылка на demo.md или видео] (для cloud-задач)
- Linear: [ссылка на задачу] (при использовании Linear)
```

### Merge-стратегия

**Squash and Merge** — все коммиты ветки схлопываются в один.

Формат squash-коммита:
```
feat(backend): add auth endpoint (#42)
```

---

## Правила

1. **Никогда не пушить напрямую в `main`.**
2. **Никогда не делать force push в `main`.**
3. Ветка называется по задаче, не по имени разработчика.
4. Один PR = одна задача (один `plan.md`).
5. PR, выходящий за scope `plan.md`, возвращается на доработку.
6. `.env`, токены, ключи — **никогда** не коммитятся.
7. Secrets в `.gitignore` + `.env.example` с плейсхолдерами.

---

## .gitignore — обязательные исключения

```gitignore
# Environment
.env
.env.local
.env.*.local

# Python
__pycache__/
*.py[cod]
.venv/
.uv/
*.egg-info/
dist/
build/

# Node
node_modules/
.next/
.nuxt/
dist/

# IDE
.idea/
.vscode/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Secrets (явно)
*.pem
*.key
*.p12
credentials.json
service-account.json
```

Полный список дополнений — в [`gitignore-additions.txt`](gitignore-additions.txt).
