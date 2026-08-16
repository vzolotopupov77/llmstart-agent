# Приложение: инвентарь Promptfoo 0.122.0

> **Спринт:** [sprint-11-red-teaming-baseline](../../docs/sprints/sprint-11-red-teaming-baseline/README.md)
> **Задача:** [03-plugin-selection](../../docs/sprints/sprint-11-red-teaming-baseline/tasks/03-plugin-selection/plan.md)
> **Основной документ:** [plugin-selection.md](./plugin-selection.md)
> **Дата выгрузки:** 2026-08-14

Справочник существует ровно для одной цели: любое имя плагина или стратегии в [plugin-selection.md](./plugin-selection.md) и в конфиге задачи 04 обязано присутствовать здесь. Если имени нет в этом файле — оно выдумано.

---

## 1. Источники выгрузки

| Что | Источник | Команда / путь |
|---|---|---|
| Список плагинов (155) | CLI запинённой версии | `npx promptfoo@0.122.0 redteam plugins` |
| Списки стратегий, коллекций, remote-only, canary-breaking | Исходники тега `0.122.0` | `src/redteam/constants/strategies.ts`, `src/redteam/constants/plugins.ts` |
| Схема секции `redteam` | Исходники тега `0.122.0` | `src/validators/redteam.ts` |
| Маппинг OWASP LLM / ASI | Исходники тега `0.122.0` | `src/redteam/constants/frameworks.ts` |
| Требования к `config` плагинов | Документация тега `0.122.0` | `site/docs/red-team/plugins/*.md` |

Версия запинена в [tooling-setup.md](./tooling-setup.md): дальше по спринту только `@0.122.0`, не `@latest`. При смене версии этот файл выгружается заново, иначе baseline «до/после» несопоставимы.

---

## 2. Дефолты версии

| Константа | Значение | Где влияет |
|---|---|---|
| `DEFAULT_NUM_TESTS_PER_PLUGIN` | `5` | Число кейсов на плагин, если не задан `numTests` |
| `REDTEAM_DEFAULTS.NUM_TESTS` | `10` | Дефолт CLI-флага `--num-tests` |
| `REDTEAM_DEFAULTS.MAX_CONCURRENCY` | `4` | Параллельные обращения к таргету |
| `REDTEAM_MODEL` | `openai:chat:gpt-5.5-2026-04-23` | Модель генерации атак **по умолчанию** — требует `OPENAI_API_KEY` для api.openai.com; перекрывается через `redteam.provider` |
| `DEFAULT_MULTI_TURN_MAX_TURNS` | `5` | Число ходов у многоходовых стратегий |
| Fan-out `jailbreak:composite` | `5` | Одна базовая проверка → 5 кейсов |
| Fan-out `gcg` | `1` | — |
| `MULTI_INPUT_VAR` | `__prompt` | Имя переменной в multi-input-режиме |

---

## 3. Ключи секции `redteam` (RedteamConfigSchema)

| Ключ | Тип | Назначение |
|---|---|---|
| `purpose` | string | Описание системы для генерации и грейдинга |
| `plugins` | array | Плагины (строка или объект `{id, numTests, config, severity}`) |
| `strategies` | array | Стратегии (строка или объект `{id, config}`); дефолт — `['default']` |
| `numTests` | int > 0 | Число кейсов на плагин по умолчанию |
| `language` | string \| string[] | Язык(и) генерируемых кейсов |
| `entities` | string[] | Имена людей, брендов, организаций, относящихся к системе |
| `provider` | provider | Провайдер генерации состязательных входов |
| `maxConcurrency` | int > 0 | Параллельные вызовы |
| `maxCharsPerMessage` | int > 0 | Верхняя граница длины одной сгенерированной реплики |
| `delay` | int ≥ 0 | Пауза между вызовами API плагинов, мс |
| `testGenerationInstructions` | string | Дополнительные инструкции генерации, применяются к каждому плагину |
| `injectVar` | string | Переменная для инъекции (single-input режим) |
| `frameworks` | enum[] | Подмножество фреймворков для генерации, отчётов и фильтрации |
| `contexts` | array | Несколько контекстов со своим `purpose` |
| `graderExamples` | array | Примеры для грейдера |
| `excludeTargetOutputFromAgenticAttackGeneration` | bool | Не передавать ответ таргета в агентную генерацию атак |
| `tracing` | object | Настройки трассировки |

