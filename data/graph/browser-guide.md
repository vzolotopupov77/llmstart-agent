# Neo4j Browser — инструкция для инспекции графа

## Доступ

| Параметр | Значение |
|----------|----------|
| URL | http://localhost:7474 |
| Connect URL | `bolt://localhost:7687` |
| Username | `neo4j` (из `NEO4J_USER` в `.env`) |
| Password | из `NEO4J_PASSWORD` в `.env` (default: `neo4jdev`) |

---

## CLI-команды

```bash
# Запустить Neo4j
make graph-up

# Интерактивный cypher-shell (admin)
make graph-shell

# Загрузить seed (идемпотентно)
make graph-seed

# Быстрая статистика: узлы, рёбра, орфаны, COVERS-покрытие
make graph-inspect

# 7 QA-запросов из scripts/graph-qa.cypher
make graph-qa

# Авто-извлечение тем (SimpleKGPipeline)
make graph-extract

# Сравнение seed vs auto
make graph-compare
```

---

## Starter Queries для Neo4j Browser

Скопируй нужный запрос в поле ввода Browser и нажми ► (Ctrl+Enter).

### Визуализация всего графа (первые 100 рёбер)

```cypher
MATCH (n)-[r]->(m) RETURN n, r, m LIMIT 100
```

### Траектория обучения: цепочка курсов

```cypher
MATCH p = (a:Course)-[:RECOMMENDED_BEFORE*1..10]->(b:Course)
WHERE NOT ()-[:RECOMMENDED_BEFORE]->(a)
RETURN p
```

### Курс и все его темы

```cypher
MATCH (c:Course {id: 'agents'})-[r:COVERS]->(t:Theme)
RETURN c, r, t
```

### Что нужно знать, чтобы изучить тему graphrag

```cypher
MATCH p = (t:Theme {id: 'graphrag'})-[:REQUIRES*1..3]->(prereq:Theme)
RETURN p
```

### Состав комбо со stepOrder

```cypher
MATCH (cb:Combo)-[r:INCLUDES]->(c:Course)
RETURN cb.id AS combo, r.stepOrder AS step, c.id AS course, c.priceRub AS price
ORDER BY r.stepOrder
```

### Аудитория для каждого курса

```cypher
MATCH (c:Course)-[:TARGETS]->(a:Audience)
RETURN c.id AS course, collect(a.id) AS audiences
```

### Топ тем по числу курсов, которые их покрывают

```cypher
MATCH (t:Theme)<-[:COVERS]-(c:Course)
RETURN t.id AS theme, count(c) AS courses
ORDER BY courses DESC
LIMIT 10
```

### Курсы для продвинутого уровня

```cypher
MATCH (c:Course)-[:AT_LEVEL]->(l:Level {id: 'advanced'})
RETURN c.id, c.title, c.priceRub
```

### Статистика узлов и рёбер

```cypher
MATCH (n) RETURN labels(n)[0] AS label, count(n) AS cnt ORDER BY cnt DESC;
MATCH ()-[r]->() RETURN type(r) AS rel, count(r) AS cnt ORDER BY cnt DESC
```

### Орфанные узлы (ожидаем 0)

```cypher
MATCH (n) WHERE NOT (n)--() RETURN labels(n)[0] AS label, n.id AS id
```

---

## Часто используемые ярлыки Browser

| Действие | Shortcut |
|----------|----------|
| Выполнить запрос | Ctrl+Enter |
| История запросов | стрелка ↑ в поле ввода |
| Сохранить запрос | ★ в панели результатов |
| Переключить вид (граф/таблица/текст) | иконки в правом углу карточки результата |
| Открыть настройки Browser | ⚙ → Browser Settings |
| Включить стрелки на рёбрах | Settings → Connect result nodes → включить |
