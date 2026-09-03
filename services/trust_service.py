import requests
from bs4 import BeautifulSoup
import re

class TrustService:
    """Module 2: Website Trust Analyzer"""
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.suspicious_keywords = ['login', 'verify', 'update', 'account', 'banking', 'secure', 'password']

        # Phrases that show up on registrar "domain for sale" pages, ad
        # parking pages, and default web-server placeholder pages. If a
        # domain resolves and responds with 200 OK but is actually just
        # one of these, it isn't a real website - it should never be
        # scored as "Safe".
        self.parked_page_phrases = [
            "domain is for sale", "buy this domain", "this domain may be for sale",
            "domain parking", "related searches", "future home of",
            "this web page is parked", "domain has expired", "domain has been registered",
            "godaddy.com", "sedo.com", "namecheap parking", "hugedomains",
            "welcome to nginx", "apache2 ubuntu default page", "iis windows server",
            "if you are the owner of this website",
        ]
        
    def analyze(self, url):
        """Analyzes a website for trust factors."""
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
            
        result = {
            "trust_score": 0,
            "explanation": [],
            "details": {}
        }
        
        try:
            response = requests.get(url, headers=self.headers, timeout=10, allow_redirects=True)
            final_url = response.url  # after any redirects - this is what actually loaded
            soup = BeautifulSoup(response.content, 'lxml')
            
            score = 50 # Base score

            # 0. Not-found / dead-page status codes. A 404/410/5xx response
            # means there's no real page here even though the server
            # answered - this should never be able to score as "Safe".
            status = response.status_code
            result["details"]["http_status"] = status
            if status in (404, 410) or status >= 500:
                result["trust_score"] = 0
                result["details"]["not_found"] = True
                result["explanation"].append(f"- Page returned HTTP {status} (page does not exist)")
                return result

            # Parked / placeholder domain detection - registrar "for sale"
            # pages, ad-parking pages, and default web-server pages all
            # respond with 200 OK but aren't a real website.
            page_text = soup.get_text(" ", strip=True).lower()
            visible_text_length = len(page_text)
            matched_parked_phrases = [p for p in self.parked_page_phrases if p in page_text]

            if matched_parked_phrases or visible_text_length < 40:
                result["trust_score"] = 5
                result["details"]["is_parked"] = True
                if matched_parked_phrases:
                    result["explanation"].append(
                        "- This looks like a parked/placeholder domain, not a real website "
                        f"(matched: {matched_parked_phrases[0]})"
                    )
                else:
                    result["explanation"].append(
                        "- Page has almost no content - likely not a real, active website"
                    )
                return result

            # 1. Title
            title = soup.title.string if soup.title else None
            result["details"]["title"] = title
            if title:
                score += 5
                result["explanation"].append("+ Has a title")
            else:
                score -= 10
                result["explanation"].append("- Missing title")
                
            # 2. HTTPS (check the URL that actually loaded, after redirects -
            # many sites are served over http:// initially but redirect to
            # https://, so checking the original request URL here would
            # incorrectly flag secure sites as insecure)
            is_https = final_url.startswith("https")
            if is_https:
                score += 15
                result["explanation"].append("+ HTTPS enabled")
            else:
                score -= 20
                result["explanation"].append("- No HTTPS (Insecure)")
                
            # 3. Links Analysis
            links = soup.find_all('a', href=True)
            external_links = 0
            internal_links = 0
            
            for link in links:
                href = link['href']
                if href.startswith('http') and final_url not in href:
                    external_links += 1
                else:
                    internal_links += 1
                    
            if external_links > 50:
                score -= 10
                result["explanation"].append("- Too many external links")
                
            # 4. Forms (Login)
            forms = soup.find_all('form')
            login_form_found = False
            for form in forms:
                inputs = form.find_all('input')
                for inp in inputs:
                    if inp.get('type') == 'password':
                        login_form_found = True
                        break
                        
            if login_form_found and not is_https:
                score -= 30
                result["explanation"].append("- Login form on insecure page (HIGH RISK)")
                
            # 5. Suspicious Keywords
            # Note: words like "login"/"account"/"secure" appear on most
            # legitimate sites too (banks, email providers, SaaS dashboards),
            # so this alone is a weak signal. We only apply a small penalty,
            # and only when several such words appear on a page that is
            # *also* not HTTPS - the combination is what's actually telling.
            text_content = soup.get_text().lower()
            found_keywords = [kw for kw in self.suspicious_keywords if kw in text_content]
            if len(found_keywords) >= 3 and not is_https:
                score -= min(len(found_keywords), 10)
                result["explanation"].append(
                    f"- Suspicious keywords on a non-HTTPS page: {', '.join(found_keywords)}"
                )
                
            # Cap the score between 0 and 100
            result["trust_score"] = max(0, min(100, score))
            result["details"]["final_url"] = final_url
            
        except Exception as e:
            result["trust_score"] = 0
            result["explanation"].append(f"- Error analyzing website: {str(e)}")
            
        return result