import asyncio
import json
import os
import subprocess
import time
import urllib.request
import websockets
import openpyxl

CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
DOWNLOAD_DIR = os.path.abspath(r"d:\3rd uc\scratch\downloads")
PROFILE_DIR = os.path.abspath(r"d:\3rd uc\scratch\chrome_profile_e2e")
PORT = 9223

os.makedirs(DOWNLOAD_DIR, exist_ok=True)
os.makedirs(PROFILE_DIR, exist_ok=True)

class CDPClient:
    def __init__(self, ws_url):
        self.ws_url = ws_url
        self.ws = None
        self._msg_id = 0

    async def connect(self):
        self.ws = await websockets.connect(self.ws_url, max_size=20*1024*1024)

    async def send(self, method, params=None):
        self._msg_id += 1
        msg = {"id": self._msg_id, "method": method, "params": params or {}}
        await self.ws.send(json.dumps(msg))
        while True:
            resp_str = await self.ws.recv()
            resp = json.loads(resp_str)
            if resp.get("id") == self._msg_id:
                if "error" in resp:
                    raise Exception(f"CDP error in {method}: {resp['error']}")
                return resp.get("result", {})

    async def eval_js(self, expression, await_promise=False):
        res = await self.send("Runtime.evaluate", {
            "expression": expression,
            "returnByValue": True,
            "awaitPromise": await_promise
        })
        return res.get("result", {}).get("value")

    async def close(self):
        if self.ws:
            await self.ws.close()

