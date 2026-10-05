import httpx
from bs4 import BeautifulSoup
from typing import Tuple, Dict, Any, List, Optional
from app.schemas.test_case import ApplicationLinkPayload

BLOCKED_SCHEMES = ("javascript:", "data:", "file:", "vbscript:", "about:", "chrome:")

def normalize_url(url: str) -> str:
    """Normalizes URL for duplicate comparison and formatting."""
    clean = url.strip()
    if not (clean.lower().startswith("http://") or clean.lower().startswith("https://")):
        clean = f"https://{clean}"
    # Standardize scheme/host casing and remove trailing slash
    parts = clean.split("://", 1)
    scheme = parts[0].lower()
    rest = parts[1]
    if "/" in rest:
        host, path = rest.split("/", 1)
        clean_normalized = f"{scheme}://{host.lower()}/{path.rstrip('/')}"
    else:
        clean_normalized = f"{scheme}://{rest.lower()}".rstrip("/")
    return clean_normalized

def is_safe_url(url: str) -> bool:
    """Validates that URL scheme is safe and supported."""
    lowered = url.strip().lower()
    for blocked in BLOCKED_SCHEMES:
        if lowered.startswith(blocked):
            return False
    return lowered.startswith("http://") or lowered.startswith("https://") or "://" not in lowered

