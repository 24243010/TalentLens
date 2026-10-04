import glob, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from engine import run_analysis


def _run():
    jd = open("samples/sample_jd.txt", encoding="utf-8").read()
    texts = {os.path.basename(p): open(p, encoding="utf-8").read() for p in glob.glob("samples/demo_resumes/*.txt")}
    return run_analysis(texts, jd)


def test_ranking_on_samples():
    res = _run()
    assert len(res) == 20
    assert res[0]["percentage"] >= res[-1]["percentage"]


def test_lavanya_is_top():
    res = _run()
    assert res[0]["resume_file"] == "Lavanya.txt" and res[0]["percentage"] == 100