Допустимые значения `frameworks`: `mitre:atlas`, `nist:ai:measure`, `owasp:api`, `owasp:llm`, `owasp:agentic`, `eu:ai-act`, `iso:42001`, `gdpr`, `dod:ai:ethics`.

---

## 4. Плагины, требующие `config`

| Плагин | Обязательный ключ `config` | Проверено по |
|---|---|---|
| `policy` | `policy` — текст правила | `CONFIG_REQUIRED_PLUGINS` в `constants/plugins.ts` |
| `intent` | `intent` — список намерений | `CONFIG_REQUIRED_PLUGINS` |
| `prompt-extraction` | `systemPrompt` — текст системного промпта | `site/docs/red-team/plugins/prompt-extraction.md`: «The `systemPrompt` config is required» |
| `indirect-prompt-injection` | `indirectInjectionVar` — имя переменной шаблона с недоверенным содержимым | `site/docs/red-team/plugins/indirect-prompt-injection.md` |

`policy` можно указывать несколько раз с разным текстом: ключ дедупликации в `src/validators/redteam.ts` — `${id}:${JSON.stringify(config)}:${severity}`, то есть разные тексты дают разные экземпляры плагина.

---

## 5. Особые списки плагинов

### 5.1 Remote-only — генерация всегда идёт в API Promptfoo

`redteam.provider` на эти плагины **не влияет**: локальной реализации у них нет (`createRemotePlugin()`).

`agentic:memory-poisoning`, `coding-agent:*` (все), `ascii-smuggling`, `bfla`, `bola`, `cca`, `competitors`, `coppa`, `data-exfil`, `ferpa`, `goal-misalignment`, `harmful:misinformation-disinformation`, `harmful:specialized-advice`, `hijacking`, `indirect-prompt-injection`, `mcp`, `model-identification`, `off-topic`, `rag-document-exfiltration`, `rag-poisoning`, `rag-source-attribution`, `reasoning-dos`, `religion`, `special-token-injection`, `ssrf`, `system-prompt-override`, `wordplay`, а также все `medical:*`, `financial:*`, `pharmacy:*`, `insurance:*`, `ecommerce:*`, `telecom:*`, `realestate:*`.

Следствие: при `PROMPTFOO_DISABLE_REMOTE_GENERATION` эти плагины отключаются, а набор кейсов молча уменьшается.

### 5.2 Плагины без стратегий (`STRATEGY_EXEMPT_PLUGINS`)

Стратегии к ним не применяются — число кейсов равно `numTests`.

- Агентные: `system-prompt-override`, `agentic:memory-poisoning`
- Датасетные: `aegis`, `beavertails`, `cyberseceval`, `donotanswer`, `harmbench`, `pliny`, `toxic-chat`, `unsafebench`, `vlguard`, `vlsu`, `xstest`

### 5.3 Коллекции (`COLLECTIONS`)

`default`, `foundation`, `harmful`, `pii`, `bias`, `medical`, `pharmacy`, `insurance`, `financial`, `ecommerce`, `telecom`, `teen-safety`, `realestate`, `guardrails-eval`, `coding-agent:core`, `coding-agent:all`.

Коллекция в `plugins` разворачивается в десятки плагинов — в конфиге спринта не используется ни одна.

### 5.4 Исключены из multi-input-режима

`cca`, `cross-session-leak` + все датасетные.

---

## 6. Полный список плагинов (155)

Выгрузка `npx promptfoo@0.122.0 redteam plugins`, порядок и описания — как выдал CLI.

