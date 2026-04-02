import asyncio
from playwright.async_api import async_playwright

async def fix_dividend_scraping():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        url = "https://racing.hkjc.com/en-us/local/information/localresults?racedate=2026/03/29&Racecourse=ST&RaceNo=1"
        await page.goto(url)
        await page.wait_for_timeout(2000)
        
        # Get all text content and parse manually
        content = await page.inner_text("body")
        
        # Find the dividend section
        lines = content.split('\n')
        dividends = {"WIN": [], "PLACE": [], "QUINELLA": [], "QUINELLA PLACE": []}
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # Look for dividend headers
            if line == "Dividend":
                # Next line should be the table header
                if i + 1 < len(lines) and "Pool" in lines[i + 1]:
                    # Skip header line
                    i += 2
                    # Now parse the dividend rows
                    while i < len(lines):
                        row = lines[i].strip()
                        if not row or row == "Dividend Note:":
                            break
                        
                        parts = row.split()
                        if len(parts) >= 3:
                            # Check if first part is a pool type
                            if parts[0] in ["WIN", "PLACE", "QUINELLA", "QUINELLA PLACE"]:
                                pool = parts[0]
                                if pool == "WIN":
                                    if len(parts) >= 3:
                                        comb = parts[1]
                                        div = parts[2]
                                        dividends["WIN"].append({"combination": comb, "dividend": div})
                                elif pool == "PLACE":
                                    # PLACE has multiple combinations
                                    j = 1
                                    while j < len(parts) - 1:
                                        comb = parts[j]
                                        div = parts[j + 1]
                                        dividends["PLACE"].append({"combination": comb, "dividend": div})
                                        j += 2
                                elif pool == "QUINELLA":
                                    if len(parts) >= 3:
                                        comb = parts[1]
                                        div = parts[2]
                                        dividends["QUINELLA"].append({"combination": comb, "dividend": div})
                                elif pool == "QUINELLA PLACE":
                                    # QUINELLA PLACE has multiple combinations
                                    j = 1
                                    while j < len(parts) - 1:
                                        comb = parts[j]
                                        div = parts[j + 1]
                                        dividends["QUINELLA PLACE"].append({"combination": comb, "dividend": div})
                                        j += 2
                        i += 1
                else:
                    i += 1
            else:
                i += 1
        
        print("Fixed dividend parsing:")
        for pool, items in dividends.items():
            if items:
                print(f"\n{pool}:")
                for item in items:
                    print(f"  {item.get('combination')}: ${item.get('dividend')}")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(fix_dividend_scraping())
