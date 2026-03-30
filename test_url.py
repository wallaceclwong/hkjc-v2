import asyncio
from playwright.async_api import async_playwright

async def test_urls():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        # Test the new URL format
        url = "https://bet.hkjc.com/en/racing/home/2026/04/01/ST/1"
        print(f"Testing: {url}")
        
        try:
            await page.goto(url, timeout=30000)
            title = await page.title()
            print(f"Page title: {title}")
            
            # Check if we can find any race-related content
            content = await page.inner_text("body")
            if "race" in content.lower() or "horse" in content.lower():
                print("✅ Found race-related content")
                # Show first 500 chars
                print(content[:500])
            else:
                print("❌ No race content found")
                
        except Exception as e:
            print(f"❌ Error: {e}")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_urls())
