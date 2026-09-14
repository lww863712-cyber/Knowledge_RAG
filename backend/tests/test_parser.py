from pathlib import Path

from app.rag.parser.parser import parse_file


def test_parse_markdown_file(temp_dir: Path) -> None:
    file = temp_dir / "note.md"
    file.write_text("# 标题\n\n这是笔记内容。", encoding="utf-8")

    sections = parse_file(str(file), "md")

    assert len(sections) == 1
    assert "这是笔记内容" in sections[0].text
    assert sections[0].metadata["filename"] == "note.md"


def test_parse_json_preserves_hierarchy(temp_dir: Path) -> None:
    file = temp_dir / "data.json"
    file.write_text('{"a": {"b": 1}}', encoding="utf-8")

    sections = parse_file(str(file), "json")

    assert sections[0].metadata["format"] == "json"
    assert "$.a.b: 1" in sections[0].text


def test_parse_txt_falls_back_for_plain_text(temp_dir: Path) -> None:
    file = temp_dir / "plain.txt"
    file.write_text("plain text content", encoding="utf-8")

    sections = parse_file(str(file), "txt")

    assert sections[0].text == "plain text content"