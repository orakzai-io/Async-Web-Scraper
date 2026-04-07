# AI-Powered Async Web Scraper

A professional, high-concurrency web scraping pipeline that extracts clean text from URLs, processes it through an LLM (Groq), and stores the structured results in both JSONL and PostgreSQL.

##  Quick Start (Docker)

The easiest way to run the entire stack is using Docker Compose:

1.  **Configure Environment**:
    Create a `.env` file in the `Backend` directory with your Groq API Key:
    ```bash
    GROQ_API_KEY=your_key_here
    DB_PASSWORD=your_db_password
    ```

2.  **Launch**:
    ```bash
    docker-compose up -d
    ```

3.  **Access**:
    - **Frontend**: [http://localhost](http://localhost)
    - **Backend API**: [http://localhost:8000](http://localhost:8000)

## Architecture

- **Frontend**: A modern dashboard built with **Vite** and **TypeScript** for real-time job monitoring and result downloads.
- **Backend**: A high-performance **FastAPI** service managing an asynchronous scraping pipeline.
- **Database**: **PostgreSQL** for persistent storage of parsed text and structured AI extractions.
- **Scraper**: Uses `curl_cffi` for advanced request impersonation to bypass bot detection.
- **Parser**: Leverages `trafilatura` for high-quality main-content extraction.
- **Extraction**: Integrates with **Groq** for lightning-fast LLM-based data structuring.


##  Project Structure

- `Backend/`: FastAPI application, database models, and scraper logic.
- `Frontend/`: Vite/TS dashboard for job status tracking and results visualization.
- `docker-compose.yml`: Orchestration for the frontend, backend, and persistence layers.

---
For detailed setup and development instructions, see the individual component's documentation:
- [Backend Documentation](./Backend/README.md)
- [Frontend Documentation](./Frontend/README.md)
