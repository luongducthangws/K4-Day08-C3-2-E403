"""Task 2 - Crawl cac bai huong dan ve quyen loi nguoi lao dong.

Du an chon Topic 1 (tro ly hoi dap Luat Lao dong), vi vay nguon du lieu
duoc lay tu Bao Dien tu Chinh phu thay cho cac URL Shopee cua starter.

Chay tu thu muc goc::

    python -m src.task2_crawl_news

Moi bai duoc luu thanh mot JSON trong ``data/landing/news`` voi cac truong
``url``, ``title``, ``date_crawled`` va ``content_markdown``.
"""

from __future__ import annotations

import asyncio
import html
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DATA_DIR = Path(__file__).parent.parent / "data" / "landing" / "news"
MIN_CONTENT_LENGTH = 500

# Nam bai viet chinh thong, bao phu cac nhu cau pho bien cua nguoi lao dong tre:
# thu viec, hop dong, cham dut hop dong, lam them gio va nghi phep.
ARTICLE_URLS = [
    "https://baochinhphu.vn/17-diem-moi-noi-bat-cua-bo-luat-lao-dong-2019-102267514.htm",
    "https://baochinhphu.vn/tu-2021-them-nhieu-quyen-loi-cho-nguoi-lao-dong-102285092.htm",
    "https://baochinhphu.vn/quy-dinh-ve-thoi-gio-nghi-ngoi-theo-bo-luat-lao-dong-moi-102294141.htm",
    "https://baochinhphu.vn/can-dieu-kien-gi-de-su-dung-nguoi-lao-dong-lam-them-gio-102291610.htm",
    "https://baochinhphu.vn/khong-nghi-het-phep-nam-co-duoc-thanh-toan-tien-10225090516273483.htm",
]


def setup_directory() -> None:
    """Tao thu muc output neu chua co."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def _markdown_text(markdown: Any) -> str:
    """Chuan hoa output Crawl4AI o ca API cu va moi thanh chuoi."""
    if isinstance(markdown, str):
        return markdown
    for attribute in ("fit_markdown", "raw_markdown", "markdown_with_citations"):
        value = getattr(markdown, attribute, None)
        if isinstance(value, str) and value.strip():
            return value
    return str(markdown or "")


def _clean_markdown(content: str) -> str:
    """Loai bo khoang trang va cac khoi dieu huong ro rang bi lap."""
    content = html.unescape(content).replace("\u00a0", " ")
    content = re.sub(r"[ \t]+", " ", content)
    content = re.sub(r"\n{3,}", "\n\n", content)
    return content.strip()


async def crawl_article(url: str, crawler: Any | None = None) -> dict[str, str]:
    """Crawl mot bai va tra ve metadata cung noi dung Markdown.

    ``crawler`` co the duoc truyen vao de tai su dung mot browser cho ca lo.
    Khi Crawl4AI khong duoc cai, ham dung ``requests`` + BeautifulSoup nhu mot
    crawler nhe. Nhu vay script van chay duoc tren may khong co Chromium.
    """
    own_crawler = crawler is None
    if own_crawler:
        try:
            from crawl4ai import AsyncWebCrawler

            crawler = AsyncWebCrawler()
            await crawler.__aenter__()
        except (ImportError, OSError):
            crawler = None

    try:
        if crawler is not None:
            result = await crawler.arun(url=url)
            if getattr(result, "success", True) is False:
                raise RuntimeError(getattr(result, "error_message", "Crawl4AI failed"))
            metadata = getattr(result, "metadata", {}) or {}
            title = metadata.get("title") or "Khong ro tieu de"
            content = _markdown_text(getattr(result, "markdown", ""))
        else:
            title, content = await asyncio.to_thread(_crawl_with_requests, url)

        content = _clean_markdown(content)
        if len(content) < MIN_CONTENT_LENGTH:
            raise ValueError(
                f"Noi dung crawl qua ngan ({len(content)} ky tu): {url}"
            )
        return {
            "url": url,
            "title": str(title).strip(),
            "date_crawled": datetime.now(timezone.utc).isoformat(),
            "content_markdown": content,
        }
    finally:
        if own_crawler and crawler is not None:
            await crawler.__aexit__(None, None, None)


def _crawl_with_requests(url: str) -> tuple[str, str]:
    """Fallback crawler cho HTML tinh khi khong co Crawl4AI/Chromium."""
    import requests
    from bs4 import BeautifulSoup

    response = requests.get(
        url,
        timeout=30,
        headers={"User-Agent": "Mozilla/5.0 (compatible; K4-RAG-Lab/1.0)"},
    )
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    for tag in soup.select("script, style, nav, footer, header, form, noscript"):
        tag.decompose()

    title_tag = soup.find("h1") or soup.find("title")
    title = title_tag.get_text(" ", strip=True) if title_tag else "Khong ro tieu de"
    article = soup.find("article") or soup.find("main") or soup.body
    if article is None:
        raise ValueError(f"Khong tim thay noi dung HTML: {url}")

    lines = [node.get_text(" ", strip=True) for node in article.find_all(["h2", "h3", "p", "li"])]
    content = "\n\n".join(line for line in lines if line)
    return title, content


async def crawl_all() -> list[Path]:
    """Crawl toan bo URL; chi ghi file sau khi bai da qua validation."""
    setup_directory()
    saved: list[Path] = []

    crawler = None
    try:
        from crawl4ai import AsyncWebCrawler

        crawler = AsyncWebCrawler()
        await crawler.__aenter__()
    except (ImportError, OSError):
        crawler = None

    try:
        for index, url in enumerate(ARTICLE_URLS, 1):
            print(f"[{index}/{len(ARTICLE_URLS)}] Crawling: {url}")
            article = await crawl_article(url, crawler=crawler)
            path = DATA_DIR / f"article_{index:02d}.json"
            path.write_text(
                json.dumps(article, ensure_ascii=False, indent=2), encoding="utf-8"
            )
            saved.append(path)
            print(f"  Saved: {path}")
    finally:
        if crawler is not None:
            await crawler.__aexit__(None, None, None)

    print(f"Done: {len(saved)} articles saved in {DATA_DIR}")
    return saved


if __name__ == "__main__":
    asyncio.run(crawl_all())
