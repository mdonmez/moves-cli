from io import StringIO
from typing import Any

from rich import box
from rich.console import Console
from rich.table import Table


def output(*args: str | dict[str, Any] | list[dict[str, Any]]) -> str:
    buf = StringIO()
    con = Console(file=buf, highlight=False, markup=False, force_terminal=True)
    out: list[str] = []
    kvs: list[tuple[str, str]] = []

    def flush() -> None:
        if not kvs:
            return
        tbl = Table(show_header=False, box=None, pad_edge=False)
        tbl.add_column(no_wrap=True)
        tbl.add_column(overflow="fold")
        [tbl.add_row(k, v) for k, v in kvs]
        buf.seek(0), buf.truncate(), con.print(tbl)
        out.append(buf.getvalue().rstrip())
        kvs.clear()

    def table(rows: list[dict[str, Any]]) -> str:
        if not rows:
            return ""
        hdrs, last = list(rows[0].keys()), len(rows[0]) - 1
        tbl = Table(
            show_header=True, header_style=None, box=box.SIMPLE_HEAD, pad_edge=False
        )
        [
            tbl.add_column(
                h, no_wrap=i < last, overflow="fold" if i == last else "ellipsis"
            )
            for i, h in enumerate(hdrs)
        ]
        [tbl.add_row(*(str(r.get(h, "")) for h in hdrs)) for r in rows]
        buf.seek(0), buf.truncate(), con.print(tbl)
        return "\n".join(
            ln.lstrip(" ")[:1] and ln[1:] if ln[0:1] == " " else ln
            for ln in buf.getvalue().strip().split("\n")
        )

    for arg in args:
        match arg:
            case str():
                flush()
                out and out.append("")
                out.append(arg)
            case dict() as d:
                kvs.extend(
                    (f"  {k}" if k.endswith(":") else f"  {k}:", str(v))
                    for k, v in d.items()
                )
            case [dict(), *_]:
                flush()
                out and out.append("")
                out.append(table(arg))

    flush()
    return "\n".join(out)
