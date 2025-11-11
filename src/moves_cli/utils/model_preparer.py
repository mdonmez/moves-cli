import asyncio
import shutil
from pathlib import Path

import httpx
import xxhash
from rich.console import Console
from rich.progress import (
    BarColumn,
    DownloadColumn,
    Progress,
    SpinnerColumn,
    TaskProgressColumn,
    TextColumn,
)

from moves_cli.data.models import EmbeddingModel, SttModel

CHUNK_SIZE = 65536
HTTP_TIMEOUT = 30.0
MODELS = [EmbeddingModel, SttModel]

console = Console(highlight=False, color_system=None)


def _has_valid_checksum(filepath: Path, expected: str) -> bool:
    try:
        hasher = xxhash.xxh3_64()
        with filepath.open("rb") as f:
            for chunk in iter(lambda: f.read(CHUNK_SIZE), b""):
                hasher.update(chunk)
        return hasher.hexdigest() == expected
    except (OSError, IOError):
        return False


def _clean_model_directory() -> None:
    models_base_path = MODELS[0].model_dir.parent
    if not models_base_path.exists():
        return

    valid_paths = set()
    for model in MODELS:
        valid_paths.add(model.model_dir)
        valid_paths.update(model.model_dir / filename for filename in model.files)

    invalid = set(models_base_path.rglob("*")) - valid_paths

    for path in invalid:
        try:
            if path.is_file():
                path.unlink()
            elif path.is_dir():
                shutil.rmtree(path, ignore_errors=True)
        except (OSError, IOError):
            pass


async def _download_file(
    client: httpx.AsyncClient,
    url: str,
    filepath: Path,
    checksum: str,
    progress: Progress,
) -> None:
    if _has_valid_checksum(filepath, checksum):
        return

    task_id = progress.add_task(filepath.name, total=None)
    temp_path = filepath.with_suffix(filepath.suffix + ".tmp")

    try:
        async with client.stream("GET", url) as response:
            response.raise_for_status()
            progress.update(
                task_id, total=int(response.headers.get("content-length", 0))
            )

            filepath.parent.mkdir(parents=True, exist_ok=True)
            with temp_path.open("wb") as f:
                async for chunk in response.aiter_bytes():
                    f.write(chunk)
                    progress.advance(task_id, len(chunk))

        temp_path.replace(filepath)

        if not _has_valid_checksum(filepath, checksum):
            progress.update(task_id, description=f"Corrupt: {filepath.name}")
            filepath.unlink(missing_ok=True)
            raise RuntimeError(f"Checksum mismatch: {filepath.name}")

    except Exception as e:
        progress.update(task_id, description=f"Failed: {filepath.name}")
        temp_path.unlink(missing_ok=True)
        raise RuntimeError(f"Download failed: {url}") from e


async def prepare_models() -> bool:
    _clean_model_directory()

    async with httpx.AsyncClient(timeout=HTTP_TIMEOUT, follow_redirects=True) as client:
        with Progress(
            SpinnerColumn(),
            TextColumn("  [progress.description]{task.description}"),
            BarColumn(),
            DownloadColumn(),
            TaskProgressColumn(),
            console=console,
        ) as progress:
            tasks = [
                _download_file(
                    client,
                    f"{model.base_url}/{filename}",
                    model.model_dir / filename,
                    checksum,
                    progress,
                )
                for model in MODELS
                for filename, checksum in model.files.items()
            ]
            await asyncio.gather(*tasks)

    return True
