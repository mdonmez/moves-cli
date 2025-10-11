from pathlib import Path
import shutil

DATA_FOLDER = Path.home() / ".moves"


def write(path: Path, data: str) -> bool:
    full_path = DATA_FOLDER / Path(path)
    try:
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(data, encoding="utf-8")
        return True
    except Exception as e:
        raise RuntimeError(f"Write operation failed for {path}: {e}") from e


def read(path: Path) -> str:
    full_path = DATA_FOLDER / Path(path)
    if not full_path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    if not full_path.is_file():
        raise IsADirectoryError(f"Path is a directory, not a file: {path}")
    try:
        data = full_path.read_text(encoding="utf-8")
        return data
    except Exception as e:
        raise RuntimeError(f"Read operation failed for {path}: {e}") from e


def list(path: Path) -> list[Path]:
    full_path = DATA_FOLDER / Path(path)
    if not full_path.exists():
        return []

    items = []
    try:
        for item in full_path.iterdir():
            items.append(item)
        return sorted(items, key=lambda p: str(p))
    except Exception as e:
        raise RuntimeError(f"List operation failed for {path}: {e}") from e


def rename(path: Path, new_name: str) -> Path:
    full_path = DATA_FOLDER / Path(path)
    target_path = full_path.parent / new_name

    try:
        if target_path.exists():
            target_path.unlink()

        moved_path = shutil.move(str(full_path), str(target_path))
        return Path(moved_path).relative_to(DATA_FOLDER)
    except Exception as e:
        raise RuntimeError(
            f"Rename operation failed for {full_path} to {new_name}: {e}"
        ) from e


def delete(path: Path) -> bool:
    full_path = DATA_FOLDER / Path(path)
    if not full_path.exists():
        raise FileNotFoundError(f"Path not found: {path}")

    try:
        if full_path.is_file():
            full_path.unlink()
        elif full_path.is_dir():
            shutil.rmtree(full_path)
        else:
            full_path.unlink()
        return True
    except Exception as e:
        raise RuntimeError(f"Delete operation failed for {path}: {e}") from e


def copy(source: Path, target: Path) -> bool:
    source_path = DATA_FOLDER / Path(source)
    target_path = DATA_FOLDER / Path(target)

    if not source_path.exists():
        raise FileNotFoundError(f"Source not found: {source}")

    if not target_path.exists():
        try:
            target_path.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            raise RuntimeError(
                f"Failed to create target directory {target}: {e}"
            ) from e

    try:
        if source_path.is_file():
            dest_file = target_path / source_path.name
            shutil.copy2(source_path, dest_file)
            return True
        elif source_path.is_dir():
            for item in source_path.rglob("*"):
                relative_path = item.relative_to(source_path)
                dest_item = target_path / relative_path
                if item.is_dir():
                    dest_item.mkdir(parents=True, exist_ok=True)
                else:
                    dest_item.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(item, dest_item)
            return True
        else:
            raise RuntimeError(f"Source path is neither file nor directory: {source}")
    except Exception as e:
        raise RuntimeError(
            f"Copy operation failed from {source} to {target}: {e}"
        ) from e
