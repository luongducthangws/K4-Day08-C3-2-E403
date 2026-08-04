"""Task 3 - Chuyen du lieu landing cua Topic 1 sang Markdown.

Script ho tro PDF/DOCX/DOC trong ``data/landing/legal`` va ca ba DOCX da
duoc dat truc tiep trong ``data/landing``. JSON cua Task 2 duoc chuyen sang
``data/standardized/news`` kem metadata nguon.
"""

from __future__ import annotations

import json
import re
import zipfile
from pathlib import Path
from xml.etree import ElementTree

LANDING_DIR = Path(__file__).parent.parent / "data" / "landing"
OUTPUT_DIR = Path(__file__).parent.parent / "data" / "standardized"
LEGAL_EXTENSIONS = {".pdf", ".docx", ".doc"}


def _markitdown_convert(filepath: Path) -> str:
    """Dung MarkItDown khi co san; fallback DOCX khong can dependency ngoai."""
    try:
        from markitdown import MarkItDown

        result = MarkItDown().convert(str(filepath))
        text = result.text_content.strip()
        if text:
            return text
    except Exception as exc:
        if filepath.suffix.lower() != ".docx":
            raise RuntimeError(
                'Khong the convert file; hay cai: pip install "markitdown[pdf]"'
            ) from exc

    if filepath.suffix.lower() == ".docx":
        return _docx_to_markdown(filepath)
    raise ValueError(f"Khong the chuyen doi file: {filepath}")


def _docx_to_markdown(filepath: Path) -> str:
    """Fallback nhe: doc noi dung WordprocessingML va giu heading/list co ban."""
    word_ns = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
    namespaces = {"w": word_ns}
    with zipfile.ZipFile(filepath) as archive:
        root = ElementTree.fromstring(archive.read("word/document.xml"))

    blocks: list[str] = []
    for paragraph in root.findall(".//w:body/w:p", namespaces):
        text = "".join(
            node.text or "" for node in paragraph.findall(".//w:t", namespaces)
        ).strip()
        if not text:
            continue

        style_node = paragraph.find("./w:pPr/w:pStyle", namespaces)
        style = ""
        if style_node is not None:
            style = style_node.attrib.get(f"{{{word_ns}}}val", "").lower()
        heading_match = re.search(r"heading\s*([1-6])|tieude([1-6])", style)
        if heading_match:
            level = int(heading_match.group(1) or heading_match.group(2))
            text = f"{'#' * level} {text}"
        elif paragraph.find("./w:pPr/w:numPr", namespaces) is not None:
            text = f"- {text}"
        blocks.append(text)

    if not blocks:
        raise ValueError(f"DOCX khong co noi dung text: {filepath}")
    return "\n\n".join(blocks)


def _legal_inputs() -> list[Path]:
    """Tim van ban o thu muc legal va o root landing (cach nhom da tai)."""
    candidates = [
        path
        for path in LANDING_DIR.rglob("*")
        if path.is_file()
        and path.suffix.lower() in LEGAL_EXTENSIONS
        and "news" not in path.relative_to(LANDING_DIR).parts
    ]
    return sorted(candidates, key=lambda path: str(path).lower())


def convert_legal_docs() -> list[Path]:
    """Convert tat ca van ban phap luat sang data/standardized/legal."""
    output_dir = OUTPUT_DIR / "legal"
    output_dir.mkdir(parents=True, exist_ok=True)
    outputs: list[Path] = []

    for filepath in _legal_inputs():
        print(f"Converting: {filepath.name}")
        content = _markitdown_convert(filepath)
        output_path = output_dir / f"{filepath.stem}.md"
        output_path.write_text(content.strip() + "\n", encoding="utf-8")
        outputs.append(output_path)
        print(f"  Saved: {output_path}")
    return outputs


def convert_news_articles() -> list[Path]:
    """Convert JSON cua Task 2 sang Markdown co provenance ro rang."""
    news_dir = LANDING_DIR / "news"
    output_dir = OUTPUT_DIR / "news"
    output_dir.mkdir(parents=True, exist_ok=True)
    outputs: list[Path] = []

    if not news_dir.exists():
        return outputs

    for filepath in sorted(news_dir.glob("*.json")):
        print(f"Converting: {filepath.name}")
        data = json.loads(filepath.read_text(encoding="utf-8"))
        content = data.get("content_markdown") or data.get("content") or ""
        if not isinstance(content, str) or not content.strip():
            raise ValueError(f"{filepath.name} khong co content_markdown")

        title = str(data.get("title") or "Khong ro tieu de").strip()
        source = str(data.get("url") or "N/A").strip()
        crawled = str(data.get("date_crawled") or "N/A").strip()
        markdown = (
            f"# {title}\n\n"
            f"**Nguon:** {source}\n\n"
            f"**Ngay thu thap:** {crawled}\n\n"
            "---\n\n"
            f"{content.strip()}\n"
        )
        output_path = output_dir / f"{filepath.stem}.md"
        output_path.write_text(markdown, encoding="utf-8")
        outputs.append(output_path)
        print(f"  Saved: {output_path}")
    return outputs


def convert_all() -> tuple[list[Path], list[Path]]:
    """Convert toan bo input va tra ve danh sach output de de kiem thu."""
    print("=" * 50)
    print("Task 3: Convert to Markdown")
    print("=" * 50)
    legal_outputs = convert_legal_docs()
    news_outputs = convert_news_articles()
    print(
        f"Done: {len(legal_outputs)} legal + {len(news_outputs)} news files "
        f"in {OUTPUT_DIR}"
    )
    return legal_outputs, news_outputs


if __name__ == "__main__":
    convert_all()
