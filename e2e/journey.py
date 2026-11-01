"""CareerPilot v2: full student journey in a real browser.
Usage: python e2e/journey.py [base_url] [--shots DIR] [--only desktop|mobile]
Desktop 1440x900 runs everything; mobile 390x844 runs a shorter pass. Fails on any console error,
uncaught page error or failed /api request (except expected 401s before login)."""
import sys
import uuid
from pathlib import Path

from playwright.sync_api import Page, expect, sync_playwright

args = [a for a in sys.argv[1:] if not a.startswith("--")]
BASE = (args[0] if args else "http://127.0.0.1:8000").rstrip("/")
ROOT = Path(__file__).resolve().parent
SAMPLE = ROOT.parent / "backend" / "sample_data" / "sample_resume.pdf"
SHOTS = Path(sys.argv[sys.argv.index("--shots") + 1]) if "--shots" in sys.argv else ROOT / "shots"
ONLY = sys.argv[sys.argv.index("--only") + 1] if "--only" in sys.argv else None
SHOTS.mkdir(parents=True, exist_ok=True)
PASSWORD = "Placement2027"
PRACTICE = ROOT.parent / "backend" / "app" / "seed" / "data" / "practice"


def known_solution(title: str) -> str | None:
    import json
    for f in PRACTICE.glob("*.json"):
        for q in json.loads(f.read_text())["coding"]:
            if q["title"] == title:
                return q["solution"]
    return None


def shot(page: Page, vp: str, name: str, full=False):
    page.wait_for_timeout(400)
    page.screenshot(path=str(SHOTS / f"{vp}_{name}.png"), full_page=full)


def go(page: Page, path: str):
    page.goto(BASE + path)
    page.wait_for_load_state("networkidle")


def sign_up(page: Page, vp: str, email: str):
    go(page, "/")
    shot(page, vp, "00_landing")
    page.get_by_role("link", name="Sign up").first.click()
    expect(page.get_by_role("heading", name="Create your account")).to_be_visible()
    page.get_by_label("Full name").fill("Rahul Kumar")
    page.get_by_label("College email or personal email").fill(email)
    page.get_by_label("Password").fill(PASSWORD)
    page.get_by_role("button", name="Create account").click()
    expect(page.get_by_role("heading", name="Where are you studying?")).to_be_visible(timeout=15000)
    page.get_by_label("College or university").fill("Nitte Meenakshi Institute of Technology")
    page.get_by_label("Branch").fill("Computer Science")
    page.get_by_label("Graduation year").fill("2026")
    page.get_by_role("button", name="Continue").click()
    page.get_by_label("Upload resume").set_input_files(str(SAMPLE))
    expect(page.get_by_text("skills and")).to_be_visible(timeout=30000)
    page.get_by_role("button", name="Continue").click()
    page.get_by_role("button", name="Skip for now").click()
    expect(page.get_by_role("heading", name="What your resume shows")).to_be_visible(timeout=15000)


def log_out_from_menu(page: Page, vp: str):
    if vp == "mobile":
        page.get_by_role("button", name="Log out").first.click()
    else:
        page.get_by_test_id("user-menu").click()
        page.get_by_role("menuitem", name="Log out").click()
    expect(page.get_by_text("You have been logged out")).to_be_visible(timeout=10000)


def log_in(page: Page, email: str, next_path: str = ""):
    go(page, "/login/" + (f"?next={next_path}" if next_path else ""))
    page.get_by_label("College email or personal email").fill(email)
    page.get_by_label("Password").fill(PASSWORD)
    page.get_by_role("button", name="Log in").click()
    page.wait_for_load_state("networkidle")


