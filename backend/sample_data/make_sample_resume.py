"""
Creates the SYNTHETIC sample resume used by tests and demo mode.
"Ananya Rao" is not a real person. Run:  python sample_data/make_sample_resume.py
"""
from pathlib import Path

HERE = Path(__file__).parent

LINES = [
    ("name", "Ananya Rao"),
    ("text", "Bengaluru, India | ananya.rao.sample@example.com | github.com/ananya-sample"),
    ("h", "Summary"),
    ("text", "Final-year Computer Science student who enjoys building backend services and small ML projects."),
    ("h", "Education"),
    ("text", "B.E. Computer Science and Engineering | Sample Institute of Technology, Bengaluru | 2023 - 2027 | CGPA: 8.4/10"),
    ("text", "Class XII (PCMC) | Sample PU College, Bengaluru | 2023 | 91%"),
    ("h", "Technical Skills"),
    ("text", "Languages: Python, Java, C, SQL"),
    ("text", "Frameworks: FastAPI, Flask, scikit-learn, Pandas, NumPy"),
    ("text", "Tools: MySQL, Git, Linux, Postman, HTML, CSS, JavaScript"),
    ("h", "Projects"),
    ("text", "Smart Notes API | FastAPI, MySQL, JWT"),
    ("bullet", "Built a REST API for a note-taking app with user signup, login using JWT and role-based access."),
    ("bullet", "Designed a normalised MySQL schema with 6 tables and wrote SQL joins for search and tagging."),
    ("bullet", "Wrote 25 pytest unit tests and documented every endpoint with OpenAPI."),
    ("text", "Loan Default Predictor | Python, Pandas, scikit-learn"),
    ("bullet", "Cleaned a 30,000-row public dataset with Pandas and did exploratory data analysis with Matplotlib."),
    ("bullet", "Trained logistic regression and random forest models; compared them using precision, recall and ROC-AUC."),
    ("text", "Campus Events Portal | Flask, HTML, CSS, JavaScript"),
    ("bullet", "Made a small web portal where clubs post events and students register; used Flask templates and SQLite."),
    ("bullet", "Worked in a team of 3 and handled the backend and deployment on a college Linux server."),
    ("h", "Certifications"),
    ("bullet", "Python for Everybody (Coursera), 2024"),
    ("bullet", "SQL (Basic) certificate, HackerRank, 2025"),
    ("h", "Achievements"),
    ("bullet", "Solved 150+ problems on HackerRank and LeetCode (arrays, strings, hashing)."),
    ("bullet", "Coding club coordinator: led weekly practice sessions for 40 juniors."),
    ("note", "SAMPLE RESUME: synthetic data created for testing CareerPilot AI. Not a real person."),
]


def make_pdf(path: Path) -> None:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.platypus import Paragraph, SimpleDocTemplate

    styles = {
        "name": ParagraphStyle("n", fontName="Helvetica-Bold", fontSize=18, spaceAfter=4),
        "h": ParagraphStyle("h", fontName="Helvetica-Bold", fontSize=12, spaceBefore=10, spaceAfter=3),
        "text": ParagraphStyle("t", fontName="Helvetica", fontSize=10, leading=13),
        "bullet": ParagraphStyle("b", fontName="Helvetica", fontSize=10, leading=13, leftIndent=12),
        "note": ParagraphStyle("x", fontName="Helvetica-Oblique", fontSize=8, spaceBefore=14),
    }
    story = [Paragraph(("• " if kind == "bullet" else "") + text, styles[kind]) for kind, text in LINES]
    SimpleDocTemplate(str(path), pagesize=A4, topMargin=40, bottomMargin=40).build(story)


def make_docx(path: Path) -> None:
    from docx import Document
    doc = Document()
    for kind, text in LINES:
        if kind == "name":
            doc.add_heading(text, level=0)
        elif kind == "h":
            doc.add_heading(text, level=1)
        elif kind == "bullet":
            doc.add_paragraph("• " + text)
        else:
            doc.add_paragraph(text)
    doc.save(str(path))


if __name__ == "__main__":
    make_pdf(HERE / "sample_resume.pdf")
    make_docx(HERE / "sample_resume.docx")
    print("wrote", HERE / "sample_resume.pdf", HERE / "sample_resume.docx")
