"""
Step 1 of resume analysis: check the uploaded file and pull plain text out of it.

We validate by extension AND by the file's first bytes (a renamed .exe will not
pass as a PDF), enforce a size limit, and refuse files with no readable text
instead of guessing.
"""
import io
import zipfile

from app.config import settings


class ResumeFileError(ValueError):
    """Raised with a message that is safe to show to the student."""


ALLOWED = {
    ".pdf": "application/pdf",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}
MIN_TEXT_CHARS = 150


def validate_upload(filename: str, data: bytes) -> str:
    """Return the file extension if the upload is acceptable, else raise ResumeFileError."""
    name = (filename or "").lower().strip()
    ext = "." + name.rsplit(".", 1)[-1] if "." in name else ""
    if ext not in ALLOWED:
        raise ResumeFileError("Please upload your resume as a PDF or DOCX file.")
    if not data:
        raise ResumeFileError("That file is empty. Please choose your resume file again.")
    limit = settings.max_upload_mb * 1024 * 1024
    if len(data) > limit:
        raise ResumeFileError(f"That file is larger than {settings.max_upload_mb} MB. Please upload a smaller file.")
    if ext == ".pdf" and not data[:1024].lstrip().startswith(b"%PDF"):
        raise ResumeFileError("This file is named .pdf but is not a real PDF. Please export your resume as PDF again.")
    if ext == ".docx":
        try:
            with zipfile.ZipFile(io.BytesIO(data)) as z:
                if "word/document.xml" not in z.namelist():
                    raise ResumeFileError("This .docx file looks damaged. Please save it again from Word or Google Docs.")
        except zipfile.BadZipFile:
            raise ResumeFileError("This file is named .docx but is not a Word document.")
    return ext


def extract_text(ext: str, data: bytes) -> str:
    """Plain text of the resume. Raises ResumeFileError if nothing readable is inside."""
    text = _pdf_text(data) if ext == ".pdf" else _docx_text(data)
    text = "\n".join(line.rstrip() for line in text.replace("\r", "").split("\n"))
    if len(text.strip()) < MIN_TEXT_CHARS:
        raise ResumeFileError(
            "We could not read enough text from this file. If it is a scanned image or a photo, "
            "please upload a text-based PDF or a DOCX (export from Word / Google Docs / Canva as PDF)."
        )
    return text.strip()


def _pdf_text(data: bytes) -> str:
    try:
        import pdfplumber
        with pdfplumber.open(io.BytesIO(data)) as pdf:
            pages = [p.extract_text(x_tolerance=1.5) or "" for p in pdf.pages[:10]]
        text = "\n".join(pages)
        if text.strip():
            return text
    except Exception:  # fall back to pypdf below
        pass
    try:
        from pypdf import PdfReader
        reader = PdfReader(io.BytesIO(data))
        return "\n".join((p.extract_text() or "") for p in reader.pages[:10])
    except Exception:
        raise ResumeFileError("This PDF could not be opened. It may be password protected or damaged.")


def _docx_text(data: bytes) -> str:
    from docx import Document
    try:
        doc = Document(io.BytesIO(data))
    except Exception:
        raise ResumeFileError("This .docx file could not be opened. Please save it again and retry.")
    lines = [p.text for p in doc.paragraphs]
    for table in doc.tables:  # many resume templates put content inside tables
        for row in table.rows:
            cells = [c.text.strip() for c in row.cells if c.text.strip()]
            if cells:
                lines.append(" | ".join(dict.fromkeys(cells)))
    return "\n".join(lines)
