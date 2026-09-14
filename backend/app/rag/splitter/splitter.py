from dataclasses import dataclass, field
import re

from app.rag.parser.parser import ParsedSection

_CODE_EXTENSIONS = {
    "py", "js", "ts", "tsx", "jsx", "java", "go", "rs", "c", "cpp", "h", "hpp",
    "cs", "rb", "php", "sh", "sql", "yml", "yaml", "toml", "json", "xml",
}


@dataclass
class ChunkInput:
    content: str
    metadata: dict = field(default_factory=dict)


def split_sections(sections: list[ParsedSection], file_type: str, chunk_size: int = 800, overlap: int = 80) -> list[ChunkInput]:
    chunks: list[ChunkInput] = []
    for section in sections:
        text = section.text.strip()
        if not text:
            continue
        if file_type in _CODE_EXTENSIONS:
            parts = _split_code(text, chunk_size)
        else:
            parts = _split_paragraphs(text, chunk_size, overlap)
        for index, part in enumerate(parts, start=1):
            metadata = dict(section.metadata)
            metadata.update({"chunk_part": index, "file_type": file_type})
            chunks.append(ChunkInput(content=part, metadata=metadata))
    return chunks


def _split_paragraphs(text: str, chunk_size: int, overlap: int) -> list[str]:
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    chunks: list[str] = []
    current = ""
    for paragraph in paragraphs:
        if len(current) + len(paragraph) + 1 <= chunk_size:
            current = f"{current}\n{paragraph}" if current else paragraph
        else:
            if current:
                chunks.append(current)
            if len(paragraph) > chunk_size:
                current = ""
                for start in range(0, len(paragraph), chunk_size - overlap):
                    chunks.append(paragraph[start:start + chunk_size])
            else:
                current = paragraph
    if current:
        chunks.append(current)
    return chunks


def _split_code(text: str, chunk_size: int) -> list[str]:
    lines = text.splitlines()
    chunks: list[str] = []
    current: list[str] = []
    current_size = 0
    for line in lines:
        line_size = len(line) + 1
        if current and current_size + line_size > chunk_size:
            chunks.append("\n".join(current))
            current = []
            current_size = 0
        current.append(line)
        current_size += line_size
    if current:
        chunks.append("\n".join(current))
    return chunks