from pathlib import Path

import typer
import xxhash

CHUNK_SIZE = 1024 * 1024

app = typer.Typer(
    add_completion=False, help="Calculate XXH3_64 hash for files (development utility)"
)


def calculate_hash(filepath: Path) -> str | None:
    if not filepath.exists():
        return None
    hasher = xxhash.xxh3_64()
    with filepath.open("rb") as f:
        while chunk := f.read(CHUNK_SIZE):
            hasher.update(chunk)
    return hasher.hexdigest()


@app.command()
def main(
    folder: Path = typer.Argument(
        ...,
        help="Folder path to calculate hashes for all files",
        exists=True,
        file_okay=False,
        dir_okay=True,
        resolve_path=True,
    ),
) -> None:
    files = sorted([f for f in folder.rglob("*") if f.is_file()])

    if not files:
        typer.echo("No files found in folder.")
        return

    print(f"{'Filename':<40} | {'Hash':<20} | {'Size (MB)':<10}")
    print("-" * 75)

    for path in files:
        hash_val = calculate_hash(path)
        size_mb = path.stat().st_size / (1024 * 1024)

        if hash_val:
            print(f"{path.name:<40} | {hash_val:<20} | {size_mb:<10.2f}")
        else:
            print(f"{path.name:<40} | {'FAILED':<20} | -")


if __name__ == "__main__":
    app()