def desktop(page: Page, vp: str = "desktop"):
    email = f"e2e-{uuid.uuid4().hex[:8]}@example.com"
    sign_up(page, vp, email)
    go(page, "/companies/view/?slug=infosys")
    page.get_by_role("button", name="Prepare for Infosys").click()
    expect(page.get_by_role("link", name="See my gaps for Infosys")).to_be_visible(timeout=15000)

    # Skill gap: change role and company, the result must follow the selection
    go(page, "/gaps/")
    page.locator("#role").select_option("data_engineer")
    page.locator("#company").select_option(label="Infosys")
    expect(page.get_by_test_id("gap-title")).to_have_text("Data Engineer at Infosys", timeout=15000)
    expect(page.get_by_test_id("company-stages")).to_contain_text("Infosys")
    page.get_by_test_id("gap-row").first.click()
    shot(page, vp, "03_skill_gap")
    page.locator("#company").select_option(label="Accenture")
    expect(page.get_by_test_id("gap-title")).to_have_text("Data Engineer at Accenture", timeout=15000)
    page.locator("#role").select_option("software_developer")
    expect(page.get_by_test_id("gap-title")).to_have_text("Software Developer at Accenture", timeout=15000)

    # Practice: the filter combination that used to say "No questions"
    go(page, "/practice/")
    page.get_by_label("Company", exact=True).select_option(label="Infosys")
    page.get_by_label("Type", exact=True).select_option("coding")
    page.wait_for_load_state("networkidle")
    page.get_by_label("Difficulty", exact=True).select_option("medium")
    page.wait_for_load_state("networkidle")
    page.get_by_label("Source", exact=True).select_option("AI practice")
    page.wait_for_load_state("networkidle")
    expect(page.get_by_test_id("question-total")).not_to_have_text("0 question(s)")
    expect(page.get_by_test_id("question-card").first).to_contain_text("Infosys", timeout=15000)
    expect(page.get_by_test_id("question-card").first).to_contain_text("Runnable")
    card = page.get_by_test_id("question-card").first
    card.get_by_test_id("open-editor").click()
    card.get_by_test_id("run-code").click()
    expect(card.get_by_test_id("test-results")).to_be_visible(timeout=20000)

    # Timed coding test: write a real solution for the first question and run it
    go(page, "/practice/test/")
    page.locator("#tcomp").select_option(label="Infosys")
    page.locator("#tcount").select_option("2")
    page.get_by_test_id("start-test").click()
    expect(page.get_by_test_id("timer")).to_be_visible(timeout=15000)
    editor = page.locator(".cm-content").first
    editor.click()
    page.keyboard.press("Control+A")
    page.keyboard.press("Delete")
    title = page.locator("p.font-serif.text-lg").first.inner_text().strip()
    page.keyboard.insert_text(known_solution(title) or "import sys\nprint(len(sys.stdin.read().split()))\n")
    page.get_by_test_id("run-code").click()
    expect(page.get_by_test_id("test-results")).to_be_visible(timeout=20000)
    shot(page, vp, "04_coding_test", full=True)
    page.get_by_test_id("submit-code").click()
    expect(page.get_by_text("Saved answer:")).to_be_visible(timeout=20000)
    page.get_by_test_id("finish-test").click()
    expect(page.get_by_test_id("test-score")).to_be_visible(timeout=15000)

    # Mock interview: three answers, then the report for this session only
    go(page, "/interview/")
    page.locator("#irole").select_option("data_engineer")
    page.get_by_role("button", name="Start interview").click()
    expect(page.get_by_label("Your answer")).to_be_visible(timeout=20000)
    answers = [
        "I am Rahul, a final year computer science student at NMIT. I like building data pipelines. For example, in my project I cleaned CSV data with pandas and loaded it into MySQL because the dashboard needed clean tables.",
        "In my Smart Notes API I used FastAPI with JWT login and a normalised MySQL schema. The result was fast search, because I added an index on the tag table and used joins instead of loops.",
        "A primary key uniquely identifies each row, for example a student id. A foreign key points to a primary key in another table, which keeps the data consistent. However, too many joins can slow queries.",
    ]
    for a in answers:
        box = page.get_by_label("Your answer")
        if not box.count():
            break
        box.fill(a)
        page.get_by_role("button", name="Submit").click()
        expect(page.get_by_label("Your answer").or_(page.get_by_text("Mock interview report"))).to_have_count(1, timeout=20000)
        expect(page.get_by_label("Your answer")).to_have_value("", timeout=20000) if page.get_by_label("Your answer").count() else None
        page.wait_for_timeout(300)
    if page.get_by_role("button", name="End and see report").count():
        page.get_by_role("button", name="End and see report").click()
    expect(page.get_by_text("Mock interview report")).to_be_visible(timeout=20000)
    expect(page.get_by_text("This report is built only from the answers in this session.")).to_be_visible()
    shot(page, vp, "05_interview_report", full=True)

    # Assistant: a free-form question
    go(page, "/assistant/")
    page.get_by_test_id("chat-input").fill("What is a deadlock and how do I explain it in an interview?")
    page.get_by_test_id("chat-send").click()
    expect(page.get_by_test_id("assistant-msg").last).to_be_visible(timeout=60000)
    page.get_by_test_id("chat-input").fill("What does the Infosys online test cover?")
    page.get_by_test_id("chat-send").click()
    expect(page.get_by_test_id("assistant-msg").nth(1)).to_be_visible(timeout=60000)
    shot(page, vp, "06_assistant")

    # Log out from the sidebar menu, log back in, log out from Settings
    log_out_from_menu(page, vp)
    shot(page, vp, "01_login")
    log_in(page, email)
    expect(page.get_by_role("heading", name="Hi Rahul.")).to_be_visible(timeout=15000)
    page.wait_for_load_state("networkidle")
    shot(page, vp, "02_dashboard")
    go(page, "/settings/")
    page.get_by_test_id("settings-logout").click()
    expect(page.get_by_text("You have been logged out")).to_be_visible(timeout=10000)
    go(page, "/dashboard/")
    expect(page).to_have_url(f"{BASE}/login/?next=%2Fdashboard%2F", timeout=10000)


