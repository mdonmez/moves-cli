# CLI Output Helper - `output()` Fonksiyonu

## Özet

CLI çıktıları için unified formatter fonksiyonu. Fonksiyon sadece string üretir, yazdırma işi `typer.echo()`'ya bırakılır.

## Dosya Konumu

`src/moves_cli/utils/output_formatter.py`

## API

```python
def output(*args: str | dict[str, Any] | list[dict[str, Any]]) -> str:
```

### Desteklenen Tipler

| Tip                    | Açıklama                                       |
| ---------------------- | ---------------------------------------------- |
| `str`                  | Header/mesaj (aralarına otomatik boş satır)    |
| `dict[str, Any]`       | Key-value pairs (2-space indent, otomatik `:`) |
| `list[dict[str, Any]]` | Tablo (header'lı, son kolon fold)              |

### Kullanım Örnekleri

```python
# Key-value çıktısı
typer.echo(output("Speaker added.", {"ID": "123", "Name": "john"}))
# Çıktı:
# Speaker added.
#   ID:   123
#   Name: john

# Tablo çıktısı
typer.echo(output(
    "Registered Speakers (3)",
    [
        {"ID": "john-HntIO", "NAME": "john", "STATUS": "Ready"},
        {"ID": "tom-H4XX0", "NAME": "tom", "STATUS": "Not Ready"},
    ]
))
# Çıktı:
# Registered Speakers (3)
#
# ID          NAME  STATUS
# ───────────────────────────
# john-HntIO  john  Ready
# tom-H4XX0   tom   Not Ready

# Mixed: text + kv + table
typer.echo(output(
    "Processing complete.",
    {"Total": "3", "Success": "2"},
    "Details:",
    [{"NAME": "john", "RESULT": "OK"}, {"NAME": "tom", "RESULT": "FAILED"}]
))

# Hata çıktısı (stderr)
typer.echo(output("Error!", {"Reason": "Not found"}), err=True)
raise typer.Exit(1)
```

## Özellikler

- ✅ Pure function (side effect yok)
- ✅ Tek fonksiyon üç tip: `str`, `dict`, `list[dict]`
- ✅ Type-safe: `str | dict[str, Any] | list[dict[str, Any]]`
- ✅ match/case ile modern Python
- ✅ Rich Table ile otomatik hizalama
- ✅ Otomatik 2-space indent (kv için)
- ✅ Otomatik boş satır (bloklar arası)
- ✅ Tablo: son kolon `overflow="fold"`, diğerleri `no_wrap=True`
- ✅ Monokrom (renksiz)
- ✅ Typer uyumlu (`err=True` ile stderr'a yazılabilir)

## cli.py Entegrasyonu

### Replace Edilebilecekler:

- `speaker add` (başarı/hata)
- `speaker edit` (başarı/hata)
- `speaker show`
- `speaker list` → `list[dict]` ile tablo
- `speaker delete`
- `speaker process`
- `settings list`
- `settings set`
- `settings unset`
- Tüm error mesajları

### Replace Edilemeyecekler:

- `presentation control` → Özel live UI (progress, keybind hints)
- Boş `typer.echo()` çağrıları
- Confirmation prompt'ları

## Notlar

- Separation of Concerns: `output()` format, `typer.echo()` I/O
- Endüstri standardı: git, docker, aws gibi renksiz çıktı
- Internal utility — public API değil
