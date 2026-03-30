import asyncio
from playwright.async_api import async_playwright

async def test_old_url():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        # Test the old URL format that worked before
        url = "https://racing.hkjc.com/en-us/local/information/racecard?RaceDate=2026/03/29&Racecourse=ST&RaceNo=11"
        print(f"Testing old URL: {url}")
        
        try:
            await page.goto(url, timeout=30000)
            title = await page.title()
            print(f"Page title: {title}")
            
            # Check if we can find any race-related content
            content = await page.inner_text("body")
            if "race" in content.lower() or "horse" in content.lower():
                print("[OK] Found race-related content")
                # Show first 500 chars
                print(content[:500])
            else:
                print("[FAIL] No race content found")
                
        except Exception as e:
            print(f"[ERROR] {e}")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_old_url())
