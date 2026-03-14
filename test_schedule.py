import urllib.request
import urllib.error
import ssl
from bs4 import BeautifulSoup

def fetch_march_schedule():
    url = "https://racing.hkjc.com/racing/information/English/Racing/Fixture.aspx"
    
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9',
    }

    print("Fetching HKJC Fixture Schedule...")
    req = urllib.request.Request(url, headers=headers)
    
    try:
        response = urllib.request.urlopen(req, context=ctx, timeout=10)
        html_content = response.read()
        
        soup = BeautifulSoup(html_content, 'lxml')
        
        # Let's find columns explicitly looking for "Mar" / "03" since dates format in HTML might be <td>01/03/2026</td>
        print("--- Finding dates containing 'Mar' or '03/2026' ---")
        march_fixtures = []
        for td in soup.find_all('td'):
            text = td.get_text(strip=True)
            if "03/2026" in text or "Mar " in text:
                 # If this cell is a Date, grab its parent row
                 row = td.parent
                 # Try to parse the standard table structure: Date, Day, Day/Night, Venue, Event
                 cols = row.find_all('td')
                 if len(cols) >= 3:
                     date = cols[0].get_text(strip=True)
                     day_night = cols[1].get_text(strip=True) if len(cols) > 1 else ""
                     venue = cols[2].get_text(strip=True) if len(cols) > 2 else ""
                     event = cols[3].get_text(strip=True) if len(cols) > 3 else ""
                     march_fixtures.append(f"{date} - {venue} ({day_night}) {event}")

        if march_fixtures:
            for f in march_fixtures:
                print(f)
        else:
            print("No March 2026 fixtures found via direct cell text match.")
            print("\nWait, checking if they use 2025/2026 season. So March would be 2026. Let's look for just '03/' in the first column:")
            
            for tr in soup.find_all('tr'):
                cols = tr.find_all('td')
                if cols:
                    date_col = cols[0].get_text(strip=True)
                    if "/03/" in date_col:
                        venue = cols[2].get_text(strip=True) if len(cols) > 2 else ""
                        march_fixtures.append(f"{date_col} - {venue}")
                        
            if march_fixtures:
                 for f in march_fixtures:
                      print(f)
            else:
                 print("\nStill no dates found. Printing the first 50 lines of body text to see what we loaded:")
                 body_text = soup.body.get_text(separator='\n', strip=True)
                 print("\n".join(body_text.split('\n')[:50]))

    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    fetch_march_schedule()
