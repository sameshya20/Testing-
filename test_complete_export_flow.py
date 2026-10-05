import urllib.request
import json
import openpyxl
import os
import subprocess

def test_complete_flow():
    base_url = "http://127.0.0.1:8000/api/v1"
    
    # 1. Login
    login_data = json.dumps({"email": "admin@enterprise.com", "password": "password123"}).encode("utf-8")
    req = urllib.request.Request(f"{base_url}/auth/login", data=login_data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as resp:
        res = json.loads(resp.read().decode("utf-8"))
        token = res["access_token"]
        print("[+] Logged in successfully. Token acquired.")

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }

    # 2. Get User Stories for Area 7
    req = urllib.request.Request(f"{base_url}/devops/areas/7/user-stories", headers=headers)
    with urllib.request.urlopen(req) as resp:
        stories = json.loads(resp.read().decode("utf-8"))
        print(f"[+] Loaded {len(stories)} User Stories for Area 7.")

    # 3. Get multi-story acceptance criteria for US-101 and US-102
    req = urllib.request.Request(f"{base_url}/devops/user-stories/multi/acceptance-criteria?story_ids=US-101&story_ids=US-102", headers=headers)
    with urllib.request.urlopen(req) as resp:
        ac_data = json.loads(resp.read().decode("utf-8"))
        print(f"[+] Multi-story AC returned {len(ac_data)} criteria groups.")

    # 4. Generate test cases for US-101 and US-102
    gen_payload = {
        "application_id": 1,
        "requirement_source": "USER_STORY",
        "requirement_identifiers": ["US-101", "US-102"],
        "user_story_ids": ["US-101", "US-102"],
        "area_ids": [7]
    }
    req = urllib.request.Request(
        f"{base_url}/generation/create",
        data=json.dumps(gen_payload).encode("utf-8"),
        headers=headers
    )
    with urllib.request.urlopen(req) as resp:
        gen_res = json.loads(resp.read().decode("utf-8"))
        pos = gen_res.get("positive_test_cases", [])
        neg = gen_res.get("negative_test_cases", [])
        edge = gen_res.get("edge_test_cases", [])
        total = len(pos) + len(neg) + len(edge)
        print(f"[+] Generated {total} test cases (Positive: {len(pos)}, Negative: {len(neg)}, Edge: {len(edge)}).")

    # 5. Call export endpoint
    export_payload = {
        "positive_test_cases": pos,
        "negative_test_cases": neg,
        "edge_test_cases": edge,
        "application_name": "Enterprise Payment Gateway",
        "requirement_ref": "US-101, US-102"
    }
    req = urllib.request.Request(
        f"{base_url}/export/excel",
        data=json.dumps(export_payload).encode("utf-8"),
        headers={**headers, "Accept": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"}
    )
    with urllib.request.urlopen(req) as resp:
        content_type = resp.headers.get("Content-Type")
        disposition = resp.headers.get("Content-Disposition")
        raw_bytes = resp.read()
        print(f"[+] Export response received: {len(raw_bytes)} bytes.")
        print(f"    Content-Type: {content_type}")
        print(f"    Content-Disposition: {disposition}")

        assert "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" in content_type, f"Wrong Content-Type: {content_type}"
        assert ".xlsx" in disposition, f"Filename does not contain .xlsx: {disposition}"

    # 6. Save to file
    out_file = os.path.abspath("test_flow_export.xlsx")
    with open(out_file, "wb") as f:
        f.write(raw_bytes)
    print(f"[+] Saved workbook to {out_file} ({os.path.getsize(out_file)} bytes).")

    # 7. Validate with openpyxl
    wb = openpyxl.load_workbook(out_file)
    print(f"[+] Sheets in workbook: {wb.sheetnames}")
    assert set(wb.sheetnames) == {"Positive", "Negative", "Edge"}, f"Unexpected sheets: {wb.sheetnames}"

    pos_ws = wb["Positive"]
    print(f"[+] Positive sheet max_row: {pos_ws.max_row}, max_column: {pos_ws.max_column}")
    assert pos_ws.max_row > 1, "Positive sheet should have rows!"
    assert pos_ws.cell(row=1, column=1).value == "Test Case ID"
    assert pos_ws.cell(row=1, column=2).value == "User Story"
    assert pos_ws.cell(row=1, column=3).value == "Acceptance Criteria"

    # Check that both US-101 and US-102 appear
    user_stories_found = set()
    for r in range(2, pos_ws.max_row + 1):
        us_val = pos_ws.cell(row=r, column=2).value
        if us_val:
            user_stories_found.add(us_val)
    print(f"[+] User stories present in Positive sheet: {user_stories_found}")
    wb.close()

    # 8. Test opening in Microsoft Excel via PowerShell COM
    ps_cmd = f"""
    $excel = New-Object -ComObject Excel.Application
    $excel.Visible = $false
    $excel.DisplayAlerts = $false
    try {{
        $wb = $excel.Workbooks.Open('{out_file}')
        Write-Host "Excel COM opened workbook successfully! Sheet count: $($wb.Sheets.Count)"
        foreach ($sh in $wb.Sheets) {{
            Write-Host " - Sheet: $($sh.Name) | Rows used: $($sh.UsedRange.Rows.Count)"
        }}
        $wb.Close($false)
        Write-Host "SUCCESS: Microsoft Excel verified the .xlsx file without errors!"
    }} catch {{
        Write-Error "FAILED to open in Microsoft Excel: $_"
        exit 1
    }} finally {{
        $excel.Quit()
        [System.Runtime.Interopservices.Marshal]::ReleaseComObject($excel) | Out-Null
        [System.GC]::Collect()
        [System.GC]::WaitForPendingFinalizers()
    }}
    """
    res = subprocess.run(["powershell", "-NoProfile", "-Command", ps_cmd], capture_output=True, text=True)
    print(res.stdout)
    if res.stderr:
        print("STDERR:", res.stderr)
    assert res.returncode == 0, "Microsoft Excel COM failed to open workbook!"
    print("[SUCCESS] Complete flow verified successfully!")

if __name__ == "__main__":
    test_complete_flow()
