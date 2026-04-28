from .browser_client import BrowserClient
from .parser import Parser
from .JSONStorage import JSONStorage
from .llm_extractor import LLMExtractor
from .datastore import DataStore
from loguru import logger


class ScraperManager:
    def __init__(self):
        self.browser_client = BrowserClient()
        self.parser = Parser()
        self.llm_extractor = LLMExtractor()
        self.json_storage = JSONStorage()
        self.datastore = DataStore()
        self.job_counter = 0

    async def scrape(self, url):
        """
        Coordinates the scraping pipeline for a single URL.
        Returns the structured data or an error.
        """
        self.job_counter += 1
        job_id = self.job_counter
        task_log = logger.bind(context="scraper_manager", url=url, job_id=job_id)

        # 1) Fetch
        try:
            html = await self.browser_client.fetch(url)
            if not html or len(html.strip()) == 0:
                raise ValueError(" Received empty HTML")
            task_log.info(f"[1/6]  Fetched HTML {len(html)} characters")
        except Exception as e:
            task_log.exception(f"Worker {job_id} aborted: Failed to fetch HTML")
            raise e # Propagation of "Bot Blocked" or "Wrong URL" from browser_client


        # 2) Parse
        try:
            parsed_text = await self.parser.parse(html)
            task_log.info(f"[2/6] Extracted {len(parsed_text)} characters of text")
        except Exception as e:
            task_log.exception(f"Worker {job_id} failed to extract text")
            raise Exception(f"Failed to parse text: {e}")


        # 3) Save cleaned text
        try:
            parsed_record = self.datastore.save_parsed_data(parsed_text)
            task_log.info("[3/6] Saved cleaned text to DB")
        except Exception as e:
            task_log.exception("[3/6] Failed to save cleaned text to DB")
            raise Exception(f"Database error: {e}")


        # 4) LLM Extract
        try:
            data = await self.llm_extractor.make(parsed_text, url)
            task_log.info("[4/6] LLM Extraction completed")
        except Exception as e:
            task_log.exception("[4/6] Failed to extract structured JSON from LLM")
            raise Exception(f"LLM extraction error: {e}")


        # 5) Save data extracted data to JSONL
        try:
            await self.json_storage.save_jsonl(data)
            task_log.info("[5/6] Saved structured JSON to File: data.jsonl")
        except Exception as e:
            task_log.exception(
                "[5/6] Failed to save structured JSON to File: data.jsonl"
            )
            raise Exception(f"File storage error: {e}")


        # 6) Save extracted data to DB
        try:
            self.datastore.save_llm_extraction(parsed_record.id, data, url)
            task_log.info("[6/6] Saved structured JSONL to DB")
        except Exception as e:
            task_log.exception("[6/6] Failed to save structured JSONL to DB")
            raise Exception(f"Database extraction save error: {e}")


        task_log.success(f"Worker {job_id} has completed all operations successfully")
        return data

    async def close(self):
        await self.browser_client.close()
