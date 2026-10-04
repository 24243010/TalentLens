"""Read TXT / PDF / DOCX resumes into plain text (fully offline)."""
import io


def read_file(name, data: bytes) -> str:
    ext = name.lower().rsplit(".", 1)[-1]
    if ext == "pdf":
        import pdfplumber
        with pdfplumber.open(io.BytesIO(data)) as pdf:
            return "\n".join((p.extract_text() or "") for p in pdf.pages)
    if ext == "docx":
        import docx
        d = docx.Document(io.BytesIO(data))
        return "\n".join(p.text for p in d.paragraphs)
    return data.decode("utf-8", errors="ignore")


import os
import zipfile

SUPPORTED = (".txt", ".pdf", ".docx")


def _unique(key, taken):
    base, ext = os.path.splitext(key)
    n = 2
    while key in taken:
        key = f"{base}_{n}{ext}"
        n += 1
    return key


def read_zip(data: bytes) -> tuple:
    """Return ({filename: text}, skipped_count) for every resume inside a ZIP (sub-folders included)."""
    texts, skipped = {}, 0
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        for info in z.infolist():
            name = info.filename
            if info.is_dir() or "__MACOSX" in name or os.path.basename(name).startswith("."):
                continue
            if not name.lower().endswith(SUPPORTED):
                continue
            try:
                texts[_unique(os.path.basename(name), texts)] = read_file(name, z.read(info))
            except Exception:
                skipped += 1
    return texts, skipped


def list_folder(path: str) -> list:
    out = []
    for root, _, names in os.walk(path):
        out += [os.path.join(root, n) for n in names if n.lower().endswith(SUPPORTED) and not n.startswith(".")]
    return sorted(out)


def read_folder(path: str) -> tuple:
    """Return ({filename: text}, skipped_count) for every resume in a local folder (sub-folders included)."""
    texts, skipped = {}, 0
    for p in list_folder(path):
        try:
            with open(p, "rb") as f:
                texts[_unique(os.path.basename(p), texts)] = read_file(p, f.read())
        except Exception:
            skipped += 1
    return texts, skipped
