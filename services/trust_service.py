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
        
    def analyze(self, url):
        """Analyzes a website for trust factors."""
        if not url.startswith(('http://', 'https://')):
            url = 'http://' + url
            
        result = {
            "trust_score": 0,
            "explanation": [],
            "details": {}
        }
        
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            soup = BeautifulSoup(response.content, 'lxml')
            
            score = 50 # Base score
            
            # 1. Title
            title = soup.title.string if soup.title else None
            result["details"]["title"] = title
            if title:
                score += 5
                result["explanation"].append("+ Has a title")
            else:
                score -= 10
                result["explanation"].append("- Missing title")
                
            # 2. HTTPS (Checking URL)
            if url.startswith("https"):
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
                if href.startswith('http') and url not in href:
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
                        
            if login_form_found and not url.startswith("https"):
                score -= 30
                result["explanation"].append("- Login form on insecure page (HIGH RISK)")
                
            # 5. Suspicious Keywords
            text_content = soup.get_text().lower()
            found_keywords = [kw for kw in self.suspicious_keywords if kw in text_content]
            if found_keywords:
                score -= (len(found_keywords) * 2)
                result["explanation"].append(f"- Suspicious keywords found: {', '.join(found_keywords)}")
                
            # Cap the score between 0 and 100
            result["trust_score"] = max(0, min(100, score))
            
        except Exception as e:
            result["trust_score"] = 0
            result["explanation"].append(f"- Error analyzing website: {str(e)}")
            
        return result
