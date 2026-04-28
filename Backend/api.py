import os
import asyncio
import uuid
import random
from app.scraper_manager import ScraperManager

from fastapi import APIRouter, BackgroundTasks, HTTPException
from fastapi.responses import FileResponse, Response
from pathlib import Path
from pydantic import BaseModel
from typing import List
from loguru import logger

router = APIRouter()

log = logger.bind(context="API")

jobs = {}
download_lock = asyncio.Lock()



class ScrapeRequest(BaseModel):
    urls: List[str]


async def process_url(
    job_id: str,
    url_id: str,
    url: str,
    delay: float = 0.0,
    limit: asyncio.Semaphore = asyncio.Semaphore(10),
):
    async with limit:
        jobs[job_id]["urls"][url_id]["status"] = "processing"
        if delay > 0:
            await asyncio.sleep(delay)
        manager = ScraperManager()
        try:
            result = await manager.scrape(url)
            jobs[job_id]["urls"][url_id]["status"] = "completed"
            return result
        except Exception as e:
            log.exception(f"Error scraping {url}: {e}")
            if "Bot Blocked" in str(e):
                jobs[job_id]["urls"][url_id]["status"] = "Bot Blocked"
            elif "Wrong URL" in str(e):
                jobs[job_id]["urls"][url_id]["status"] = "Wrong URL"
            elif "LLM" in str(e):
                jobs[job_id]["urls"][url_id]["status"] = "LLM limit exceeded"
            else:
                jobs[job_id]["urls"][url_id]["status"] = "Failed"
            
            return {"error": jobs[job_id]["urls"][url_id]["status"], "url": url}

        finally:
            await manager.close()


async def run(job_id: str, urls: List[str], url_tracking: dict):
    jobs[job_id]["status"] = "processing"
    results = []
    limit = asyncio.Semaphore(10)
    random_delay = random.uniform(0.0, 2.0)

    # Create tasks as before...
    tasks = [
        process_url(job_id=job_id, url_id=url_id, url=info["url"], delay=random_delay, limit=limit)
        for url_id, info in url_tracking.items()
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
    
    # Store tracking by index so duplicate URLs don't overwrite each other
    url_tracking = {str(i): {"url": url, "status": "pending"} for i, url in enumerate(request.urls)}

    jobs[job_id] = {
        "status": "pending",
        "urls": url_tracking,
        "data": None,
        "error": None,
    }

    # Send the scraping task to the background
    background_tasks.add_task(run, job_id, request.urls, url_tracking)

    return {
        "job_id": job_id,
        "status": "pending",
        "message": f"Started scraping {len(request.urls)} URLs in the background.",
    }


@router.get("/results")
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
async def download_jsonl():
    """
    Returns the data.jsonl file as a downloadable attachment and deletes it after.
    Handles double-clicks gracefully by returning 204 if state was just cleared.
    """
    async with download_lock:
        file_path = DATA_DIR / "data.jsonl"
        if not file_path.exists():
            # If file is gone but jobs are cleared, it's likely a double-click
            if not jobs:
                log.info("Download requested but data already cleared. Returning 204.")
                return Response(status_code=204)
            
            raise HTTPException(
                status_code=404, detail="No data file found. Run a scrape job first."
            )

        log.success("Downloading data.jsonl")

        # Read the file into memory first to avoid race conditions with FileResponse
        content = file_path.read_bytes()

        is_any_job_active = any(
            job["status"] in ["pending", "processing"] for job in jobs.values()
        )
        if not is_any_job_active:
            file_path.unlink(missing_ok=True)
            jobs.clear()  
            log.info("File deleted & jobs cleared: No active jobs found.")

        return Response(
            content=content,
            media_type="application/x-ndjson",
            headers={"Content-Disposition": "attachment; filename=data.jsonl"},
        )

