import requests
import socket
import ssl
from urllib.parse import urlparse
import time

class ConnectivityService:
    """Module 1: Website Connectivity Check"""
    
    def check_connectivity(self, url):
        """Runs connectivity checks on the given URL."""
        if not url.startswith(('http://', 'https://')):
            url = 'http://' + url
            
        parsed_url = urlparse(url)
        domain = parsed_url.netloc
        
        result = {
            "reachable": False,
            "http_status": None,
            "https_enabled": False,
            "ssl_valid": False,
            "redirect_count": 0,
            "response_time": 0,
            "error_message": None
        }
        
        # DNS Resolution
        try:
            socket.gethostbyname(domain)
        except socket.gaierror:
            result["error_message"] = "DNS Resolution Failed. Invalid domain."
            return result
            
        # HTTP Request
        start_time = time.time()
        try:
            response = requests.get(url, timeout=10, allow_redirects=True)
            result["response_time"] = round((time.time() - start_time) * 1000, 2)
            result["reachable"] = True
            result["http_status"] = response.status_code
            result["redirect_count"] = len(response.history)
            
            final_url = response.url
            if final_url.startswith("https"):
                result["https_enabled"] = True
                
        except requests.exceptions.Timeout:
            result["error_message"] = "Connection Timed Out."
            return result
        except requests.exceptions.ConnectionError:
            result["error_message"] = "Connection Failed."
            return result
        except Exception as e:
            result["error_message"] = str(e)
            return result
            
        # SSL Verification
        if result["https_enabled"]:
            try:
                ctx = ssl.create_default_context()
                with ctx.wrap_socket(socket.socket(), server_hostname=domain) as s:
                    s.connect((domain, 443))
                result["ssl_valid"] = True
            except Exception:
                result["ssl_valid"] = False
                
        return result
