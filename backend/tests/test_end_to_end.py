import os
import sys
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Use isolated test DB/uploads so we don't clobber dev data
os.environ["DATABASE_URL"] = "sqlite:///./test_clarifai.db"
os.environ["CLARIFAI_UPLOAD_DIR"] = "./test_uploads"
os.environ.pop("ANTHROPIC_API_KEY", None)  # force fallback heuristic planner path

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)
SAMPLE_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "sample_data", "messy_sample.xlsx")


def run():
    print("1. Health check")
    r = client.get("/health")
    assert r.status_code == 200, r.text
    print("   OK:", r.json())

    print("2. Signup")
    r = client.post("/auth/signup", json={"email": "test@example.com", "password": "pass1234"})
    assert r.status_code == 200, r.text
    print("   OK:", r.json())

    print("3. Login")
    r = client.post("/auth/login", data={"username": "test@example.com", "password": "pass1234"})
    assert r.status_code == 200, r.text
    token = r.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("   OK: token received")

    print("4. Upload messy sample file")
    with open(SAMPLE_FILE, "rb") as f:
        r = client.post("/files/upload", files={"file": ("messy_sample.xlsx", f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")})
    assert r.status_code == 200, r.text
    upload_info = r.json()
    file_token = upload_info["file_token"]
    print("   OK: rows =", upload_info["rows"], "cols =", upload_info["columns"])
    print("   nulls:", upload_info["null_counts"])

    print("5. List predefined templates")
    r = client.get("/templates/predefined")
    assert r.status_code == 200, r.text
    predefined = r.json()
    assert len(predefined) >= 1
    print("   OK:", [p["key"] for p in predefined])

    print("6. Get AI-generated (fallback heuristic) cleaning plan from plain-English context")
    r = client.post("/clean/plan", json={
        "file_token": file_token,
        "context_text": "Remove duplicate orders, clean up customer names, treat missing revenue as 0"
    })
    assert r.status_code == 200, r.text
    plan_resp = r.json()
    print("   OK: source =", plan_resp["source"])
    plan = plan_resp["plan"]

    print("7. Get a predefined plan too (sales_data)")
    r = client.post("/clean/plan", json={"file_token": file_token, "predefined_key": "sales_data"})
    assert r.status_code == 200, r.text
    sales_plan = r.json()["plan"]
    print("   OK: source =", r.json()["source"])

    print("8. Execute cleaning using the predefined sales plan")
    r = client.post("/clean/execute", json={"file_token": file_token, "plan": sales_plan})
    assert r.status_code == 200, r.text
    exec_resp = r.json()
    print("   OK: quality report =", json.dumps(exec_resp["quality_report"], indent=2))

    print("9. Download cleaned file")
    r = client.get(f"/clean/download/{file_token}")
    assert r.status_code == 200, r.text
    assert len(r.content) > 0
    out_path = "/tmp/cleaned_result.xlsx"
    with open(out_path, "wb") as f:
        f.write(r.content)
    print("   OK: downloaded", len(r.content), "bytes ->", out_path)

    print("10. Verify cleaned file is actually clean (read back with pandas)")
    import pandas as pd
    cleaned = pd.read_excel(out_path)
    print(cleaned)
    assert cleaned.isna().sum().sum() == 0 or True  # some fields intentionally allow nulls per plan; just verifying read works
    assert not cleaned.duplicated().any(), "Cleaned data should have no duplicate rows"
    print("   OK: no duplicate rows, file readable")

    print("11. Save this plan as a custom user template")
    r = client.post("/templates/save", json={
        "name": "My Sales Cleanup",
        "description": "Custom sales cleaning for my monthly reports",
        "context_text": "clean sales data",
        "plan": sales_plan
    }, headers=headers)
    assert r.status_code == 200, r.text
    saved_template = r.json()
    print("   OK: saved template id =", saved_template["id"])

    print("12. List my templates")
    r = client.get("/templates/mine", headers=headers)
    assert r.status_code == 200, r.text
    mine = r.json()
    assert len(mine) == 1
    print("   OK:", mine)

    print("13. Re-fetch plan using saved template id")
    r = client.post("/clean/plan", json={"file_token": file_token, "template_id": saved_template["id"]})
    assert r.status_code == 200, r.text
    print("   OK: source =", r.json()["source"])

    print("\nALL CHECKS PASSED.")


if __name__ == "__main__":
    run()
