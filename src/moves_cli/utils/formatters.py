from datetime import datetime
from io import StringIO
from typing import Any, Iterable

import mistune
from mistune.core import BaseRenderer, BlockState
from rich import box
from rich.console import Console
from rich.table import Table


type OutputArg = str | dict[str, Any] | list[dict[str, Any]]


class PlainTextRenderer(BaseRenderer):
    """Render markdown to plain text by stripping all markup.

    Used for normalizing markdown content before hash calculation,
    ensuring whitespace/formatting differences don't affect checksums.
    """

    NAME = "plain"

    def __call__(self, tokens: Iterable[dict[str, Any]], state: BlockState) -> str:
        out = self.render_tokens(tokens, state)
        return " ".join(out.split())

    def render_children(self, token: dict[str, Any], state: BlockState) -> str:
        children = token.get("children")
        if children:
            return self.render_tokens(children, state)
        return ""

    # Inline-level tokens
    def text(self, token: dict[str, Any], state: BlockState) -> str:
        return token.get("raw", "")

    def emphasis(self, token: dict[str, Any], state: BlockState) -> str:
        return self.render_children(token, state)

    def strong(self, token: dict[str, Any], state: BlockState) -> str:
        return self.render_children(token, state)

    def link(self, token: dict[str, Any], state: BlockState) -> str:
        return self.render_children(token, state)

    def image(self, token: dict[str, Any], state: BlockState) -> str:
        return self.render_children(token, state)

    def codespan(self, token: dict[str, Any], state: BlockState) -> str:
        return token.get("raw", "")

    def linebreak(self, token: dict[str, Any], state: BlockState) -> str:
        return " "

    def softbreak(self, token: dict[str, Any], state: BlockState) -> str:
        return " "

    def inline_html(self, token: dict[str, Any], state: BlockState) -> str:
        return ""

    # Block-level tokens
    def paragraph(self, token: dict[str, Any], state: BlockState) -> str:
        return self.render_children(token, state) + " "

    def heading(self, token: dict[str, Any], state: BlockState) -> str:
        return self.render_children(token, state) + " "

    def thematic_break(self, token: dict[str, Any], state: BlockState) -> str:
        return ""

    def blank_line(self, token: dict[str, Any], state: BlockState) -> str:
        return ""

    def block_text(self, token: dict[str, Any], state: BlockState) -> str:
        return self.render_children(token, state) + " "

    def block_code(self, token: dict[str, Any], state: BlockState) -> str:
        return token.get("raw", "") + " "

    def block_quote(self, token: dict[str, Any], state: BlockState) -> str:
        return self.render_children(token, state) + " "

    def block_html(self, token: dict[str, Any], state: BlockState) -> str:
        return ""

    def block_error(self, token: dict[str, Any], state: BlockState) -> str:
        return ""

    def list(self, token: dict[str, Any], state: BlockState) -> str:
        return self.render_children(token, state) + " "

    def list_item(self, token: dict[str, Any], state: BlockState) -> str:
        return self.render_children(token, state) + " "


def markdown_to_plain_text(md_content: str) -> str:
    """Convert markdown to plain text by stripping all markup."""
    md = mistune.create_markdown(renderer=PlainTextRenderer())
    return md(md_content)


def format_datetime(iso_string: str | None, fallback: str = "N/A") -> str:
    if not iso_string:
        return fallback

    try:
        dt = datetime.fromisoformat(iso_string)
        return dt.strftime("%Y-%m-%d %H:%M")
    except ValueError:
        return "Invalid Date"


def output(*args: OutputArg) -> str:
    buffer = StringIO()
    console = Console(file=buffer, highlight=False, markup=False, force_terminal=True)

    output_parts: list[str] = []
    pending_key_values: list[tuple[str, str]] = []

    def flush_key_values() -> None:
        if not pending_key_values:
            return

        key_value_table = Table(show_header=False, box=None, pad_edge=False)
        key_value_table.add_column(no_wrap=True)
        key_value_table.add_column(overflow="fold")

        for key, value in pending_key_values:
            key_value_table.add_row(key, value)

        buffer.seek(0)
        buffer.truncate()
        console.print(key_value_table)
        output_parts.append(buffer.getvalue().rstrip())
        pending_key_values.clear()

    def render_table(rows: list[dict[str, Any]]) -> str:
        if not rows:
            return ""

        headers = list(rows[0].keys())
        last_column_index = len(headers) - 1

        data_table = Table(
            show_header=True,
            header_style=None,
            box=box.SIMPLE_HEAD,
            pad_edge=False,
        )

        for index, header in enumerate(headers):
            is_last_column = index == last_column_index
            data_table.add_column(
                header,
                no_wrap=not is_last_column,
                overflow="fold" if is_last_column else "ellipsis",
            )

        for row in rows:
            cell_values = [str(row.get(header, "")) for header in headers]
            data_table.add_row(*cell_values)

        buffer.seek(0)
        buffer.truncate()
        console.print(data_table)

        # rich adds 1 char padding to each line, strip it
        lines = buffer.getvalue().strip().split("\n")
        cleaned_lines = []
        for line in lines:
            if line.startswith(" ") and len(line) > 1:
                cleaned_lines.append(line[1:])
            else:
                cleaned_lines.append(line)

        return "\n".join(cleaned_lines)

    for arg in args:
        match arg:
            case str() as message:
                flush_key_values()
                if output_parts:
                    output_parts.append("")  # blank line between sections
                output_parts.append(message)

            case dict() as key_value_pairs:
                for key, value in key_value_pairs.items():
                    # avoid double colon if key already ends with :
                    formatted_key = f"  {key}" if key.endswith(":") else f"  {key}:"
                    pending_key_values.append((formatted_key, str(value)))

            case [dict(), *_] as table_rows:
                flush_key_values()
                if output_parts:
                    output_parts.append("")
                output_parts.append(render_table(table_rows))

    flush_key_values()

    return "\n".join(output_parts)
