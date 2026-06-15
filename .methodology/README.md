# AI-Driven Development

Самодостаточный методологический пакет для AI-driven / Spec-driven разработки с агентами.

Скопируйте папку `.methodology/` в любой новый или существующий проект — и команда (или агент) сразу получает единый проектный язык, структуру документов, правила процесса и точки входа.

---

## Что внутри

```
.methodology/
├── METHODOLOGY.md          # цельное описание: 5 слоёв, иерархия, поток работы
├── GLOSSARY.md             # словарь терминов
├── eval/                   # eval-трек: ядро и справочник метрик
├── rules/                  # правила для .cursor/rules/
├── templates/              # шаблоны для всех слоёв (включая templates/eval/)
├── onboarding/             # точки входа для агента (3 режима)
├── ci/                     # стартер CI/Git
└── examples/               # живые примеры заполненной методологии
```

---

## Установка в проект (3 шага)

### Шаг 1. Скопировать пакет

```bash
cp -r .methodology/ /path/to/your-project/.methodology/
```

### Шаг 2. Активировать правила в Cursor

```bash
mkdir -p /path/to/your-project/.cursor/rules/methodology
cp .methodology/rules/*.mdc /path/to/your-project/.cursor/rules/methodology/
```

Убедитесь, что правила `alwaysApply: true` в метаданных каждого `.mdc` файла, или включите их вручную в настройках Cursor.

### Шаг 3. Выбрать onboarding-режим

| Ситуация | Промпт |
|----------|--------|
| Проект с нуля — нет ни кода, ни документов | [`onboarding/from-scratch.md`](onboarding/from-scratch.md) |
| Есть рабочий код, но нет документов | [`onboarding/existing-code.md`](onboarding/existing-code.md) |
| Проект уже на методологии, открыть следующую задачу | [`onboarding/continue-project.md`](onboarding/continue-project.md) |

Скопируйте содержимое нужного промпта и отправьте агенту как первое сообщение.

---

## Быстрая навигация

| Что нужно | Куда |
|-----------|------|
| Понять методологию целиком | [METHODOLOGY.md](METHODOLOGY.md) |
| Найти термин | [GLOSSARY.md](GLOSSARY.md) |
| Написать идею проекта | [templates/concept/idea-template.md](templates/concept/idea-template.md) |
| Написать техническое видение | [templates/concept/vision-template.md](templates/concept/vision-template.md) |
| Составить архитектуру | [templates/concept/architecture-template.md](templates/concept/architecture-template.md) |
| Спроектировать базу данных | [templates/concept/data-model-template.md](templates/concept/data-model-template.md) |
| Зафиксировать внешние интеграции | [templates/concept/integrations-template.md](templates/concept/integrations-template.md) |
| Зафиксировать API-контракты | [templates/concept/api-contracts-template.md](templates/concept/api-contracts-template.md) |
| Составить дорожную карту | [templates/roadmap/roadmap-template.md](templates/roadmap/roadmap-template.md) |
| Спланировать спринт | [templates/sprints/sprint-template.md](templates/sprints/sprint-template.md) |
| Создать план задачи | [templates/tasks/plan-template.md](templates/tasks/plan-template.md) |
| Зафиксировать итог задачи | [templates/tasks/summary-template.md](templates/tasks/summary-template.md) |
| Записать видео-демо | [templates/tasks/demo-template.md](templates/tasks/demo-template.md) |
| Написать спецификацию фичи | [templates/specs/spec-template.md](templates/specs/spec-template.md) |
| Зафиксировать архитектурное решение | [templates/decisions/adr-template.md](templates/decisions/adr-template.md) |
| Настроить CI/Git | [ci/git-conventions.md](ci/git-conventions.md) |
| Запустить измерительный контур качества (eval) | [eval/eval-methodology.md](eval/eval-methodology.md) |
| Выбрать метрики для оценки агента | [eval/metrics-guide.md](eval/metrics-guide.md) |

---

## Eval-трек

Расширение методологии для измерительного контура качества LLM-агентов — от построения датасетов до сравнения конфигураций и регрессионного гейта. Основан на AI Engineering Loop (Langfuse Academy) и ADK (Google). Запускается единой kickoff-фразой, описанной в ядре.

→ Ядро и поток работы: [eval/eval-methodology.md](eval/eval-methodology.md)
→ Справочник метрик (категории A–E, инструменты): [eval/metrics-guide.md](eval/metrics-guide.md)
→ Шаблоны: [templates/eval/](templates/eval/)
