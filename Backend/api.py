import os
import asyncio
import uuid
import random
from app.scraper_manager import ScraperManager

from fastapi import APIRouter, BackgroundTasks, HTTPException
from fastapi.responses import FileResponse
from pathlib import Path
from pydantic import BaseModel
from typing import List
from loguru import logger

router = APIRouter()

log = logger.bind(context="API")

jobs = {}


class ScrapeRequest(BaseModel):
    urls: List[str]


async def process_url(
    job_id: str,
    url: str,
    delay: float = 0.0,
    limit: asyncio.Semaphore = asyncio.Semaphore(10),
):
    async with limit:
        jobs[job_id]["urls"][url] = "processing"
        if delay > 0:
            await asyncio.sleep(delay)
        manager = ScraperManager()
        try:
            result = await manager.scrape(url)
            jobs[job_id]["urls"][url] = "completed"
            return result
        except Exception as e:
            log.exception(f"Error scraping {url}: {e}")
            jobs[job_id]["urls"][url] = "failed"
            return {"error": str(e), "url": url}
        finally:
            await manager.close()


async def run(job_id: str, urls: List[str]):
    jobs[job_id]["status"] = "processing"
    results = []
    limit = asyncio.Semaphore(10)
    random_delay = random.uniform(0.0, 2.0)

    # Create tasks as before...
    tasks = [
        process_url(job_id=job_id, url=url, delay=random_delay, limit=limit)
        for url in urls
    ]
    # Use as_completed to update progress one by one
    for task in asyncio.as_completed(tasks):
        result = await task
        results.append(result)

    jobs[job_id]["status"] = "completed"
    # Wait until the end to store the heavy result data
    jobs[job_id]["data"] = results


@router.post("/scrape")
async def trigger_scrape(request: ScrapeRequest, background_tasks: BackgroundTasks):
    """
    Accepts a list of URLs, generates a job ID, and starts scraping in the background.
    """
    if not request.urls:
        log.warning("Received scrape request with no URLs")
        raise HTTPException(status_code=400, detail="No URLs provided")

    log.success(f"Received scrape request for {len(request.urls)} URLs")
    job_id = str(uuid.uuid4())
    jobs[job_id] = {
        "status": "pending",
        "urls": {url: "pending" for url in request.urls},
        "data": None,
        "error": None,
    }

    # Send the scraping task to the background
    background_tasks.add_task(run, job_id, request.urls)

    return {
        "job_id": job_id,
        "status": "pending",
        "message": f"Started scraping {len(request.urls)} URLs in the background.",
    }


@router.get("/results/{job_id}")
async def get_all_results():
    """
    Return a summary of ALL jobs for the frontend to poll once
    """
    return {
        job_id: {
            "status": info["status"],
            "urls": info.get("urls", {}),
            "error": info["error"],
        }
        for job_id, info in jobs.items()
    }


DATA_DIR = Path(__file__).resolve().parent


@router.get("/download")
async def download_jsonl(background_tasks: BackgroundTasks):
    """
    Returns the data.jsonl file as a downloadable attachment and deletes it after.
    """
    file_path = DATA_DIR / "data.jsonl"
    if not file_path.exists():
        raise HTTPException(
            status_code=404, detail="No data file found. Run a scrape job first."
        )

    log.success("Downloading data.jsonl")

    # Send the file and then delete it if no other jobs are active
    response = FileResponse(
        path=str(file_path),
        filename="data.jsonl",
        media_type="application/x-ndjson",
    )

    # Safety Check: Don't delete if another job is still writing to it
    is_any_job_active = any(
        job["status"] in ["pending", "processing"] for job in jobs.values()
    )
    if not is_any_job_active:
        background_tasks.add_task(os.remove, str(file_path))
        jobs.clear()  # Clear all jobs so the dashboard starts completely fresh
        log.info("File deletion scheduled & jobs cleared: No active jobs found.")
    else:
        log.warning("File deletion skipped: One or more jobs are currently active.")

    return response
