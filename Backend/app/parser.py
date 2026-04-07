import asyncio
import trafilatura
import tiktoken

_TOKENIZER = tiktoken.get_encoding("cl100k_base")


def count_tokens(text):
    tokens = _TOKENIZER.encode(text)
    return len(tokens) + 1


class Parser:
    def __init__(self):
        pass

    async def parse(self, html: str) -> str:
        """
        Extracts clean text from HTML asynchronously using a thread pool.
        """
        if not html:
            return ""

        # trafilatura is synchronous/CPU-bound, so we run it in a thread
        content = await asyncio.to_thread(
            trafilatura.extract,
            html,
            output_format="markdown",
            favor_recall=True,
            include_comments=True,
            include_links=True,
        )

        result = content if content else ""
        token = count_tokens(result)
        if token > 4000:
            tokens = _TOKENIZER.encode(result)
            trimmed = tokens[:4000]
            return _TOKENIZER.decode(trimmed)

        return result
