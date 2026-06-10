# Validation Sample (~10%) — v1

Ревью: естественность `input`, корректность `answer_key_points`, соответствие политикам (G4 демо, B2B≠B2C checkout).

## B2C (7)

### `b2c-objection-m02`
- **type:** b2c-objection | **group:** G4 / **cat:** G4.1 | **source:** extraction | **turn:** multi
- **input:** можете показать какие то отрывки материалов прошлого курса? пока не понимаю что за предмет вы преподаете. стоит ли плати…
- **key_points:** публичного демо и отрывков уроков нет; кратко описать содержание программ из каталога (agents, fullstack, intensive и др.); не обещать ссылку на демо и не отсылать только к возврату; мягко уточнить, какой курс интересует
- **tools:** search_knowledge_base
- **must_not:** ['обещать прислать фрагмент урока', 'выдуманный URL превью']

### `b2c-syn-tools-001`
- **type:** b2c-tools | **group:** G9 / **cat:** G9.1 | **source:** synthetic | **turn:** single
- **input:** Решил, беру agents. Как оплатить?
- **key_points:** создать мок-ссылку на оплату для agents; кратко подтвердить выбор продукта
- **tools:** list_b2c_products, create_payment_link

### `b2c-rag-001`
- **type:** b2c-rag | **group:** G1 / **cat:** G1.1 | **source:** extraction | **turn:** single
- **input:** Добрый день. Заинтересовал комбо курс. Скажите, какой формат у курсов? Можно будет проходить в свое удобное время? Или е…
- **key_points:** формат онлайн с практическими заданиями и учебным репозиторием; комбо включает agents, deep-agents, fullstack-aidd и vibe-coding-intensive; можно проходить в своём темпе, есть поддержка в чате курса; консультация с экспертом — отдельный продукт consultation
- **tools:** search_knowledge_base

### `b2c-syn-segment-001`
- **type:** b2c-segment | **group:** G7 / **cat:** G7.2 | **source:** synthetic | **turn:** single
- **input:** Нужно обучить 30 инженеров в компании, есть бюджет на корпоративный договор. Вы делаете такое?
- **key_points:** распознать B2B: команда, компания, договор; не предлагать 30 покупок через B2C checkout; маршрут: корпоративное обучение / consultation / бриф; кратко форматы B2B из KB
- **tools:** search_knowledge_base

### `b2c-product-001`
- **type:** b2c-product | **group:** G2 / **cat:** G2.2 | **source:** extraction | **turn:** single
- **input:** Привет. У меня вопрос про интеснив. По каким дням и во сколько семинары?
- **key_points:** распознать запрос как интенсив по Cursor; дать структуру: созвоны, практика, поддержка в чате; при необходимости уточнить, что речь о vibe-coding-intensive
- **tools:** list_b2c_products, search_knowledge_base

### `b2c-syn-rag-003`
- **type:** b2c-rag | **group:** G9 / **cat:** G9.1 | **source:** synthetic | **turn:** single
- **input:** Есть ли рассрочка на комбо?
- **key_points:** на MVP оплата через демо-мок-ссылку; не обещать реальную рассрочку и платёжные провайдеры как доступные сейчас; в production планируются провайдеры — если уместно упомянуть из FAQ
- **tools:** search_knowledge_base
- **must_not:** ['обещать рассрочку сейчас', 'назвать конкретный банк']

### `b2c-objection-m01`
- **type:** b2c-objection | **group:** G3 / **cat:** G3.2 | **source:** extraction | **turn:** multi
- **input:** Нет так со мной не сработает. Я знаю что я не посмотрю в итоге видео. Синхрон это важно. Есть более привычные форматы — …
- **key_points:** признать, что записи не подходят пользователю; не настаивать на async как основном решении; предложить альтернативу: поток с вечерним или выходным расписанием; не обещать конкретные даты без данных из KB
- **tools:** search_knowledge_base

## B2B (2)

### `b2b-syn-segment-001`
- **type:** b2b-segment | **group:** G7 / **cat:** G7.2 | **source:** synthetic | **turn:** single
- **input:** Хотим заказать разработку sales-бота с RAG под наш каталог — это обучение или разработка?
- **key_points:** заказная разработка B2B, не корпоративный курс; типовой проект: публичный sales-бот с RAG; процесс: discovery, прототип LangChain+MCP+Langfuse, hardening; не предлагать B2C checkout
- **tools:** search_knowledge_base

### `b2b-nurture-m01`
- **type:** b2b-nurture | **group:** G8 / **cat:** G8.4 | **source:** extraction | **turn:** multi
- **input:** Сегодня повторно уточню и вернусь к вам.
- **key_points:** принять объяснение задержки без давления; контактное лицо ≠ финальный заказчик — это нормально; поблагодарить и подтвердить готовность ждать; не путать задержку с отказом…
