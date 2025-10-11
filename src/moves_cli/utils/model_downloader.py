from typing import Literal
from pathlib import Path
import httpx
from tqdm import tqdm
from moves_cli.utils import data_handler

MODELS = {
    "embedding": {
        "name": "all-MiniLM-L6-v2_quint8_avx2",
        "base_url": "https://github.com/mdonmez/moves-cli/raw/refs/heads/master/src/moves_cli/core/components/ml_models/all-MiniLM-L6-v2_quint8_avx2",
        "files": [
            "model.onnx",
            "config.json",
            "special_tokens_map.json",
            "tokenizer.json",
            "tokenizer_config.json",
        ],
    },
    "stt": {
        "name": "nemo-streaming-stt-480ms-int8",
        "base_url": "https://github.com/mdonmez/moves-cli/raw/refs/heads/master/src/moves_cli/core/components/ml_models/nemo-streaming-stt-480ms-int8",
        "files": [
            "decoder.int8.onnx",
            "encoder.int8.onnx",
            "joiner.int8.onnx",
            "tokens.txt",
        ],
    },
}


def _download_file(
    client: httpx.Client, url: str, filepath: Path, chunk_size: int = 8192
) -> None:
    if filepath.exists():
        return
    try:
        with client.stream("GET", url, follow_redirects=True) as r:
            r.raise_for_status()
            total = int(r.headers.get("content-length", 0))
            with (
                filepath.open("wb") as f,
                tqdm(
                    total=total,
                    unit="iB",
                    unit_scale=True,
                    desc=f"Downloading {filepath.name}",
                ) as bar,
            ):
                for chunk in r.iter_bytes(chunk_size):
                    f.write(chunk)
                    bar.update(len(chunk))
    except httpx.HTTPError as e:
        filepath.unlink(missing_ok=True)
        raise RuntimeError(f"Download failed: {url} ({e})") from e


def download_model(model_type: Literal["embedding", "stt"]) -> Path:
    if model_type not in MODELS:
        raise ValueError(f"Unsupported model type: {model_type}")
    conf = MODELS[model_type]
    model_dir = Path(data_handler.DATA_FOLDER) / "ml_models" / conf["name"]
    model_dir.mkdir(parents=True, exist_ok=True)
    with httpx.Client(timeout=30.0, follow_redirects=True) as client:
        for fname in conf["files"]:
            _download_file(client, f"{conf['base_url']}/{fname}", model_dir / fname)
    return model_dir


if __name__ == "__main__":
    download_model("embedding")
    download_model("stt")