class WebContextExtractor:
    """Safely extracts HTML form inputs, field names, buttons, and context from multiple application links."""

    async def extract_single_url_context(self, link: ApplicationLinkPayload, default_index: int = 1) -> Dict[str, Any]:
        """Extracts DOM structure from a single application link independently."""
        raw_url = link.url.strip() if link.url else ""
        link_name = link.name.strip() if link.name and link.name.strip() else f"Application Page {default_index}"

        if not raw_url or not is_safe_url(raw_url):
            return {
                "name": link_name,
                "url": raw_url,
                "requirement_ref": link.requirement_ref,
                "status": "failed",
                "error": "Invalid URL or unsupported protocol",
                "detected_inputs": [],
                "detected_actions": [],
                "page_title": link_name
            }

        clean_url = normalize_url(raw_url)

        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
            async with httpx.AsyncClient(timeout=6.0, follow_redirects=True, verify=False) as client:
                response = await client.get(clean_url, headers=headers)

                if response.status_code >= 400:
                    return {
                        "name": link_name,
                        "url": clean_url,
                        "requirement_ref": link.requirement_ref,
                        "status": "failed",
                        "error": f"HTTP status {response.status_code}",
                        "detected_inputs": [],
                        "detailed_inputs": [],
                        "detected_actions": [],
                        "detailed_actions": [],
                        "observed_errors": [],
                        "page_title": link_name
                    }

                html = response.text
                soup = BeautifulSoup(html, "html.parser")

                title = soup.title.string.strip() if soup.title and soup.title.string else link_name
                forms = soup.find_all("form")
                inputs = soup.find_all(["input", "select", "textarea"])
                buttons = soup.find_all(["button", "input", "a"])
                headings = [h.get_text(strip=True) for h in soup.find_all(["h1", "h2", "h3"]) if h.get_text(strip=True)]

                detailed_inputs = []
                extracted_inputs = []
                for inp in inputs:
                    inp_type = inp.get("type", "text")
                    if inp_type in ("hidden", "submit", "button", "reset"):
                        continue
                    field_id = inp.get("id") or inp.get("name") or inp.get("placeholder") or inp_type
                    field_name = inp.get("name") or inp.get("id") or inp.get("placeholder") or field_id
                    placeholder = inp.get("placeholder") or ""
                    
                    # Find label if available
                    label_text = ""
                    if inp.get("id"):
                        lbl = soup.find("label", attrs={"for": inp.get("id")})
                        if lbl:
                            label_text = lbl.get_text(strip=True)
                    if not label_text and inp.parent and inp.parent.name == "label":
                        label_text = inp.parent.get_text(strip=True)

                    display_name = label_text or placeholder or field_name or field_id

                    if display_name:
                        extracted_inputs.append(str(display_name))
                        detailed_inputs.append({
                            "id": str(field_id),
                            "name": str(field_name),
                            "label": str(label_text),
                            "placeholder": str(placeholder),
                            "type": str(inp_type),
                            "display_name": str(display_name)
                        })

                detailed_actions = []
                extracted_actions = []
                for btn in buttons:
                    is_btn = btn.name in ("button", "a") or btn.get("type") in ("submit", "button")
                    if not is_btn:
                        continue
                    btn_text = btn.get_text(strip=True) or btn.get("value") or btn.get("id") or btn.get("name")
                    btn_id = btn.get("id") or btn.get("name") or btn_text
                    if btn_text and len(btn_text) < 40 and btn_text.lower() not in ("http", "https", "javascript:void(0)"):
                        extracted_actions.append(str(btn_text))
                        detailed_actions.append({
                            "id": str(btn_id),
                            "text": str(btn_text)
                        })

                # Detect validation/error messages if present in HTML
                error_nodes = soup.find_all(lambda tag: tag.get("class") and any("error" in str(c).lower() or "alert" in str(c).lower() or "validation" in str(c).lower() for c in (tag.get("class") if isinstance(tag.get("class"), list) else [tag.get("class")])))
                observed_errors = [e.get_text(strip=True) for e in error_nodes if e.get_text(strip=True) and len(e.get_text(strip=True)) < 100]

                # --- SPA Fallback Extraction (e.g. React/Vite client-side bundles like SauceDemo) ---
                if len(detailed_inputs) < 2:
                    script_srcs = [s.get("src") for s in soup.find_all("script") if s.get("src")]
                    for s_src in script_srcs[:3]:
                        try:
                            if s_src.startswith("http://") or s_src.startswith("https://"):
                                js_url = s_src
                            else:
                                base_root = clean_url.rsplit('/', 1)[0] if clean_url.endswith('/') else clean_url
                                js_url = f"{clean_url.rstrip('/')}/{s_src.lstrip('/')}"
                            
                            js_resp = await client.get(js_url, headers=headers)
                            if js_resp.status_code == 200:
                                js_text = js_resp.text
                                import re
                                placeholders = set(re.findall(r'placeholder:[`"\']([^`"\']+)[`"\']', js_text))
                                names = set(re.findall(r'name:[`"\']([^`"\']+)[`"\']', js_text))
                                ids = set(re.findall(r'id:[`"\']([^`"\']+)[`"\']', js_text))
                                test_ids = set(re.findall(r'testId:[`"\']([^`"\']+)[`"\']', js_text))
                                values = set(re.findall(r'value:[`"\']([^`"\']+)[`"\']', js_text))
                                js_errors = set(re.findall(r'Epic sadface: ([^"<`]+)', js_text))

                                # Process extracted placeholders/inputs
                                for p in placeholders:
                                    if p and len(p) < 40 and p not in extracted_inputs:
                                        extracted_inputs.append(p)
                                        detailed_inputs.append({"id": p.lower().replace(" ", "-"), "name": p.lower().replace(" ", "_"), "placeholder": p, "display_name": p, "type": "text"})
                                for t_id in test_ids:
                                    if t_id in ("username", "password", "firstName", "lastName", "postalCode") and t_id not in extracted_inputs:
                                        extracted_inputs.append(t_id)
                                        detailed_inputs.append({"id": t_id, "name": t_id, "placeholder": t_id.capitalize(), "display_name": t_id, "type": "text"})
                                
                                # Process buttons / actions
                                for val in values:
                                    if val in ("Login", "Continue", "Submit", "Checkout", "Finish", "Cancel") and val not in extracted_actions:
                                        extracted_actions.append(val)
                                        detailed_actions.append({"id": val.lower(), "text": val})
                                if "login-button" in test_ids and "Login" not in extracted_actions:
                                    extracted_actions.append("Login")
                                    detailed_actions.append({"id": "login-button", "text": "Login"})
                                
                                # Process observed errors
                                for err in js_errors:
                                    full_err = f"Epic sadface: {err.strip()}"
                                    if full_err not in observed_errors:
                                        observed_errors.append(full_err)
                        except Exception:
                            pass

                return {
                    "name": link_name,
                    "url": clean_url,
                    "requirement_ref": link.requirement_ref,
                    "status": "success",
                    "page_title": title,
                    "form_count": len(forms),
                    "headings": headings[:5],
                    "detected_inputs": list(dict.fromkeys(extracted_inputs))[:15],
                    "detailed_inputs": detailed_inputs[:10],
                    "detected_actions": list(dict.fromkeys(extracted_actions))[:10],
                    "detailed_actions": detailed_actions[:10],
                    "observed_errors": list(dict.fromkeys(observed_errors))[:5],
                    "raw_text_snippet": soup.get_text()[:500].strip()
                }

        except Exception as e:
            return {
                "name": link_name,
                "url": clean_url,
                "requirement_ref": link.requirement_ref,
                "status": "failed",
                "error": f"Application link could not be reached: {str(e)}",
                "detected_inputs": [],
                "detailed_inputs": [],
                "detected_actions": [],
                "detailed_actions": [],
                "observed_errors": [],
                "page_title": link_name
            }

    async def extract_multi_context(
        self,
        links: Optional[List[ApplicationLinkPayload]]
    ) -> Tuple[bool, str, List[Dict[str, Any]]]:
        """
        Extracts DOM context from multiple application links independently.
        Returns: (any_analyzed: bool, summary_message: str, page_contexts: List[Dict])
        """
        if not links:
            return (
                False,
                "No application links provided. Requirements analyzed using application specification.",
                []
            )

        # Deduplicate links by normalized URL
        seen_urls = set()
        unique_links: List[ApplicationLinkPayload] = []

        for idx, item in enumerate(links, 1):
            if not item.url or not item.url.strip():
                continue
            if not is_safe_url(item.url):
                continue
            norm = normalize_url(item.url)
            if norm not in seen_urls:
                seen_urls.add(norm)
                unique_links.append(item)

        if not unique_links:
            return (
                False,
                "No valid application links provided.",
                []
            )

        page_contexts = []
        successful_count = 0

        for idx, link in enumerate(unique_links, start=1):
            context = await self.extract_single_url_context(link, default_index=idx)
            page_contexts.append(context)
            if context.get("status") == "success":
                successful_count += 1

        total = len(unique_links)
        if successful_count == total and total > 0:
            msg = f"{total} of {total} application link(s) successfully analyzed."
            analyzed = True
        elif successful_count > 0:
            msg = f"{successful_count} of {total} application link(s) successfully analyzed. Some application links could not be accessed."
            analyzed = True
        else:
            msg = "Application links could not be accessed. Requirement context will be used."
            analyzed = False

        return (analyzed, msg, page_contexts)

    async def extract_context(self, url: Optional[str]) -> Tuple[bool, str, Dict[str, Any]]:
        """Backward compatible single-link extraction method."""
        if not url or not url.strip():
            return (
                False,
                "No Application Link provided. Requirements analyzed using application specification and work item.",
                {}
            )
        payload = ApplicationLinkPayload(name="Application Page 1", url=url)
        analyzed, msg, contexts = await self.extract_multi_context([payload])
        single_metadata = contexts[0] if contexts else {}
        return (analyzed, msg, single_metadata)

web_extractor = WebContextExtractor()

