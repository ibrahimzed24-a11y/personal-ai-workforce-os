import asyncio
from playwright.async_api import async_playwright

async def verify_ui():
    print("Testing Web UI with Headless Chromium...")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        # Navigate to OS Web Control Panel
        await page.goto("http://127.0.0.1:8765", wait_until="networkidle")
        title = await page.title()
        print(f"✓ Page Title: {title}")
        assert "AI Workforce OS" in title
        
        # Verify navigation tabs present
        tabs = await page.query_selector_all(".nav-item")
        print(f"✓ Found {len(tabs)} navigation tabs in sidebar.")
        assert len(tabs) >= 5
        
        # Click Security Tab
        sec_tab = await page.query_selector('button[data-tab="security"]')
        assert sec_tab is not None
        await sec_tab.click()
        await page.wait_for_timeout(1000)
        
        # Verify account card rendered
        account_cards = await page.query_selector_all(".account-card")
        print(f"✓ Security tab rendered {len(account_cards)} account card(s).")
        assert len(account_cards) >= 1
        
        # Click Agents Tab
        agents_tab = await page.query_selector('button[data-tab="agents"]')
        await agents_tab.click()
        await page.wait_for_timeout(1000)
        agent_cards = await page.query_selector_all(".agent-card")
        print(f"✓ Agents tab rendered {len(agent_cards)} agent card(s).")
        assert len(agent_cards) >= 8
        
        # Click Tasks Tab
        tasks_tab = await page.query_selector('button[data-tab="tasks"]')
        await tasks_tab.click()
        await page.wait_for_timeout(1000)
        task_cards = await page.query_selector_all(".task-card")
        print(f"✓ Tasks tab rendered {len(task_cards)} task card(s).")
        assert len(task_cards) >= 1
        
        await browser.close()
        print("🎉 Browser UI verification passed with flying colors!")

if __name__ == "__main__":
    asyncio.run(verify_ui())
