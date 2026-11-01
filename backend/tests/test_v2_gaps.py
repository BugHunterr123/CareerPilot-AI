"""Skill gap: role x company merge, origin labels, sources, and different inputs give different results."""
import pytest


def _cid(client, h, slug):
    return next(c["id"] for c in client.get("/api/companies", headers=h).json()["companies"] if c["slug"] == slug)


def _gap(client, h, role, slug=None, jd=""):
    body = {"role_key": role, "company_id": _cid(client, h, slug) if slug else None, "job_description": jd}
    r = client.post("/api/gaps", headers=h, json=body)
    assert r.status_code in (200, 201), r.text
    return r.json()


def test_summary_matches_the_selection(client, student):
    g = _gap(client, student, "data_engineer", "infosys")
    assert g["summary"]["role"] == "Data Engineer" and g["summary"]["company"] == "Infosys"
    assert g["role_key"] == "data_engineer" and g["company_id"] == _cid(client, student, "infosys")


def test_different_role_company_combos_give_different_results(client, student):
    de_inf = _gap(client, student, "data_engineer", "infosys")
    sd_acc = _gap(client, student, "software_developer", "accenture")
    de_acc = _gap(client, student, "data_engineer", "accenture")
    sd_inf = _gap(client, student, "software_developer", "infosys")
    sets = [frozenset(i["skill"] for i in g["items"]) for g in (de_inf, sd_acc, de_acc, sd_inf)]
    assert len(set(sets)) == 4, "every combination must produce its own requirement set"
    assert "ETL" in sets[0] and "ETL" not in sets[1]


def test_role_skills_come_from_the_role(client, student):
    de = _gap(client, student, "data_engineer")
    skills = {i["skill"] for i in de["items"]}
    assert {"ETL", "Data Modelling", "Data Warehousing", "Apache Spark"} <= skills
    assert all(i["origin"] == "role" for i in de["items"])
    assert de["summary"]["company_stages"] == [] and de["summary"]["from_company"] == 0


def test_company_items_carry_stage_topics_and_sources(client, student):
    g = _gap(client, student, "data_engineer", "infosys")
    company_items = [i for i in g["items"] if i["origin"] in ("company", "both")]
    assert company_items, "Infosys stages must add requirements"
    assert any(i["skill"] == "Pseudocode" for i in company_items)
    for i in company_items:
        assert i["company_topics"], i["skill"]
        for t in i["company_topics"]:
            assert t["stage"] and t["label"]
    urls = [s["url"] for st in g["summary"]["company_stages"] for s in st["sources"]]
    assert urls and all(u.startswith("http") for u in urls)


def test_both_origin_when_role_and_company_agree(client, student):
    g = _gap(client, student, "software_developer", "accenture")
    both = [i for i in g["items"] if i["origin"] == "both"]
    assert both and g["summary"]["from_both"] == len(both)
    assert g["summary"]["from_role"] + g["summary"]["from_company"] + g["summary"]["from_both"] + g["summary"].get("from_jd", 0) == g["summary"]["total"]


def test_job_description_adds_requirements(client, student):
    g = _gap(client, student, "software_developer", None, jd="Must know Kubernetes and Docker. Kafka is a plus.")
    jd_items = [i for i in g["items"] if i["origin"] == "jd" or "Job description" in " ".join(i["reasons"])]
    assert jd_items


@pytest.mark.parametrize("role", ["data_analyst", "qa_automation", "tech_support", "ml_engineer"])
def test_every_role_has_requirements(client, student, role):
    g = _gap(client, student, role)
    assert g["summary"]["total"] >= 5 and g["summary"]["role"]
