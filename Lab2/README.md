# Лабораторная работа № 2 — Анализ сходства и оценка качества

**Траектория:** Python Core · **Уровень:** основной · **Курс:** «Библиотеки и фреймворки Python» · **Период:** октябрь 2026 г.

## Назначение

Продолжение проекта онлайн-школы из лабораторной работы № 1. Прототип сравнивает **учебные** решения на Python, выделяет пары для ручной проверки и предоставляет объяснимые результаты. Совпадение кода **не является доказательством плагиата**. Код студентов не выполняется.

## Структура

Модули находятся в `src/school/`:

| Модуль | Назначение |
|---|---|
| `streaming.py` | Потоковое чтение, проверка JSONL и генераторы |
| `features.py`, `similarity.py` | `tokenize`, токеновые 3-граммы и коэффициент Жаккара |
| `ast_similarity.py` | Структурные AST-признаки и нормализация имён |
| `candidates.py` | Фильтры кандидатов, разрешённые шаблоны, top-k и диапазоны строк |
| `corpus.py` | Детерминированный синтетический корпус |
| `evaluation.py` | Порог `review_required`, матрица ошибок, precision, recall, F1 |
| `error_analysis.py` | Анализ ложных срабатываний и ошибок |
| `performance.py`, `optimized_performance.py` | Измерения до/после оптимизации |
| `performance_report.py` | Сравнительный отчёт о производительности |
| `audit.py` | Проверка корпуса и диапазонов доказательств |
| `template_versioning.py` | Демонстрация новой версии разрешённого шаблона |

## Воспроизведение

Запускать команды из **корня проекта** (каталога `Lab1`) в активированном виртуальном окружении:

```powershell
python -m unittest discover -s tests -v
python -m src.school.corpus
python -m src.school.audit
python -m src.school.evaluation
python -m src.school.error_analysis
python -m src.school.performance --sizes 100 1000 5000 --repeats 3
python -m src.school.optimized_performance --sizes 100 1000 5000 --repeats 3
python -m src.school.performance_report
python -m src.school.template_versioning
```

Дополнительное профилирование (одна диагностическая итерация):

```powershell
python -m cProfile -o data/lab2/profile_optimized_1000.prof -m src.school.optimized_performance --sizes 1000 --repeats 1 --output data/lab2/profile_run_1000.json
python -c "import pstats; pstats.Stats('data/lab2/profile_optimized_1000.prof').strip_dirs().sort_stats('cumtime').print_stats(15)"
```

Для формирования `performance_report.md` необходимы предварительно созданные JSON-отчёты обеих версий. Команда версии `v2` использует `data/lab2/template_config_v2.json` и записывает результаты отдельно в `data/lab2/demo_v2/`.

## Корпус и проверка качества

Сгенерированы **30 синтетических сдач** из 10 семейств, 30 записей происхождения и **40 размеченных пар**; по 20 пар в наборах `tuning` и `evaluation`. Семейства не пересекаются между наборами. В корпусе 6 отрицательных пар с общим разрешённым шаблоном. Порог определяется только по `tuning`, метрики рассчитываются на `evaluation`.

Результат версии `v1` на 20 оценочных парах:

| Метод | Порог | Precision | Recall | F1 |
|---|---:|---:|---:|---:|
| Token | 0,1111 | 0,938 | 1,000 | 0,968 |
| AST | 1,0000 | 1,000 | 1,000 | 1,000 |

После демонстрационного изменения разрешённого шаблона (`v2`) меняются оценки 20 пар: F1 Token = 0,857; F1 AST = 0,929. Эти числа получены **на тех же синтетических исходных решениях**, а не на новых независимых данных.

## Выходные файлы

- `data/lab2/submissions.jsonl`, `provenance.jsonl`, `pairs.jsonl` — корпус и разметка;
- `data/lab2/evaluation_report.json` — метрики `v1`;
- `data/lab2/error_analysis.json`, `error_analysis.md` — анализ ошибок;
- `data/lab2/audit_report.json` — аудит;
- `data/lab2/performance_baseline.json`, `performance_optimized.json`, `performance_report.md` — производительность;
- `data/lab2/template_config_v2.json`, `demo_v2/evaluation_report_v2.json`, `demo_v2/changes_v1_v2.json` — демонстрация изменения шаблона.

## Ограничения

Это небольшой искусственный корпус; результаты нельзя переносить на реальные студенческие работы. Нормализация AST не покрывает все семантически эквивалентные преобразования. Система не принимает дисциплинарных решений. Нагрузочный эксперимент выполняет N сравнений с **одним фиксированным образцом**, а не полный перебор всех пар; `tracemalloc` измеряет выделения памяти Python, а не общую память процесса Windows.

Дополнительные сведения: `REPORT.md` и `AI_USAGE.md` в этой папке. История лабораторной № 1 сохраняется в корневых документах проекта.
