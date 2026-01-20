import asyncio
import os
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

from moves_cli.models import EmbeddingModel, SttModel, VadModel

CHUNK_SIZE = 1024 * 1024
HTTP_TIMEOUT = 30.0
MAX_CONCURRENT_DOWNLOADS = 4
MODELS = [EmbeddingModel, SttModel, VadModel]

console = Console(stderr=True, highlight=False, force_terminal=True)


def _verify_checksum_sync(filepath: Path, expected: str) -> bool:
    if not filepath.exists():
        return False

    try:
        hasher = xxhash.xxh3_64()
        with filepath.open("rb") as f:
            while chunk := f.read(CHUNK_SIZE):
                hasher.update(chunk)
        return hasher.hexdigest() == expected
    except (OSError, IOError):
        return False


def _clean_model_directory() -> None:
    models_base_path = MODELS[0].model_dir.parent
    if not models_base_path.exists():
        return

    valid_files = set()
    valid_dirs = set()

    for model in MODELS:
        valid_dirs.add(model.model_dir.resolve())
        for filename in model.files:
            full_path = (model.model_dir / filename).resolve()
            valid_files.add(full_path)

    for path in models_base_path.rglob("*"):
        resolved = path.resolve()

        if resolved.is_file() and resolved not in valid_files:
            try:
                resolved.unlink()
            except OSError:
                pass

    for root, dirs, files in os.walk(models_base_path, topdown=False):
        for name in dirs:
            d_path = Path(root) / name
            if d_path.resolve() not in valid_dirs:
                try:
                    d_path.rmdir()
                except OSError:
                    pass


async def _download_file(
    client: httpx.AsyncClient,
    url: str,
    filepath: Path,
    checksum: str,
    progress: Progress,
    semaphore: asyncio.Semaphore,
) -> None:
    is_valid = await asyncio.to_thread(_verify_checksum_sync, filepath, checksum)
    if is_valid:
        return

    task_id = progress.add_task(filepath.name, total=None)
    temp_path = filepath.with_suffix(".tmp")

    try:
        async with semaphore:
            async with client.stream("GET", url) as response:
                response.raise_for_status()

                total_size = int(response.headers.get("content-length", 0))
                progress.update(task_id, total=total_size)

                filepath.parent.mkdir(parents=True, exist_ok=True)

                with temp_path.open("wb") as f:
                    async for chunk in response.aiter_bytes(chunk_size=CHUNK_SIZE):
                        f.write(chunk)
                        progress.advance(task_id, len(chunk))

        temp_path.replace(filepath)

        is_valid = await asyncio.to_thread(_verify_checksum_sync, filepath, checksum)
        if not is_valid:
            progress.update(task_id, description=f"Corrupt: {filepath.name}")
            filepath.unlink(missing_ok=True)
            raise RuntimeError(f"Checksum mismatch: {filepath.name}")

        progress.update(task_id, visible=False)

    except Exception as e:
        progress.update(task_id, description=f"Failed: {filepath.name}")
        temp_path.unlink(missing_ok=True)
        raise RuntimeError(f"Download failed: {url}") from e


async def prepare_models() -> bool:
    from rich.live import Live
    from rich.spinner import Spinner

    semaphore = asyncio.Semaphore(MAX_CONCURRENT_DOWNLOADS)

    spinner = Spinner("dots", text="Loading models")

    with Live(spinner, console=console, refresh_per_second=10, transient=True):
        pass

    async with httpx.AsyncClient(
        timeout=HTTP_TIMEOUT,
        follow_redirects=True,
        limits=httpx.Limits(max_keepalive_connections=5, max_connections=10),
    ) as client:
        with Progress(
            SpinnerColumn("dots"),
            TextColumn("{task.description}"),
            BarColumn(complete_style="white", finished_style="white"),
            TaskProgressColumn(),
            DownloadColumn(),
            console=console,
            transient=True,
        ) as progress:
            tasks = [
                _download_file(
                    client,
                    f"{model.base_url}/{filename}",
                    model.model_dir / filename,
                    checksum,
                    progress,
                    semaphore,
                )
                for model in MODELS
                for filename, checksum in model.files.items()
            ]

            await asyncio.gather(*tasks)

    return True
