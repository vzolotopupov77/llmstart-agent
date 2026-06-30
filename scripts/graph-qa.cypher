// ============================================================
// graph-qa.cypher — контрольные запросы для инспекции графа
// Запуск: make graph-qa
// Ожидаемые результаты зафиксированы в комментариях
// ============================================================

// 1. Орфанные узлы (без рёбер) — ожидаем 0 строк
MATCH (n) WHERE NOT (n)--()
RETURN labels(n)[0] AS label, n.id AS id, n.name AS name
ORDER BY label, id;

// 2. Дубли тем по toLower(name) — ожидаем 0 строк
MATCH (t1:Theme), (t2:Theme)
WHERE elementId(t1) < elementId(t2)
  AND toLower(
        CASE WHEN t1.name IS :: STRING THEN t1.name ELSE t1.name[0] END
      ) = toLower(
        CASE WHEN t2.name IS :: STRING THEN t2.name ELSE t2.name[0] END
      )
RETURN t1.id AS dup1, t2.id AS dup2,
       CASE WHEN t1.name IS :: STRING THEN t1.name ELSE t1.name[0] END AS name;

// 3. Покрытие тем по курсам (Course -[:COVERS]-> Theme)
// Ожидаем: vibe-coding 4, fullstack-aidd 9, agents 15, deep-agents 14
MATCH (c:Course)-[:COVERS]->(t:Theme)
RETURN c.id AS course, count(t) AS themeCnt
ORDER BY themeCnt DESC;

// 4. Входящая степень тем (популярность — сколько курсов покрывают тему)
MATCH (t:Theme)
OPTIONAL MATCH ()-[r:COVERS]->(t)
RETURN t.id AS theme, count(r) AS coveredBy
ORDER BY coveredBy DESC, theme;

// 5. Prerequisite-цепочки: полные пути RECOMMENDED_BEFORE
// Ожидаем цепочку: vibe-coding -> fullstack-aidd -> agents -> deep-agents
MATCH (a:Course)
WHERE NOT ()-[:RECOMMENDED_BEFORE]->(a)
  AND (a)-[:RECOMMENDED_BEFORE]->()
MATCH p = (a)-[:RECOMMENDED_BEFORE*1..10]->(b:Course)
RETURN [n IN nodes(p) | n.id] AS chain, length(p) AS hops
ORDER BY hops DESC;

// 6. Курсы без аудитории TARGETS — ожидаем 0 строк
MATCH (c:Course)
WHERE NOT (c)-[:TARGETS]->()
RETURN c.id AS courseWithoutAudience;

// 7a. Итоговые счётчики узлов по меткам
// Ожидаем: Theme 29, Course 4, Format 6, Audience 5, Level 3, Combo 1 (итого 48)
MATCH (n)
RETURN labels(n)[0] AS label, count(n) AS cnt
ORDER BY cnt DESC;

// 7b. Итоговые счётчики рёбер по типам
// После seed-only: REQUIRES 12, COVERS >= 42 (post-extract может быть 48+)
// TARGETS 8, AVAILABLE_AS 7, AT_LEVEL 4, INCLUDES 4, RECOMMENDED_BEFORE 3
MATCH ()-[r]->()
RETURN type(r) AS rel, count(r) AS cnt
ORDER BY cnt DESC;

// 8. Похожие дубли тем (apoc.text.levenshteinSimilarity > 0.85) — ожидаем 0 строк
MATCH (t1:Theme), (t2:Theme)
WHERE elementId(t1) < elementId(t2)
WITH t1, t2,
     toLower(CASE WHEN t1.name IS :: STRING THEN t1.name ELSE t1.name[0] END) AS n1,
     toLower(CASE WHEN t2.name IS :: STRING THEN t2.name ELSE t2.name[0] END) AS n2
WHERE apoc.text.levenshteinSimilarity(n1, n2) > 0.85
RETURN t1.id AS dup1, t2.id AS dup2, n1 AS name1, n2 AS name2,
       apoc.text.levenshteinSimilarity(n1, n2) AS similarity
ORDER BY similarity DESC;

// 9. Распределение степени узлов (min / max / avg)
MATCH (n)
OPTIONAL MATCH (n)-[r]-()
WITH n, count(r) AS degree
RETURN min(degree) AS minDegree, max(degree) AS maxDegree,
       round(avg(degree), 2) AS avgDegree, count(n) AS nodeCount;

// 10. Доля курсов с COVERS-связью (ожидаем 100%)
MATCH (c:Course)
OPTIONAL MATCH (c)-[:COVERS]->(t:Theme)
WITH c, count(t) AS themeCnt
WITH count(c) AS totalCourses,
     sum(CASE WHEN themeCnt > 0 THEN 1 ELSE 0 END) AS coursesWithCovers
RETURN totalCourses, coursesWithCovers,
       round(100.0 * coursesWithCovers / totalCourses, 1) AS pctWithCovers;

// 11. REQUIRES self-loops (A -> A) — ожидаем 0 строк
MATCH (a:Theme)-[r:REQUIRES]->(b:Theme)
WHERE a.id = b.id
RETURN a.id AS theme, count(r) AS loopCnt
ORDER BY loopCnt DESC;

// 12. REQUIRES duplicate pairs — ожидаем 0 строк
MATCH (a:Theme)-[r:REQUIRES]->(b:Theme)
WITH a.id AS from_id, b.id AS to_id, count(r) AS cnt
WHERE cnt > 1
RETURN from_id, to_id, cnt
ORDER BY cnt DESC;
