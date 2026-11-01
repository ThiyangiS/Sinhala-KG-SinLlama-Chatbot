# Sinhala KG + SinLlama Chatbot

Research prototype for a Sinhala tourism question-answering chatbot using **Neo4j graph retrieval** and (in a later stage) **SinLlama**. The current implementation covers graph construction, enrichment, Sinhala question processing, and experimental comparison of retrieval strategies. **SinLlama is not yet integrated. No frontend, vector database, or embeddings are used.**

## Current progress

- One Sinhala source document: Ella tourism information (23 sections).
- Initial manually verified extraction: 14 entities and 13 relationships in `data/extracted/`.
- Extended local graph: **25 entity nodes and 27 relationships** in an otherwise empty database.
- Retrieval strategies studied: 0-hop, 1-hop, 2-hop, relationship-aware; plus multi-entity comparison.
- Experimental evidence metrics: precision, recall, F1, evidence completeness, and query time.
- Preliminary six-question experiment: relationship-aware queries achieved mean F1 **0.568**, compared with 0-hop **0.234**, 1-hop **0.192**, and 2-hop **0.110**. The focused queries are a manually specified *oracle baseline*, not yet automatic query routing. Small sample results are not general chatbot accuracy.

## Prerequisites

- Windows with Neo4j Desktop 2 (local instance running)
- Python 3.13.3 (used in development) with a virtual environment
- VS Code with Python and Jupyter extensions
- Git / GitHub Desktop

## First-time setup (each team member)

1. **Clone** this repository using GitHub Desktop. Open the repository root in VS Code.
2. **Install Neo4j Desktop**, create a local instance (e.g. `Sinhala-KG-Chatbot`), choose a password, and **Start** it.
3. Confirm the **connection URI** shown by Desktop. The usual local address is `bolt://127.0.0.1:7687` (adjust if Desktop uses another port).
4. Open a VS Code terminal **in the repository root** and create the environment:

   ```powershell
   py -3.13 -m venv .venv
   .\.venv\Scripts\Activate.ps1
   python -m pip install --upgrade pip
   python -m pip install -r requirements.txt
   ```

   If `py -3.13` is unavailable but `python` points to a compatible interpreter, use `python -m venv .venv`.
5. Create `.env` in the repository root (do not commit it):

   ```dotenv
   NEO4J_URI=bolt://127.0.0.1:7687
   NEO4J_USER=neo4j
   NEO4J_PASSWORD=REPLACE_WITH_LOCAL_PASSWORD
   NEO4J_DATABASE=neo4j
   ```

6. Select `.venv` as the notebook kernel in VS Code.
7. Ensure `data/extracted/entities.csv` and `data/extracted/relationships.csv` exist. These are outputs from the initial extraction notebook; team members do **not** need the original restricted source document merely to reconstruct the pilot graph.
8. **Rebuild the same pilot graph** by running from the repository root:

   ```powershell
   python setup_graph.py
   ```

   This script uses `MERGE` and stable IDs. It loads the initial CSVs, adds the documented enrichment facts, and attaches a starter set of source-evidence strings. It is safe to rerun for these known IDs, but it can update existing property values.
9. Open Neo4j Query and verify:

   ```cypher
   MATCH (n:Entity) RETURN count(n) AS entity_nodes;
   MATCH (:Entity)-[r]->(:Entity) RETURN count(r) AS relationships;
   MATCH p=(n:Destination {id:'D001'})-[:LOCATED_IN]->(:District)-[:PART_OF]->(:Province) RETURN p;
   ```

   Expected in a fresh instance: **25 entity nodes and 27 relationships**.

## Existing notebook order

| Notebook | Purpose | Run again when? |
|---|---|---|
| `01_neo4j_connection.ipynb` | Test Neo4j connection | On initial setup / troubleshooting |
| `02_document_extraction.ipynb` | Load Ella Sinhala document, extract initial CSVs | Only when rebuilding the extraction from source (requires local source document) |
| `03_graph_construction.ipynb` | Original graph insertion experiment | Not required after `setup_graph.py` |
| `04_retrieval_experiments.ipynb` | Retrieval strategies, benchmarks and evaluation (check actual cells) | When repeating evaluation |
| `05_sinhala_question_processing.ipynb` | Rule-based intent and entity matching | When developing/testing question processing |

**Note:** Earlier development notes referred to separate notebook names/numbers. This README follows the current VS Code screenshot. Before merging, confirm every notebook's actual content and cell dependencies. The `setup_graph.py` script replaces the need to execute all graph creation/enrichment cells in order.

## Daily workflow

1. Start the Neo4j Desktop local instance.
2. Open the repository in VS Code and select the `.venv` Jupyter kernel.
3. Run only the notebook setup/import/function cells needed for the task. Do **not** need to rebuild the graph daily.
4. Save experiment results to `results/` and commit appropriate code / results on a feature branch.
5. Stop the instance when finished.

## Expected repository structure

```text
data/               # raw source data (private) and extracted CSVs
docs/               # research and experiment notes
graph/              # schema and Cypher files
notebooks/          # Jupyter experiments
results/            # evaluation CSVs
src/                # reusable Python modules (future)
tests/              # automated tests (future)
setup_graph.py      # reproducible Ella pilot graph construction
requirements.txt
.env.example
README.md
```

## Project safety and collaboration

- Never commit `.env`, passwords, credentials, database dumps containing secrets, or the `.venv` folder.
- Share the original Sinhala documents only with authorization. Keep raw files in `data/raw/` outside version control unless explicitly approved.
- GitHub shares **code and extracted files**, not the running Neo4j database; each team member must run the setup script locally.
- Work on feature branches and open pull requests into `main`.
- Training / generation with SinLlama on Colab is a **future integration**. Colab cannot access the local machine's `localhost` directly. A reachable database such as authorized AuraDB, or a separately secured connection setup, will be required.

## Troubleshooting

- **Connection refused:** Ensure Desktop instance is Running, confirm the URI/port, and test `Test-NetConnection 127.0.0.1 -Port 7687` in PowerShell.
- **Routing discovery error:** For one local instance, try direct `bolt://127.0.0.1:7687` in `.env`.
- **Credentials error:** Verify the *local* Neo4j password, not an AuraDB password.
- **CSV missing:** Check `data/extracted/` or generate the initial CSVs from the extraction notebook.
- **Notebook import error:** Verify `.venv` kernel and `pip install -r requirements.txt`.

## Next milestones

1. Improve entity alias handling and Sinhala intent classification.
2. Map intents and entities automatically to parameterized Cypher templates.
3. Evaluate query routing separately from oracle relationship-aware retrieval.
4. Add the other two Sinhala documents, extend source provenance and QA tests.
5. Integrate SinLlama to produce grounded Sinhala answers and measure answer quality.
