from groq import AsyncGroq, RateLimitError
from dotenv import load_dotenv
import os
import json
import logging
from tenacity import retry, wait_exponential, retry_if_exception_type
import datetime

load_dotenv()
client = AsyncGroq(api_key=os.getenv("GROQ_API_KEY"))

logger = logging.getLogger(__name__)

system_prompt = """
<role>You are a highly analytical web content extractor and structured data synthesizer.</role>

<task>
Analyze the provided content using step-by-step reasoning, then extract structured data.
You MUST handle noisy, incomplete, or poorly formatted text gracefully.
</task>

<Meta_reasoning>
Select exactly one schema based on the content type.
If the page mixes content types, use the dominant one and ignore secondary noise.
Prefer completeness over brevity, but never invent missing facts.
If the content is ambiguous, choose the safest minimal structure rather than guessing.
Before finalizing, verify that every item fits the chosen schema and that the JSON is parseable.
</Meta_reasoning>

<analysis_of_content>
Before extracting, think through these steps:

1. CONTENT IDENTIFICATION & NOISE CANCELLATION
   - What kind of content is this? Use your judgement to analyse the source_url and the content and give it a reasonable suitable most appropriate name such as  products, articles etc 
   - What is the most useless unnecessary gibberish  data  in this content? Identify noise and ignore it such as navigation links, cookie banners, footers, and sidebars.

2. KEY ELEMENTS DETECTION
   - Isolate the most important data points.
   - what is the most important data points in this content? For lists/products: capture name, price, rating, stats, etc.
   - and for articles: capture main text, author, publication date

3. STRUCTURE PLANNING & EDGE CASES
   - what is the most appropriate structure for this content? 
   - Standardize missing fields to `null`.
   - Ensure numbers, prices, or dates are consistently formatted where possible.
   - If the main content is empty, provide a valid but empty items list.
</analysis_of_content>

<Example_output_format>
{
  "content_type": "product | article | listing | table | social | search_results",
  "source_url": "https://example.com",
  "items": [
    {
      "// IF product": {
        "title": "Exact name of product",
        "price": 29.99,
        "currency": "USD",
        "availability": "in_stock | out_of_stock | preorder",
        "brand": "Brand Name",
        "sku": "Unique Identifier",
        "rating": 4.5,
        "review_count": 120,
        "images": ["https://url.com"],
        "link": "https://url.com",
        "specs": { "color": "red", "size": "XL" }
      },
      "// IF article": {
        "title": "Article Headline",
        "author": "Author Name",
        "published_date": "YYYY-MM-DD",
        "category": "Technology",
        "summary": "Short snippet or TL;DR",
        "main_content": "Full markdown-formatted body text",
        "article_links": ["https://external.com"],
        "word_count": 850
      },
      "// IF listing (Jobs/Real Estate)": {
        "title": "Job Title or Property Name",
        "organization": "Company or Agency",
        "location": "City, State/Remote",
        "price": { "value": 150000, "max_value": 180000, "currency": "USD", "is_range": true },
        "posted_date": "YYYY-MM-DD",
        "employment_type": "Full-time | Contract",
        "requirements": ["Skill 1", "Skill 2"],
        "apply_link": "https://url.com"
      },
      "// IF table": {
        "table_title": "Name of the table",
        "headers": ["Column 1", "Column 2"],
        "rows": [["Value A1", "Value B1"], ["Value A2", "Value B2"]],
        "row_count": 2
      },
      "// IF social": {
        "handle": "@username",
        "display_name": "User Name",
        "body": "Post content text",
        "timestamp": "ISO 8601 Timestamp",
        "engagement": { "likes": 10, "reposts": 5, "replies": 2 },
        "media_urls": ["https://url.com"]
      }
    }
  ],
  "metadata": {
    "total_items": 0,
    "scraped_at": "2025-03-28T14:30:00Z",
    "notes": "Any extraction issues or null field explanations"
  }
}
</Example_output_format>

<instructions>
- add https to the links if not present
- avoid duplication unless very important
- Make sure that the response is in JSON format
- Use null for missing fields.
- Adapt structure to match the detected content type.
- Do NOT output any conversational text.
</instructions>
"""