def mobile(page: Page, vp: str = "mobile"):
    email = f"e2e-m-{uuid.uuid4().hex[:8]}@example.com"
    sign_up(page, vp, email)
    for path, name in [("/dashboard/", "02_dashboard"), ("/gaps/", "03_skill_gap"), ("/practice/", "04_practice"),
                       ("/practice/test/", "04b_tests"), ("/interview/", "05_interview"), ("/assistant/", "06_assistant")]:
        go(page, path)
        page.wait_for_timeout(600)
        shot(page, vp, name)
    log_out_from_menu(page, vp)
    shot(page, vp, "01_login")


def main():
    problems = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        for vp, size, fn in [("desktop", {"width": 1440, "height": 900}, desktop), ("mobile", {"width": 390, "height": 844}, mobile)]:
            if ONLY and ONLY != vp:
                continue
            ctx = browser.new_context(viewport=size, device_scale_factor=2 if vp == "mobile" else 1)
            page = ctx.new_page()
            page.on("console", lambda m, vp=vp: m.type == "error" and problems.append(f"{vp} console: {m.text}"))
            page.on("pageerror", lambda e, vp=vp: problems.append(f"{vp} pageerror: {e}"))
            page.on("response", lambda r, vp=vp: "/api/" in r.url and r.status >= 400 and not (r.status == 401 and "/api/auth/me" in r.url)
                    and problems.append(f"{vp} http {r.status} {r.url}"))
            try:
                fn(page)
            except Exception:
                page.screenshot(path=str(SHOTS / f"{vp}_FAILED.png"), full_page=True)
                raise
            ctx.close()
        browser.close()
    print("problems:", len(problems))
    for x in problems:
        print("  ", x)
    if problems:
        sys.exit(1)
    print("JOURNEY OK")


if __name__ == "__main__":
    main()