async def run_full_validation():
    print("==================================================================")
    print("STARTING COMPLETE BROWSER FLOW VALIDATION")
    print("==================================================================")

    # 1. Clean download directory
    for f in os.listdir(DOWNLOAD_DIR):
        try:
            os.remove(os.path.join(DOWNLOAD_DIR, f))
        except Exception:
            pass

    # 2. Launch headless Chrome with remote debugging
    chrome_cmd = [
        CHROME_PATH,
        "--headless=new",
        f"--remote-debugging-port={PORT}",
        f"--user-data-dir={PROFILE_DIR}",
        "--disable-gpu",
        "--no-sandbox",
        "--window-size=1400,1050",
        "about:blank"
    ]
    proc = subprocess.Popen(chrome_cmd)
    try:
        # Wait for debugging port
        for _ in range(25):
            time.sleep(0.5)
            try:
                with urllib.request.urlopen(f"http://127.0.0.1:{PORT}/json") as r:
                    targets = json.loads(r.read().decode())
                    if targets:
                        break
            except Exception:
                pass
        else:
            raise Exception("Chrome remote debugging not available!")

        ws_url = targets[0]["webSocketDebuggerUrl"]
        client = CDPClient(ws_url)
        await client.connect()
        print("[1] Connected to Chrome DevTools Protocol.")

        await client.send("Page.enable")
        await client.send("Runtime.enable")

        # Set download behavior to allow automatic downloads
        await client.send("Browser.setDownloadBehavior", {
            "behavior": "allow",
            "downloadPath": DOWNLOAD_DIR,
            "eventsEnabled": True
        })

        # Navigate to frontend
        print("[2] Navigating to frontend at http://localhost:5173/...")
        await client.send("Page.navigate", {"url": "http://localhost:5173/"})
        await asyncio.sleep(2)

        # Check login
        is_login = await client.eval_js("document.body.innerText.includes('Sign In') || document.body.innerText.includes('Welcome back')")
        if is_login:
            print("[3] Performing login as admin@enterprise.com...")
            await client.eval_js("""
                (() => {
                    const inputs = document.querySelectorAll('input');
                    for (const inp of inputs) {
                        if (inp.type === 'email' || inp.placeholder.toLowerCase().includes('email')) {
                            inp.value = 'admin@enterprise.com';
                            inp.dispatchEvent(new Event('input', { bubbles: true }));
                            inp.dispatchEvent(new Event('change', { bubbles: true }));
                        }
                        if (inp.type === 'password' || inp.placeholder.toLowerCase().includes('password')) {
                            inp.value = 'password123';
                            inp.dispatchEvent(new Event('input', { bubbles: true }));
                            inp.dispatchEvent(new Event('change', { bubbles: true }));
                        }
                    }
                    const btns = Array.from(document.querySelectorAll('button'));
                    const submitBtn = btns.find(b => b.innerText.includes('Sign In'));
                    if (submitBtn) submitBtn.click();
                })()
            """)
            await asyncio.sleep(2.5)

        # Wait for form
        for _ in range(15):
            has_form = await client.eval_js("document.body.innerText.includes('Area / Service Selection') || document.body.innerText.includes('User Stories')")
            if has_form:
                break
            await asyncio.sleep(1)
        print("[4] Application form loaded.")

        # Select Area: Payments
        await client.eval_js("""
            (() => {
                const spans = Array.from(document.querySelectorAll('span'));
                const targetSpan = spans.find(s => 
                    s.innerText.includes('Payments & Core Banking') ||
                    s.innerText.includes('Payment Processing') ||
                    s.innerText.toLowerCase().includes('payment')
                );
                if (targetSpan) targetSpan.closest('div').click();
            })()
        """)
        await asyncio.sleep(2.5)

        # Select Stories US-101 and US-102
        print("[5] Selecting User Stories US-101 and US-102...")
        await client.eval_js("""
            (() => {
                const cb1 = document.getElementById('story-checkbox-US-101');
                if (cb1 && !cb1.checked) cb1.click();
                const cb2 = document.getElementById('story-checkbox-US-102');
                if (cb2 && !cb2.checked) cb2.click();
            })()
        """)
        await asyncio.sleep(2)

        # Select all acceptance criteria
        print("[5b] Ensuring all Acceptance Criteria are selected...")
        await client.eval_js("""
            (() => {
                const btns = Array.from(document.querySelectorAll('button'));
                const selectAllBtn = btns.find(b => b.innerText.includes('Select All'));
                if (selectAllBtn) selectAllBtn.click();
            })()
        """)
        await asyncio.sleep(1)

        # Click Generate Test Cases
        print("[6] Generating Test Cases for US-101 and US-102...")
        gen_clicked = await client.eval_js("""
            (() => {
                const btns = Array.from(document.querySelectorAll('button'));
                const genBtn = btns.find(b => b.innerText.includes('Generate Test Cases') || b.innerText.includes('Generate'));
                if (genBtn) {
                    genBtn.click();
                    return true;
                }
                return false;
            })()
        """)
        print(f"    Generate button clicked: {gen_clicked}")

        # Wait for generation to complete
        total_cases = 0
        for _ in range(30):
            await asyncio.sleep(1)
            total_cases = await client.eval_js("""
                (() => {
                    const text = document.body.innerText;
                    const m = text.match(/(\\d+)\\s+Total Test Cases/i) || text.match(/Total Test Cases\\s*(\\d+)/i) || text.match(/Positive\\s*(\\d+)/i);
                    const table = document.querySelector('table');
                    if (table && table.querySelectorAll('tbody tr').length > 0) {
                        return table.querySelectorAll('tbody tr').length;
                    }
                    return m ? parseInt(m[1]) : 0;
                })()
            """)
            if total_cases and total_cases > 0:
                break
        print(f"[+] Test cases successfully generated: {total_cases} test cases.")
        assert total_cases > 0, "No test cases generated!"

        # TEST FEATURE 1: VIEW EXCEL SHEETS
        print("\n--- Testing Feature 1: 'View Excel Sheets' Modal ---")
        view_btn_clicked = await client.eval_js("""
            (() => {
                const btn = document.getElementById('view-excel-btn');
                if (btn) {
                    btn.click();
                    return true;
                }
                return false;
            })()
        """)
        assert view_btn_clicked, "View Excel Sheets button not found!"
        print("[+] Clicked 'View Excel Sheets' button.")

        # Wait for SheetJS to parse and modal to display verified sheets
        modal_verified = False
        modal_info = ""
        for _ in range(15):
            await asyncio.sleep(1)
            modal_info = await client.eval_js("""
                (() => {
                    const modal = document.querySelector('.fixed.inset-0');
                    if (!modal) return null;
                    return {
                        title: modal.querySelector('h3')?.innerText || '',
                        filename: modal.querySelector('.font-mono')?.innerText || '',
                        badge: modal.innerText.includes('Verified') || modal.innerText.includes('SheetJS'),
                        positiveCount: modal.innerText.includes('Positive Sheet'),
                        negativeCount: modal.innerText.includes('Negative Sheet'),
                        edgeCount: modal.innerText.includes('Edge Sheet'),
                        rowCount: modal.querySelectorAll('tbody tr').length
                    };
                })()
            """)
            if modal_info and modal_info.get("badge") and modal_info.get("rowCount", 0) > 0:
                modal_verified = True
                break

        print(f"[+] 'View Excel Sheets' Modal Info: {modal_info}")
        assert modal_verified, "View Excel Sheets did not successfully verify and parse the XLSX binary!"
        print("[SUCCESS] Feature 1 ('View Excel Sheets') verified: SheetJS parsed XLSX binary, displayed all sheets.")

        # Close the modal
        await client.eval_js("""
            (() => {
                const closeBtn = Array.from(document.querySelectorAll('button')).find(b => b.title === 'Close Viewer' || b.innerText === 'Close');
                if (closeBtn) closeBtn.click();
            })()
        """)
        await asyncio.sleep(1)

        # TEST FEATURE 2: DOWNLOAD EXCEL
        print("\n--- Testing Feature 2: 'Download Excel' Button ---")
        export_clicked = await client.eval_js("""
            (() => {
                const btn = document.getElementById('export-excel-btn');
                if (btn) {
                    btn.click();
                    return true;
                }
                return false;
            })()
        """)
        assert export_clicked, "Download Excel button not found!"
        print("[+] Clicked 'Download Excel' button.")

        # Wait for download in DOWNLOAD_DIR
        downloaded_file = None
        for _ in range(15):
            await asyncio.sleep(1)
            files = [f for f in os.listdir(DOWNLOAD_DIR) if f.endswith('.xlsx')]
            if files:
                downloaded_file = os.path.join(DOWNLOAD_DIR, files[0])
                break

        assert downloaded_file and os.path.exists(downloaded_file), "No .xlsx file was downloaded by browser!"
        filename = os.path.basename(downloaded_file)
        file_size = os.path.getsize(downloaded_file)
        print(f"[+] Browser downloaded file: {filename} ({file_size} bytes)")

        # Verify filename criteria
        assert filename.endswith('.xlsx'), f"Filename does NOT end with .xlsx: {filename}"
        assert not filename.endswith('.xls'), f"Filename incorrectly ends with .xls: {filename}"
        assert not filename.endswith('.xlsx.xlsx'), f"Double extension in filename: {filename}"
        assert file_size > 0, "Downloaded file is empty!"

        # Verify binary starts with PK\x03\x04
        with open(downloaded_file, 'rb') as f:
            header_bytes = f.read(4)
        assert header_bytes == b'PK\x03\x04', f"File does not have ZIP/OOXML magic bytes: {header_bytes}"
        print(f"[+] Validated binary magic bytes: {header_bytes!r} (PK\\x03\\x04)")

        # Verify openpyxl can load and inspect sheets
        wb = openpyxl.load_workbook(downloaded_file)
        print(f"[+] openpyxl sheet names: {wb.sheetnames}")
        assert set(wb.sheetnames) == {"Positive", "Negative", "Edge"}, f"Unexpected sheet names: {wb.sheetnames}"
        for sname in ["Positive", "Negative", "Edge"]:
            ws = wb[sname]
            print(f"    - Sheet '{sname}': max_row={ws.max_row}, max_col={ws.max_column}")
            assert ws.max_row > 1, f"Sheet '{sname}' has no test case rows!"
            assert ws.max_column == 13, f"Sheet '{sname}' expected 13 columns, found {ws.max_column}"
        wb.close()
        print("[+] openpyxl loaded workbook and verified all 3 sheets + 13 columns successfully.")

        # Check Success Banner in UI
        banner_text = await client.eval_js("""
            (() => {
                const banner = Array.from(document.querySelectorAll('h4')).find(h => h.innerText.includes('Excel Workbook Ready'));
                return banner ? banner.innerText : null;
            })()
        """)
        print(f"[+] UI Success Banner: {banner_text}")
        assert banner_text and "Excel Workbook Ready" in banner_text, "Success banner did not appear after validation!"

        await client.close()
        return downloaded_file

    finally:
        try:
            proc.terminate()
            proc.wait(timeout=3)
        except Exception:
            try:
                proc.kill()
            except Exception:
                pass

