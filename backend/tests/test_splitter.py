from app.rag.parser.parser import ParsedSection
from app.rag.splitter.splitter import split_sections


def test_split_long_text() -> None:
    sections = [ParsedSection(text="段落A" * 50 + "\n\n" + "段落B" * 50, metadata={"filename": "a.md"})]

    chunks = split_sections(sections, file_type="md", chunk_size=60, overlap=10)

    assert len(chunks) > 1
    assert all(chunk.content for chunk in chunks)


def test_split_code_keeps_lines() -> None:
    lines = [f"line_{index} = {index}" for index in range(20)]
    sections = [ParsedSection(text="\n".join(lines), metadata={"filename": "app.py"})]

    chunks = split_sections(sections, file_type="py", chunk_size=60)

    assert chunks
    assert "line_0 = 0" in chunks[0].content