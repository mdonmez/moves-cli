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

from moves_cli.data.models import EmbeddingModel, MlModel, SttModel
from moves_cli.utils import data_handler

CHUNK_SIZE = 65536
HTTP_TIMEOUT = 30.0
MODELS = [EmbeddingModel, SttModel]
MODELS_BASE_PATH = Path(data_handler.DATA_FOLDER) / "ml_models"

console = Console(highlight=False, color_system=None)


def _has_valid_checksum(filepath: Path, expected: str) -> bool:
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


def _remove_invalid_models() -> None:
    if not MODELS_BASE_PATH.exists():
        return

    valid_paths = set()
    for model in MODELS:
        valid_paths.add(model.model_dir)
        valid_paths.update(model.model_dir / filename for filename in model.files)

    invalid = sorted(
        set(MODELS_BASE_PATH.rglob("*")) - valid_paths,
        key=lambda p: len(p.parts),
        reverse=True,
    )

    for path in invalid:
        try:
            path.unlink() if path.is_file() else shutil.rmtree(path, ignore_errors=True)
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
        if not isinstance(e, RuntimeError):
            raise RuntimeError(f"Download failed: {url}") from e
        raise


def _create_download_tasks(
    client: httpx.AsyncClient,
    progress: Progress,
    models: list[tuple[str, MlModel]],
) -> list:
    tasks = []
    for name, model in models:
        for filename, checksum in model.files.items():
            url = f"{model.base_url}/{filename}"
            filepath = model.model_dir / filename
            tasks.append(_download_file(client, url, filepath, checksum, progress))
    return tasks


async def download_and_prepare_models() -> dict[str, Path]:
    _remove_invalid_models()

    models = [("embedding", EmbeddingModel), ("stt", SttModel)]
    model_paths = {name: model.model_dir for name, model in models}

    async with httpx.AsyncClient(timeout=HTTP_TIMEOUT, follow_redirects=True) as client:
        with Progress(
            SpinnerColumn(),
            TextColumn("  [progress.description]{task.description}"),
            BarColumn(),
            DownloadColumn(),
            TaskProgressColumn(),
            console=console,
        ) as progress:
            tasks = _create_download_tasks(client, progress, models)
            await asyncio.gather(*tasks)

    return model_paths


def prepare_models() -> dict[str, Path]:
    return asyncio.run(download_and_prepare_models())
