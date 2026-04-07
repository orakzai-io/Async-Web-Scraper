# Backend - Async Web Scraper API

A high-performance **FastAPI** service coordinating an asynchronous database-driven web scraping and AI extraction pipeline.
## Project Structure & Core Classes

The backend is organized into a modular pipeline, with each file and class having a dedicated responsibility.

### Root Files

- **`main.py`**: The application entry point. 
    - Handles **FastAPI** initialization and lifespan management.
    - Configures **Loguru** for structured logging and sets up **CORS** middleware.
    - Runs the **Uvicorn** server.
- **`api.py`**: The interface layer.
    - Defines the **APIRouter** and endpoints (`/scrape`, `/results`, `/download`).
    - Manages in-memory job state and initiates **BackgroundTasks** for asynchronous execution.
    - Coordinates the `run()` loop for processing a batch of URLs.

### App Module (`app/`)

- **`scraper_manager.py` (`ScraperManager`)**: The orchestrator.
    - Coordinates the full 6-stage scraping pipeline (Fetch -> Parse -> DB Store -> LLM -> JSONL -> DB Store).
    - Interfaces between all the specialized modules.
- **`browser_client.py` (`BrowserClient`)**: The fetching layer.
    - Uses **`curl_cffi`** to fetch HTML while impersonating modern browser fingerprints (TLS/HTTP2) to bypass bot protection.
- **`parser.py` (`Parser`)**: The content engine.
    - Leverages **`trafilatura`** to extract clean, structured text from raw HTML.
    - Includes token-counting logic using **`tiktoken`**.
- **`llm_extractor.py` (`LLMExtractor`)**: The AI intelligence.
    - Interfaces with **Groq** to transform raw text into structured JSON based on user-defined prompts.
    - Implements **`tenacity`** retry logic for robust AI interactions.
- **`datastore.py` (`DataStore`)**: The database manager.
    - Handles all **SQLAlchemy** operations, including saving parsed content and structured extractions to PostgreSQL.
- **`models.py` & `database.py`**: The data foundation.
    - Defines the relational schema (`ParsedData`, `LlmExtraction`) and sets up the database engine/session management.
- **`JSONStorage.py` (`JSONStorage`)**: File persistence.
    - Asynchronously appends structured results to a local `.jsonl` file using **`aiofiles`**.

---
[Return to Root Project README](../README.md)
