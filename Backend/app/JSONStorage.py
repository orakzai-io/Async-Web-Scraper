import json
import aiofiles
import asyncio


class JSONStorage:
    def __init__(self):
        # The Lock ensures that multiple async tasks don't
        # write to the same file at the exact same time.
        self._lock = asyncio.Lock()

    async def save_jsonl(self, new_data, path="data.jsonl"):
        """
        Asynchronously appends a single dictionary as a JSON line.
        Strictly UTF-8 for global character support.
        """
        async with self._lock:
            try:
                async with aiofiles.open(path, mode="a", encoding="utf-8") as f:
                    # ensure_ascii=False keeps your UTF-8 characters readable
                    line = json.dumps(new_data, ensure_ascii=False)
                    await f.write(line + "\n")
            except Exception as e:
                print(f"❌ Storage Error: {e}")

    async def load_all(self, path="data.jsonl"):
        """
        Reads the JSONL file and returns a list of dictionaries.
        """
        data = []
        try:
            async with aiofiles.open(path, mode="r", encoding="utf-8") as f:
                async for line in f:
                    if line.strip():
                        data.append(json.loads(line))
        except FileNotFoundError:
            pass
        return data