| ID | Описание |
|---|---|
| `aegis` | Tests content safety handling using NVIDIA's Aegis dataset |
| `agentic:memory-poisoning` | Tests whether an agent is vulnerable to memory poisoning attacks |
| `ascii-smuggling` | Tests vulnerability to Unicode tag-based instruction smuggling attacks |
| `beavertails` | Tests handling of malicious prompts from the BeaverTails dataset |
| `bfla` | Tests for broken function-level authorization vulnerabilities (OWASP API 5) |
| `bias:age` | Age-related bias detection |
| `bias:disability` | Disability-related bias detection |
| `bias:gender` | Gender-related bias detection |
| `bias:race` | Race-related bias detection |
| `bola` | Tests for broken object-level authorization vulnerabilities (OWASP API 1) |
| `cca` | Tests for vulnerability to Context Compliance Attacks using fabricated conversation history |
| `coding-agent:automation-poisoning` | Tests for unsafe changes to repository automation |
| `coding-agent:delayed-ci-exfil` | Tests for data exfiltration through CI automation |
| `coding-agent:generated-vulnerability` | Tests for insecure code generated by coding agents |
| `coding-agent:network-egress-bypass` | Tests for unauthorized outbound network requests |
| `coding-agent:procfs-credential-read` | Tests for credential exposure through process metadata |
| `coding-agent:repo-prompt-injection` | Tests for prompt injection in repository content |
| `coding-agent:sandbox-read-escape` | Tests for reads outside the intended workspace |
| `coding-agent:sandbox-write-escape` | Tests for writes outside the intended workspace |
| `coding-agent:secret-env-read` | Tests for exposure of environment secrets |
| `coding-agent:secret-file-read` | Tests for unauthorized access to sensitive files |
| `coding-agent:steganographic-exfil` | Tests for sensitive data hidden in agent outputs |
| `coding-agent:terminal-output-injection` | Tests for prompt injection in terminal output |
| `coding-agent:verifier-sabotage` | Tests for weakened tests and security checks |
| `competitors` | Tests for unauthorized competitor mentions and endorsements |
| `contracts` | Tests for unauthorized contractual commitments and legal exposure |
| `coppa` | Tests for COPPA (Children's Online Privacy Protection Act) compliance violations |
| `cross-session-leak` | Tests for information leakage between user sessions |
| `cyberseceval` | Tests prompt injection attacks from Meta's CyberSecEval dataset |
| `data-exfil` | Tests for data exfiltration via URL parameters, images, or markdown links |
| `debug-access` | Tests for exposed debugging interfaces and commands |
| `divergent-repetition` | Tests for training data leaks through repetitive pattern exploitation that causes model divergence |
| `donotanswer` | Tests for vulnerabilities to Do Not Answer attacks |
| `ecommerce:compliance-bypass` | Tests for attempts to bypass security rules, terms of service, or compliance policies in e-commerce systems |
| `ecommerce:order-fraud` | Tests for detection of fraudulent order patterns, unauthorized transactions, or payment manipulation attempts |
| `ecommerce:pci-dss` | Tests for exposure of payment card data including credit card numbers, CVVs, and bank account details in violation of PCI DSS requirements |
| `ecommerce:price-manipulation` | Tests for price manipulation through discount abuse, inventory exploits, or unauthorized price modifications |
| `excessive-agency` | Tests for unauthorized actions beyond defined system boundaries |
| `ferpa` | Tests for compliance with Family Educational Rights and Privacy Act |
| `financial:calculation-error` | Tests for errors in financial calculations, risk assessments, or quantitative analysis |
| `financial:compliance-violation` | Tests for suggestions that violate securities laws, enable insider trading, or circumvent regulations |
| `financial:confidential-disclosure` | Tests for inappropriate disclosure of MNPI, proprietary strategies, or confidential financial data |
| `financial:counterfactual` | Tests for false financial narratives or misleading market information |
| `financial:data-leakage` | Tests for exposure of proprietary trading strategies or confidential financial data |
| `financial:defamation` | Tests for false statements damaging financial entity reputations |
| `financial:hallucination` | Tests for fabricated market data, non-existent financial instruments, or fictional company information |
| `financial:impartiality` | Tests for unauthorized financial advice or transaction facilitation |
| `financial:japan-fiea-suitability` | Tests for unsuitable financial product recommendations or downplaying of risks under Japan's FIEA |
| `financial:misconduct` | Tests for facilitation of financial crimes or market manipulation |
| `financial:sox-compliance` | Tests for violations of Sarbanes-Oxley requirements including internal controls, financial reporting, and audit integrity |
| `financial:sycophancy` | Tests for agreeing with risky investment strategies or validating get-rich-quick schemes |
| `goal-misalignment` | Tests whether AI systems recognize when optimizing proxy metrics might not align with true goals (Goodhart's Law) |
| `hallucination` | Tests for fabrication of false or misleading information |
| `harmbench` | Tests for harmful content using the HarmBench dataset |
| `harmful:chemical-biological-weapons` | Tests handling of WMD-related content |
| `harmful:child-exploitation` | Tests handling of child exploitation content |
| `harmful:copyright-violations` | Tests handling of intellectual property violations |
| `harmful:cybercrime` | Tests handling of cybercrime-related content |
| `harmful:cybercrime:malicious-code` | Tests creation of malicious code |
| `harmful:graphic-content` | Tests handling of graphic or violent content |
| `harmful:harassment-bullying` | Tests handling of harassment and bullying content |
| `harmful:hate` | Tests handling of hate speech and discriminatory content |
| `harmful:illegal-activities` | Tests handling of general illegal activities |
| `harmful:illegal-drugs` | Tests handling of illegal drug-related content |
| `harmful:illegal-drugs:meth` | Tests handling of methamphetamine-related content |
| `harmful:indiscriminate-weapons` | Tests handling of weapons-related content |
| `harmful:insults` | Tests handling of personal attacks and insults |
| `harmful:intellectual-property` | Tests handling of IP theft and violations |
| `harmful:misinformation-disinformation` | Tests handling of false information campaigns |
| `harmful:non-violent-crime` | Tests handling of non-violent criminal content |
| `harmful:privacy` | Tests handling of privacy violation attempts |
| `harmful:profanity` | Tests handling of profane or inappropriate language |
| `harmful:radicalization` | Tests handling of extremist content and recruitment |
| `harmful:self-harm` | Tests handling of self-harm and suicide content |
| `harmful:sex-crime` | Tests handling of sexual crime content |
| `harmful:sexual-content` | Tests handling of explicit sexual content |
| `harmful:specialized-advice` | Tests handling of unauthorized professional advice |
| `harmful:unsafe-practices` | Tests handling of dangerous activity instructions |
| `harmful:violent-crime` | Tests handling of violent crime content |
| `harmful:weapons:ied` | Tests handling of Improvised Explosive Devices |
| `hijacking` | Tests for unauthorized resource usage and purpose deviation |
| `imitation` | Tests handling of unauthorized impersonation of entities |
| `indirect-prompt-injection` | Tests for injection vulnerabilities via untrusted variables |
| `insurance:coverage-discrimination` | Tests for discriminatory coverage decisions based on protected characteristics (age, disability, race, etc.) |
| `insurance:data-disclosure` | Tests for unauthorized disclosure of protected policyholder data including claims history, property details, driving records, and financial information |
| `insurance:network-misinformation` | Tests for inaccurate provider network information |
| `insurance:phi-disclosure` | Tests for unauthorized disclosure of Protected Health Information in violation of HIPAA privacy regulations |
| `intent` | Tests for manipulation of system behavior via specific prompts |
| `mcp` | Tests for vulnerabilities to Model Context Protocol (MCP) attacks |
| `medical:anchoring-bias` | Tests for medical anchoring bias where AI fixates on irrelevant information |
| `medical:fda:ai-disclosure` | Tests whether medical AI systems conceal intended-use limits, low-confidence outputs, subgroup caveats, data drift, or silent model updates |
| `medical:fda:cyber-access-control` | Tests whether medical-device AI systems enforce authenticated, role-scoped, deny-by-default access before privileged commands or therapy changes |
| `medical:fda:cyber-audit-tampering` | Tests whether medical-device AI systems suppress anomaly alerts, rewrite audit trails, hide SBOM/version evidence, or disable forensic logging |
| `medical:hallucination` | Tests for fabricated medical facts, studies, or drug interactions |
| `medical:incorrect-knowledge` | Tests for factually wrong medical information that could cause harm |
| `medical:off-label-use` | Tests for inappropriate off-label medication recommendations without proper disclaimers |
| `medical:prioritization-error` | Tests for poor medical prioritization and triage decisions |
| `medical:sycophancy` | Tests for agreeing with incorrect medical assumptions to be helpful |
| `model-identification` | Tests whether an AI system can be tricked into revealing its underlying model identity |
| `off-topic` | Tests whether AI systems can be manipulated to go off-topic from their intended purpose |
| `overreliance` | Tests for overreliance on system assumptions |
| `pharmacy:controlled-substance-compliance` | Tests adherence to DEA regulations for controlled substance prescribing, dispensing, and monitoring |
| `pharmacy:dosage-calculation` | Tests accuracy of pharmaceutical dosage calculations including weight-based dosing and renal adjustments |
| `pharmacy:drug-interaction` | Tests identification of dangerous drug-drug, drug-food, and drug-supplement interactions |
| `pii:api-db` | Tests for PII exposure via API/database access |
| `pii:direct` | Tests for direct PII exposure vulnerabilities |
| `pii:session` | Tests for PII exposure in session data |
| `pii:social` | Tests for PII exposure via social engineering |
| `pliny` | Tests handling of Pliny prompt injections |
| `policy` | Tests compliance with custom security policies |
| `politics` | Tests handling of political content and bias |
| `prompt-extraction` | Tests for system prompt disclosure vulnerabilities |
| `rag-document-exfiltration` | Tests for RAG document exfiltration |
| `rag-poisoning` | Tests for vulnerabilities to RAG retrieval poisoning attacks |
| `rag-source-attribution` | Tests for fabricated document citations in RAG systems |
| `rbac` | Tests role-based access control implementation |
| `realestate:accessibility-discrimination` | Tests for ADA and FHA disability accommodation violations in housing |
| `realestate:advertising-discrimination` | Tests for discriminatory targeting and language in housing advertisements |
| `realestate:discriminatory-listings` | Tests for discriminatory language in property listings and advertisements |
| `realestate:fair-housing-discrimination` | Tests for Fair Housing Act violations across all 7 protected classes |
| `realestate:lending-discrimination` | Tests for ECOA and FHA violations in mortgage lending including redlining and disparate treatment |
| `realestate:source-of-income` | Tests for Section 8 and housing voucher discrimination (state-specific protections) |
| `realestate:steering` | Tests for illegal steering practices directing buyers to/from neighborhoods based on demographics |
| `realestate:valuation-bias` | Tests for algorithmic bias in property appraisals and automated valuations |
| `reasoning-dos` | Tests for vulnerabilities to computational resource exhaustion through excessive reasoning patterns |
| `religion` | Tests handling of religious content and bias |
| `shell-injection` | Tests for command injection vulnerabilities |
| `special-token-injection` | Tests vulnerability to token injection attacks using format-specific delimiters |
| `sql-injection` | Tests for SQL injection vulnerabilities |
| `ssrf` | Tests for server-side request forgery vulnerabilities |
| `system-prompt-override` | Tests for system prompt override vulnerabilities |
| `teen-safety:age-restricted-goods-and-services` | Tests for enabling or normalizing underage access to alcohol, vaping, gambling, weapons, and other age-restricted goods or services |
| `teen-safety:dangerous-content` | Tests for dangerous activities, viral challenges, unsafe stunts, and dangerous at-home procedures inappropriate for teens |
| `teen-safety:dangerous-roleplay` | Tests for unsafe roleplay involving minors, including romantic, sexual, or violent interactive scenarios |
| `teen-safety:harmful-body-ideals` | Tests for harmful body ideals, body shaming, and enabling disordered eating or exercise behaviors that are unsafe for teens |
| `telecom:accessibility-violation` | Tests for accessibility compliance violations |
| `telecom:account-takeover` | Tests for SIM swap and account hijacking vulnerabilities |
| `telecom:billing-misinformation` | Tests for incorrect billing and pricing information |
| `telecom:coverage-misinformation` | Tests for false coverage or service claims |
| `telecom:cpni-disclosure` | Tests for unauthorized disclosure of Customer Proprietary Network Information |
| `telecom:e911-misinformation` | Tests for incorrect emergency calling information |
| `telecom:fraud-enablement` | Tests for telecom-specific fraud facilitation |
| `telecom:law-enforcement-request-handling` | Tests for improper law enforcement request handling |
| `telecom:location-disclosure` | Tests for unauthorized disclosure of customer location data |
| `telecom:porting-misinformation` | Tests for incorrect number portability information |
| `telecom:tcpa-violation` | Tests for TCPA consent and Do Not Call compliance |
| `telecom:unauthorized-changes` | Tests for slamming and cramming vulnerabilities |
| `tool-discovery` | Tests for enumeration of available tools and function calls |
| `toxic-chat` | Tests handling of toxic prompts from the ToxicChat dataset |
| `unsafebench` | Tests handling of unsafe image content from the UnsafeBench dataset |
| `unverifiable-claims` | Tests for claims that cannot be verified or fact-checked |
| `vlguard` | Tests handling of potentially unsafe image content from the VLGuard dataset |
| `vlsu` | Tests compositional safety where individually safe images and text combine to produce harmful outputs |
| `wordplay` | Tests whether AI systems can be tricked into generating profanity through wordplay |
| `xstest` | Tests for XSTest attacks |

---

## 7. Стратегии

### 7.1 Дефолтные (`DEFAULT_STRATEGIES`)

`basic`, `jailbreak:meta`, `jailbreak:composite` — применяются при `strategies: ['default']` или если ключ не задан.

### 7.2 Полный список (`ADDITIONAL_STRATEGIES` + коллекции + агентные)

`audio`, `authoritative-markup-injection`, `base64`, `best-of-n`, `camelcase`, `citation`, `crescendo`, `custom`, `emoji`, `gcg`, `goat`, `hex`, `homoglyph`, `image`, `indirect-web-pwn`, `jailbreak`, `jailbreak-templates`, `jailbreak:goblin`, `jailbreak:hydra`, `jailbreak:likert`, `jailbreak:meta`, `jailbreak:tree`, `layer`, `leetspeak`, `math-prompt`, `mischievous-user`, `morse`, `multilingual` (deprecated), `piglatin`, `prompt-injection` (deprecated → `jailbreak-templates`), `retry`, `rot13`, `video`, `other-encodings` (коллекция), плюс `basic`, `jailbreak:composite`, `default`.

Коллекция `other-encodings` = `camelcase`, `morse`, `piglatin`, `emoji`.

### 7.3 Многоходовые (`MULTI_TURN_STRATEGIES`)

`crescendo`, `goat`, `jailbreak:hydra`, `jailbreak:goblin`, `custom`, `mischievous-user`. По умолчанию 5 ходов на кейс.

`jailbreak:meta` в этот список **не входит** — он агентный, но одноходовый.

### 7.4 Агентные (`AGENTIC_STRATEGIES`)

`crescendo`, `goat`, `indirect-web-pwn`, `custom`, `jailbreak`, `jailbreak:goblin`, `jailbreak:hydra`, `jailbreak:meta`, `jailbreak:tree`, `mischievous-user`.

### 7.5 Требуют remote-генерации (`STRATEGIES_REQUIRING_REMOTE`)

`audio`, `citation`, `gcg`, `goat`, `indirect-web-pwn`, `jailbreak:composite`, `jailbreak:goblin`, `jailbreak:hydra`, `jailbreak:likert`, `jailbreak:meta`.

### 7.6 Ломающие детерминированное сравнение (`CANARY_BREAKING_STRATEGY_IDS`)

`base64`, `hex`, `homoglyph`, `leetspeak`, `rot13`, `multilingual`, `math-prompt`, `jailbreak:composite`.

Комментарий в исходнике: «Encoding strategies that mangle prompt text and break deterministic canary/receipt matching».

### 7.7 Настраиваемые (`CONFIGURABLE_STRATEGIES`)

`layer`, `best-of-n`, `goat`, `crescendo`, `indirect-web-pwn`, `jailbreak`, `jailbreak:composite`, `jailbreak:goblin`, `jailbreak:hydra`, `jailbreak:meta`, `jailbreak:tree`, `gcg`, `citation`, `custom`, `mischievous-user`.

### 7.8 Кодирующие (`ENCODING_STRATEGIES`)

`base64`, `hex`, `rot13`, `leetspeak`, `homoglyph`, `morse`, `atbash`, `piglatin`, `camelcase`, `emoji`, `reverse`, `binary`, `octal`, `audio`, `image`, `video`.

### 7.9 Деприкейт `multilingual`

Стратегия принимается для обратной совместимости, но при валидации её языки переносятся в верхнеуровневый `language` (плюс автоматически добавляется `en`), а сама стратегия удаляется из массива. Сообщение в логе: «The "multilingual" strategy is deprecated. Use the top-level "language" config instead».

---

## 8. Маппинг OWASP в версии 0.122.0

Именно этот маппинг делает выбор издания LLM Top 10 **2025** в [threat-model.md](./threat-model.md) §1 обязательным: `owasp:llm:07` резолвится в System Prompt Leakage.

### 8.1 OWASP LLM Top 10

| Алиас | Категория | Плагины | Стратегии |
|---|---|---|---|
| `owasp:llm:01` | Prompt Injection | `ascii-smuggling`, `indirect-prompt-injection`, `prompt-extraction`, `harmful` | `jailbreak`, `jailbreak-templates`, `jailbreak:composite` |
| `owasp:llm:02` | Sensitive Information Disclosure | `pii:api-db`, `pii:direct`, `pii:session`, `pii:social`, `harmful:privacy`, `cross-session-leak`, `prompt-extraction` | те же |
| `owasp:llm:03` | Supply Chain | **пусто** | — |
| `owasp:llm:04` | Data and Model Poisoning | `harmful:misinformation-disinformation`, `harmful:hate`, `bias:age`, `bias:disability`, `bias:gender`, `bias:race`, `harmful:radicalization`, `harmful:specialized-advice` | те же |
| `owasp:llm:05` | Improper Output Handling | `shell-injection`, `sql-injection`, `ssrf`, `debug-access` | `jailbreak`, `jailbreak-templates` |
| `owasp:llm:06` | Excessive Agency | `excessive-agency`, `rbac`, `bfla`, `bola`, `shell-injection`, `sql-injection`, `ssrf` | `jailbreak`, `jailbreak-templates`, `jailbreak:composite` |
| `owasp:llm:07` | System Prompt Leakage | `prompt-extraction`, `rbac`, `harmful:privacy`, `pii:api-db`, `pii:direct`, `pii:session`, `pii:social` | те же |
| `owasp:llm:08` | Vector and Embedding Weaknesses | `cross-session-leak`, `harmful:privacy`, `pii:api-db`, `pii:direct`, `pii:session`, `pii:social` | те же |
| `owasp:llm:09` | Misinformation | `hallucination`, `overreliance`, `harmful:misinformation-disinformation`, `harmful:specialized-advice` | те же |
| `owasp:llm:10` | Unbounded Consumption | `divergent-repetition`, `reasoning-dos` | — |

### 8.2 OWASP ASI Top 10 (агентные)

| Алиас | Категория | Плагины | Стратегии |
|---|---|---|---|
| `owasp:agentic:asi01` | Agent Goal Hijack | `hijacking`, `system-prompt-override`, `indirect-prompt-injection`, `intent` | `jailbreak`, `jailbreak-templates`, `jailbreak:composite` |
| `owasp:agentic:asi02` | Tool Misuse and Exploitation | `excessive-agency`, `mcp`, `tool-discovery` | `jailbreak`, `jailbreak-templates` |
| `owasp:agentic:asi03` | Identity and Privilege Abuse | `rbac`, `bfla`, `bola`, `imitation` | `jailbreak`, `jailbreak-templates` |
| `owasp:agentic:asi04` | Agentic Supply Chain | `indirect-prompt-injection`, `mcp` | `jailbreak-templates` |
| `owasp:agentic:asi05` | Unexpected Code Execution | `shell-injection`, `sql-injection`, `harmful:cybercrime:malicious-code`, `ssrf` | `jailbreak`, `jailbreak-templates` |
| `owasp:agentic:asi06` | Memory and Context Poisoning | `agentic:memory-poisoning`, `cross-session-leak`, `indirect-prompt-injection` | `jailbreak`, `crescendo` |
| `owasp:agentic:asi07` | Insecure Inter-Agent Communication | `indirect-prompt-injection`, `hijacking`, `imitation` | `jailbreak-templates` |
| `owasp:agentic:asi08` | Cascading Failures | `hallucination`, `harmful:misinformation-disinformation`, `divergent-repetition` | `jailbreak`, `jailbreak-templates` |
| `owasp:agentic:asi09` | Human-Agent Trust Exploitation | `overreliance`, `imitation`, `harmful:misinformation-disinformation` | `crescendo` |
| `owasp:agentic:asi10` | Rogue Agents | `excessive-agency`, `hijacking`, `rbac`, `goal-misalignment` | — |

### 8.3 Почему алиасы OWASP не используются в конфиге

Указание `owasp:llm:06` в `plugins` разворачивается в 7 плагинов, включая `shell-injection`, `sql-injection`, `ssrf` и `bola`/`bfla`, которые [threat-model.md](./threat-model.md) §7.2–7.3 признала неприменимыми. Поэтому в конфиге задачи 04 перечисляются **конкретные плагины**, а соответствие OWASP ведётся таблицей в [plugin-selection.md](./plugin-selection.md).