class LLMExtractor:
    def __init__(self, blacklist_path="app/blacklist.json"):
        self._client = client
        self.blacklist_path = blacklist_path
        self.Available_models = [
            "llama-3.3-70b-versatile",
            "llama-3.1-8b-instant",
            "moonshotai/kimi-k2-instruct-0905",
            "moonshotai/kimi-k2-instruct",
            "qwen/qwen3-32b",
            "meta-llama/llama-4-scout-17b-16e-instruct",
            "allam-2-7b",
            "openai/gpt-oss-120b",
            "openai/gpt-oss-20b",
        ]

        # Initialize blacklist by loading from file and cleaning old dates
        self.Blacklisted_models = self._load_blacklist()
        self._cleanup_old_dates()

        # Filter models already blacklisted today
        today = self._get_date()
        if today in self.Blacklisted_models:
            for model in self.Blacklisted_models[today]:
                if model in self.Available_models:
                    self.Available_models.remove(model)

    def _get_date(self):
        return datetime.datetime.now().strftime("%Y-%m-%d")

    def _load_blacklist(self):
        if os.path.exists(self.blacklist_path):
            try:
                with open(self.blacklist_path, "r") as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to load blacklist: {e}")
        return {}

    def _cleanup_old_dates(self):
        """Remove all dates except today from blacklist"""
        today = self._get_date()

        # Keep only today's blacklist, remove all old dates
        dates_to_remove = [
            date for date in self.Blacklisted_models.keys() if date != today
        ]

        for old_date in dates_to_remove:
            del self.Blacklisted_models[old_date]

        # Save the cleaned blacklist if we removed anything
        if dates_to_remove:
            self._save_blacklist()
            logger.info(
                f"🧹 Cleaned up {len(dates_to_remove)} old date(s) from blacklist: {dates_to_remove}"
            )

    def _save_blacklist(self):
        try:
            with open(self.blacklist_path, "w") as f:
                json.dump(self.Blacklisted_models, f, indent=4)
        except Exception as e:
            logger.error(f"Failed to save blacklist: {e}")

    @retry(
        wait=wait_exponential(multiplier=2, min=4, max=30),
        retry=retry_if_exception_type((RateLimitError, Exception)),
        reraise=True,
    )
    async def model_manager(self, raw_text, url):
        today = self._get_date()

        # Reload blacklist to get latest state (in case updated by another instance)
        self.Blacklisted_models = self._load_blacklist()
        self._cleanup_old_dates()

        if today not in self.Blacklisted_models:
            self.Blacklisted_models[today] = []

        while True:
            if not self.Available_models:
                raise RuntimeError("All models have exhausted their daily quotas!")

            current_model = self.Available_models[0]
            try:
                response = await self._client.chat.completions.create(
                    model=current_model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {
                            "role": "user",
                            "content": f"CONTENT: {raw_text}, SOURCE_URL: {url}",
                        },
                    ],
                    response_format={"type": "json_object"},
                )
                return response.choices[0].message.content

            except RateLimitError as e:
                error_msg = str(e).lower()
                # handling TPD and RPD errors (Daily Limits)
                if ("tpd" in error_msg) or ("rpd" in error_msg):
                    if current_model in self.Available_models:
                        self.Blacklisted_models[today].append(current_model)
                        self.Available_models.remove(current_model)
                        self._save_blacklist()
                        logger.warning(
                            f"❌ Daily Rate Limit: Blacklisted {current_model}. {len(self.Blacklisted_models[today])} models out for today."
                        )
                    continue

                if "tpm" in error_msg or "rpm" in error_msg:
                    # Minute Limit: Rotate to the back of the queue
                    failed_model = self.Available_models.pop(0)
                    self.Available_models.append(failed_model)
                    new_model = self.Available_models[0]
                    logger.warning(
                        f"⏳ Minute Limit hit for {failed_model}. Rotating to {new_model}."
                    )
                    continue
                raise e

            except Exception as e:
                logger.error(f"LLM generation failed for {current_model}: {e}")
                raise e

    async def make(self, raw_text: str, url: str):
        if not raw_text or not raw_text.strip() or not url:
            return {"error": "Empty text provided"}

        raw_json = await self.model_manager(raw_text, url)
        try:
            return json.loads(raw_json)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM Response as JSON: {e}")
            return {"error": "Invalid LLM output", "raw": raw_json}
