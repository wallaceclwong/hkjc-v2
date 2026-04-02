import asyncio
from playwright.async_api import async_playwright

async def debug_dividends():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        url = "https://racing.hkjc.com/en-us/local/information/localresults?racedate=2026/03/29&Racecourse=ST&RaceNo=1"
        print(f"Loading: {url}")
        await page.goto(url)
        await page.wait_for_timeout(2000)
        
        # Check for dividend tables
        dividend_sections = await page.query_selector_all("div[class*='dividend']")
        print(f"\nFound {len(dividend_sections)} dividend sections")
        
        for i, section in enumerate(dividend_sections):
            text = await section.inner_text()
            print(f"\nSection {i+1}:")
            print(text[:200])
        
        # Also check for any table with dividend data
        tables = await page.query_selector_all("table")
        print(f"\nFound {len(tables)} tables")
        
        for i, table in enumerate(tables[:3]):  # Check first 3 tables
            text = await table.inner_text()
            if "WIN" in text or "PLACE" in text or "QUINELLA" in text:
                print(f"\nTable {i+1} has dividend data:")
                print(text[:300])
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(debug_dividends())
