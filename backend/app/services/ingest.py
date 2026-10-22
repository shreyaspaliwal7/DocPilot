import io
import pypdf


def extract_pages(filename: str, content: bytes) -> list[dict]:
  lower = filename.lower()
  pages = []

  if lower.endswith(".pdf"):
    reader = pypdf.PdfReader(io.BytesIO(content))
    for idx, page in enumerate(reader.pages, start=1):
      text = page.extract_text() or ""
      if text.strip():
        pages.append({"page": idx, "text": text.strip()})
  elif lower.endswith(".txt"):
    text = content.decode("utf-8", errors="replace").strip()
    if text:
      pages.append({"page": 1, "text": text})

  return pages


def chunk_pages(
    pages: list[dict], chunk_size: int, chunk_overlap: int
) -> list[dict]:
  chunks = []
  chunk_index = 0
  step = max(1, chunk_size - chunk_overlap)

  for page in pages:
    text = page["text"]
    page_num = page["page"]
    start = 0

    # slide window by size minus overlap to preserve context across chunks
    while start < len(text):
      end = start + chunk_size
      chunk_text = text[start:end].strip()
      if chunk_text:
        chunks.append({
            "chunk_index": chunk_index,
            "page_number": page_num,
            "content": chunk_text,
        })
        chunk_index += 1
      start += step

  return chunks
