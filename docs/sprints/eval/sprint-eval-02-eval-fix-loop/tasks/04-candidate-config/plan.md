# Plan: Задача 04 — Candidate-конfig #1 (RAG-first prompt)

> **Спринт:** [../../README.md](../../README.md) · **Статус:** ✅ Done

## Цель

Первый eval-fix loop (E-7): **один** параметр vs baseline — `prompt.name: agent-system-prompt-v2` (RAG-first). Прогон + compare.

## Гипотеза (из analyze)

9 retrieval-провалов: агент отвечает без `search_knowledge_base`. v2: обязательный KB-поиск перед фактическими ответами.

## Состав

- [x] `prompts.py` — v2 + registry `get_system_prompt`
- [x] `ReactRunner` + `AgentConfigRegistry` — применять `config.prompt.name` (E-6)
- [x] `evals/configs/candidate-rag-first-prompt.yaml`
- [x] Тесты backend
- [x] Прогон candidate (094647Z)
- [x] compare vs baseline 083100Z
- [x] summary (⛔ review pending)

## DoD

| # | Критерий |
|---|----------|
| 1 | Candidate отличается только `prompt.name` |
| 2 | Прогон 26 items, compare report |
| 3 | Δ avg_answer_correctness зафиксирован |
| 4 | ⛔ Пользователь видит compare |
