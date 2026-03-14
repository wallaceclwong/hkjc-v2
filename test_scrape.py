import urllib.request
import urllib.error
import ssl
import json
from datetime import datetime

def test_hkjc_access():
    print(f"Testing HKJC Access at {datetime.now()}")
    print("-" * 50)
    
    # We'll test a few different endpoints to see if they behave differently.
    endpoints = {
        "Main Homepage": "https://racing.hkjc.com/racing/english/index.aspx",
        "Results Page": "https://racing.hkjc.com/racing/information/English/Racing/LocalResults.aspx",
        # Try a known JSON endpoint (if we can guess one, or just test HTML first)
        # Often odds are loaded via JSON/XML in the background. Let's start with basic HTML routes.
    }
    
    # Create an unverified context in case of SSL issues, though HKJC should have valid certs.
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    # Use a standard browser User-Agent to avoid immediate bot rejection
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Language': 'en-US,en;q=0.9',
    }

    for name, url in endpoints.items():
        print(f"\nTesting {name} ({url})...")
        req = urllib.request.Request(url, headers=headers)
        
        try:
            response = urllib.request.urlopen(req, context=ctx, timeout=10)
            status_code = response.getcode()
            html_content = response.read().decode('utf-8')
            
            print(f"Status Code: {status_code}")
            print(f"Response Size: {len(html_content)} bytes")
            
            # Simple check to see if we got an actual HKJC page or a block page (like Cloudflare challenge)
            if "Hong Kong Jockey Club" in html_content or "HKJC" in html_content:
                 print("Result: SUCCESS (Found typical HKJC text)")
            elif "Cloudflare" in html_content or "Please wait" in html_content:
                 print("Result: BLOCKED (Likely Cloudflare or similar challenge page)")
            else:
                 print("Result: UNKNOWN (Page loaded, but didn't find expected text. Might be an error page or a block.)")
                 print(f"Snippet: {html_content[:200]}")
                 
        except urllib.error.HTTPError as e:
            print(f"HTTP Error: {e.code} - {e.reason}")
        except urllib.error.URLError as e:
            print(f"URL Error: {e.reason}")
        except Exception as e:
            print(f"Unexpected Error: {e}")

if __name__ == '__main__':
    test_hkjc_access()
