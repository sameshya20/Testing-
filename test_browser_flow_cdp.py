import asyncio
import json
import os
import subprocess
import time
import urllib.request
import websockets

CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
DOWNLOAD_DIR = os.path.abspath(r"d:\3rd uc\scratch\downloads")
PROFILE_DIR = os.path.abspath(r"d:\3rd uc\scratch\chrome_profile")
PORT = 9222

os.makedirs(DOWNLOAD_DIR, exist_ok=True)
os.makedirs(PROFILE_DIR, exist_ok=True)

class CDPClient:
    def __init__(self, ws_url):
        self.ws_url = ws_url
        self.ws = None
        self._msg_id = 0

    async def connect(self):
        self.ws = await websockets.connect(self.ws_url, max_size=10*1024*1024)

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

async def run_browser_test():
    print(f"[1] Starting Chrome headless...")
    # Clean previous downloads
    for f in os.listdir(DOWNLOAD_DIR):
        try:
            os.remove(os.path.join(DOWNLOAD_DIR, f))
        except Exception:
            pass

    chrome_cmd = [
        CHROME_PATH,
        "--headless=new",
        f"--remote-debugging-port={PORT}",
        f"--user-data-dir={PROFILE_DIR}",
        "--disable-gpu",
        "--no-sandbox",
        "--window-size=1280,1024",
        "about:blank"
    ]
    proc = subprocess.Popen(chrome_cmd)
    try:
        # Wait for debugging port
        for _ in range(20):
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
        print("[2] Connected to Chrome DevTools Protocol.")

        # Enable Page and Runtime
        await client.send("Page.enable")
        await client.send("Runtime.enable")

        # Set download directory
        await client.send("Browser.setDownloadBehavior", {
            "behavior": "allow",
            "downloadPath": DOWNLOAD_DIR,
            "eventsEnabled": True
        })

        # Navigate to frontend
        print("[3] Navigating to http://localhost:5173/...")
        await client.send("Page.navigate", {"url": "http://localhost:5173/"})
        await asyncio.sleep(2)

        # Check if login is needed
        is_login = await client.eval_js("document.body.innerText.includes('Sign In') || document.body.innerText.includes('Welcome back')")
        print(f"    Is login page displayed? {is_login}")
        if is_login:
            print("    Entering login credentials...")
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

        # Wait for Application Form to be ready
        print("[4] Checking form UI...")
        for _ in range(15):
            has_form = await client.eval_js("document.body.innerText.includes('Area / Service Selection') || document.body.innerText.includes('User Stories')")
            if has_form:
                break
            await asyncio.sleep(1)

        # Select Area: Click on Payments / Payment Processing in AreaSelector
        print("[5] Selecting Area in AreaSelector tree...")
        area_selected = await client.eval_js("""
            (() => {
                const spans = Array.from(document.querySelectorAll('span'));
                const targetSpan = spans.find(s => 
                    s.innerText.includes('Payments & Core Banking') ||
                    s.innerText.includes('Payment Processing') ||
                    s.innerText.toLowerCase().includes('payment') ||
                    s.innerText.includes('Fund Transfer')
                );
                if (targetSpan) {
                    targetSpan.closest('div').click();
                    return targetSpan.innerText;
                }
                // Fallback to any node in AreaSelector
                const anyNode = spans.find(s => s.parentElement && s.parentElement.className.includes('cursor-pointer') && s.innerText.trim().length > 4);
                if (anyNode) {
                    anyNode.closest('div').click();
                    return anyNode.innerText;
                }
                return null;
            })()
        """)
        print(f"    Area selected: {area_selected}")
        await asyncio.sleep(3)

        # Select User Stories: Wait for stories to appear and select US-101 and US-102
        print("[6] Selecting multiple User Stories (US-101 and US-102)...")
        await client.eval_js("""
            (() => {
                const cb1 = document.getElementById('story-checkbox-US-101');
                if (cb1 && !cb1.checked) cb1.click();
            })()
        """)
        await asyncio.sleep(2)

        await client.eval_js("""
            (() => {
                const cb2 = document.getElementById('story-checkbox-US-102');
                if (cb2 && !cb2.checked) cb2.click();
            })()
        """)
        await asyncio.sleep(2)

        stories_selected = await client.eval_js("""
            (() => {
                const checked = Array.from(document.querySelectorAll('input[type="checkbox"]:checked'))
                    .filter(cb => cb.id.startsWith('story-checkbox-'))
                    .map(cb => cb.id.replace('story-checkbox-', ''));
                return checked;
            })()
        """)
        print(f"    Selected User Stories: {stories_selected}")

        # Ensure all criteria are selected
        await client.eval_js("""
            (() => {
                const btns = Array.from(document.querySelectorAll('button'));
                const selectAllBtn = btns.find(b => b.innerText.includes('Select All'));
                if (selectAllBtn) selectAllBtn.click();
            })()
        """)
        await asyncio.sleep(1)

        # Check acceptance criteria grouping
        ac_summary = await client.eval_js("""
            (() => {
                const text = document.body.innerText;
                const countMatch = text.match(/(\\d+)\\s+of\\s+(\\d+)\\s+selected/i);
                return countMatch ? countMatch[0] : 'None';
            })()
        """)
        print(f"    Acceptance Criteria status: {ac_summary}")

        # Click Generate Test Cases button
        print("[7] Clicking 'Generate Test Cases'...")
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

        # Wait for test case generation to complete
        print("[8] Waiting for test cases to generate...")
        total_tc = 0
        for i in range(25):
            await asyncio.sleep(1)
            total_tc = await client.eval_js("""
                (() => {
                    const text = document.body.innerText;
                    const m = text.match(/(\\d+)\\s+Total Test Cases/i) || text.match(/Positive\\s*(\\d+)/i);
                    return m ? m[0] : null;
                })()
            """)
            if total_tc:
                print(f"    Test cases generated: {total_tc}")
                break

        await asyncio.sleep(2)

        # Click Export Excel button
        print("[9] Clicking 'Export Excel' button...")
        export_clicked = await client.eval_js("""
            (() => {
                const btn = document.getElementById('export-excel-btn') || 
                            Array.from(document.querySelectorAll('button')).find(b => b.innerText.toLowerCase().includes('excel'));
                if (btn) {
                    btn.click();
                    return true;
                }
                return false;
            })()
        """)
        print(f"    Export Excel clicked: {export_clicked}")

        # Wait for downloaded file in DOWNLOAD_DIR
        print("[10] Waiting for downloaded .xlsx file...")
        downloaded_file = None
        for i in range(15):
            await asyncio.sleep(1)
            files = [f for f in os.listdir(DOWNLOAD_DIR) if f.endswith('.xlsx')]
            if files:
                downloaded_file = os.path.join(DOWNLOAD_DIR, files[0])
                break

        assert downloaded_file and os.path.exists(downloaded_file), "No .xlsx file was downloaded by the browser!"
        file_size = os.path.getsize(downloaded_file)
        print(f"[+] Downloaded file: {os.path.basename(downloaded_file)} ({file_size} bytes)")
        assert file_size > 0, "Downloaded file is 0 bytes!"

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

if __name__ == "__main__":
    downloaded_file = asyncio.run(run_browser_test())
    print("\n--- Testing downloaded file in Microsoft Excel COM ---")
    ps_cmd = f"""
    $excel = New-Object -ComObject Excel.Application
    $excel.Visible = $false
    $excel.DisplayAlerts = $false
    try {{
        $wb = $excel.Workbooks.Open('{downloaded_file}')
        Write-Host "Excel COM opened file successfully!"
        Write-Host "Sheet count: $($wb.Sheets.Count)"
        foreach ($sh in $wb.Sheets) {{
            Write-Host " - Sheet: $($sh.Name) | Rows used: $($sh.UsedRange.Rows.Count)"
        }}
        $wb.Close($false)
        Write-Host "SUCCESS: Microsoft Excel verified the downloaded .xlsx file without errors!"
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
    assert res.returncode == 0, "Microsoft Excel failed to open the downloaded .xlsx file!"
    print("\n=======================================================")
    print("ALL TESTS PASSED: Browser UI -> Export -> Microsoft Excel")
    print("=======================================================")
