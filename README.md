# nl2sql_validation

nl2sql-evaluation-framework/
│
├── README.md
├── pyproject.toml
├── .env.example
├── .gitignore
│
├── config/
│   ├── database.yaml
│   └── evaluation.yaml
│
├── datasets/
│   ├── basic.yaml
│   ├── aggregation.yaml
│   ├── joins.yaml
│   ├── temporal.yaml
│   ├── ambiguity.yaml
│   ├── adversarial.yaml
│   └── regression.yaml
│
├── src/
│   └── nl2sql_eval/
│       ├── __init__.py
│       │
│       ├── models/
│       │   ├── test_case.py
│       │   ├── evaluation.py
│       │   └── schema.py
│       │
│       ├── generators/
│       │   └── nl2sql.py
│       │
│       ├── validators/
│       │   ├── syntax.py
│       │   ├── safety.py
│       │   └── schema.py
│       │
│       ├── executors/
│       │   └── postgres.py
│       │
│       ├── evaluators/
│       │   ├── result.py
│       │   ├── semantic.py
│       │   └── sql.py
│       │
│       ├── retrieval/
│       │   ├── schema_retriever.py
│       │   └── qdrant_store.py
│       │
│       ├── metrics/
│       │   └── metrics.py
│       │
│       └── pipeline.py
│
├── tests/
│   ├── unit/
│   ├── integration/
│   └── regression/
│
├── reports/
│
├── app/
│   └── streamlit_app.py
│
└── scripts/
    ├── run_evaluation.py
    └── seed_database.py


Question
   ↓
NL2SQL Generator
   ↓
Generated SQL
   ↓
SQLGlot Syntax Check
   ↓
Safety Check
   ↓
PostgreSQL Execution
   ↓
Expected Result Comparison
   ↓
PASS / FAIL