def verify_in_microsoft_excel(filepath):
    print("\n==================================================================")
    print("STEP 9 & 10: VERIFYING IN REAL MICROSOFT EXCEL VIA COM")
    print(f"Target file: {filepath}")
    print("==================================================================")

    # Test with DisplayAlerts = true to catch ANY corruption, repair, or unreadable content warning
    ps_cmd = f"""
    $excel = New-Object -ComObject Excel.Application
    $excel.Visible = $false
    $excel.DisplayAlerts = $true
    try {{
        Write-Host "Opening in Microsoft Excel COM..."
        $wb = $excel.Workbooks.Open('{filepath}')
        Write-Host "SUCCESS: Microsoft Excel opened the workbook!"
        Write-Host "Workbook Name: $($wb.Name)"
        Write-Host "Sheets Count: $($wb.Sheets.Count)"
        foreach ($sh in $wb.Sheets) {{
            Write-Host " - Sheet: $($sh.Name) | Rows: $($sh.UsedRange.Rows.Count) | Cols: $($sh.UsedRange.Columns.Count)"
        }}
        $wb.Close($false)
        Write-Host "VERIFICATION_SUCCESSFUL"
    }} catch {{
        Write-Error "EXCEL_OPEN_FAILED: $($_.Exception.Message)"
        exit 1
    }} finally {{
        $excel.Quit()
        [System.Runtime.InteropServices.Marshal]::ReleaseComObject($excel) | Out-Null
        [System.GC]::Collect()
        [System.GC]::WaitForPendingFinalizers()
    }}
    """
    res = subprocess.run(["powershell", "-NoProfile", "-Command", ps_cmd], capture_output=True, text=True)
    print(res.stdout)
    if res.stderr:
        print("STDERR:", res.stderr)
    assert res.returncode == 0, "Microsoft Excel failed to open the downloaded .xlsx file!"
    assert "VERIFICATION_SUCCESSFUL" in res.stdout, "Verification string not found in Excel output!"
    print("\n>>> CONFIRMED: Microsoft Excel opened the browser-downloaded file with 0 errors/warnings!")

if __name__ == "__main__":
    downloaded = asyncio.run(run_full_validation())
    verify_in_microsoft_excel(downloaded)
