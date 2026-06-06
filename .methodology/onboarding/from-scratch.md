# Onboarding: From Scratch

> **Режим:** новый проект, нет ни кода, ни документов.
> **Скопируй этот промпт и отправь агенту как первое сообщение.**

---

## Промпт для агента

```
Мы начинаем новый проект с нуля. Нужно последовательно сформировать проектную документацию по методологии AI-Driven Development.

Методология находится в .methodology/. Прочитай .methodology/METHODOLOGY.md прежде чем начинать.

Работай пошагово. На каждом шаге:
1. Задай мне все необходимые вопросы одним сообщением.
2. Дождись моих ответов.
3. Создай соответствующий документ по шаблону из .methodology/templates/.
4. Покажи мне результат и жди явного «ок» перед переходом к следующему шагу.

Шаги в порядке:

--- ШАГ 1: idea.md ---
Задай вопросы для заполнения .methodology/templates/concept/idea-template.md:
- Как называется проект?
- В чём суть продукта? (2–4 предложения)
- Для кого? (роли и их потребности)
- Какую задачу/проблему решает?
- Что войдёт в MVP (первая очередь)?
- 3–5 примеров действий пользователя
Создай: docs/concept/idea.md

--- ШАГ 2: vision.md ---
Задай вопросы для .methodology/templates/concept/vision-template.md:
- Какие компоненты системы? (backend, frontend, bot, monolith, ...)
- Какие роли пользователей и их сценарии?
- Какой технологический стек планируется?
- Какие внешние системы нужны?
Создай: docs/concept/vision.md

--- ШАГ 3: architecture.md (только если ≥2 компонентов) ---
Задай вопросы для .methodology/templates/concept/architecture-template.md:
- Как компоненты взаимодействуют между собой?
- Где живёт бизнес-логика?
- Как деплоится (docker-compose / k8s / serverless / ...)?
Создай: docs/concept/architecture.md

--- ШАГ 4: data-model.md (только если есть БД) ---
Задай вопросы для .methodology/templates/concept/data-model-template.md:
- Какие основные сущности?
- Какие связи между ними?
- Какая СУБД?
Создай: docs/concept/data-model.md

--- ШАГ 5: integrations.md (только если есть внешние сервисы) ---
Задай вопросы для .methodology/templates/concept/integrations-template.md:
- Какие внешние API или сервисы?
- Направление (in / out / bidirectional)?
- Критичность для MVP?
Создай: docs/concept/integrations.md

--- ШАГ 6: api-contracts.md (только если есть публичный API) ---
Задай вопросы для .methodology/templates/concept/api-contracts-template.md:
- Какие основные эндпоинты нужны?
- Какие входные/выходные данные?
- Какие сценарии ошибок?
Создай: docs/concept/api-contracts.md

--- ШАГ 7: roadmap.md ---
Задай вопросы для .methodology/templates/roadmap/roadmap-template.md:
- Какие крупные этапы/версии планируются?
- Что войдёт в MVP (v0.1)?
- Примерный горизонт планирования?
Создай: docs/roadmap.md

--- ШАГ 8: Первый sprint ---
На основе roadmap.md определи первый sprint:
- Предложи декомпозицию v0.1 на 2–5 задач.
- Создай docs/sprints/sprint-01-<name>/README.md по шаблону .methodology/templates/sprints/sprint-template.md
- Предложи plan.md для первой задачи по .methodology/templates/tasks/plan-template.md

--- ШАГ 9: Создать docs/README.md ---
Создай навигатор docs/README.md со ссылками на все созданные документы.

Начни с Шага 1 — задай мне все вопросы для idea.md.
```

---

## Чек-лист по завершении онбординга

- [ ] `docs/concept/idea.md` — создан и согласован
- [ ] `docs/concept/vision.md` — создан и согласован
- [ ] `docs/concept/architecture.md` — создан (или пропущен с явным обоснованием)
- [ ] `docs/concept/data-model.md` — создан (или пропущен)
- [ ] `docs/concept/integrations.md` — создан (или пропущен)
- [ ] `docs/concept/api-contracts.md` — создан (или пропущен)
- [ ] `docs/roadmap.md` — создан и согласован
- [ ] `docs/sprints/sprint-01-.../README.md` — создан
- [ ] `docs/sprints/sprint-01-.../tasks/01-.../plan.md` — создан
- [ ] `docs/README.md` — создан как навигатор
