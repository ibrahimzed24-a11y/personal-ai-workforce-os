import os
import time
from playwright.sync_api import sync_playwright

ARTIFACT_DIR = "/Users/ibrahimzid/.gemini/antigravity/brain/dfd73b45-dcfa-4f1a-957f-4463c1b3e27c"
URL = "https://personal-ai-workforce-os-pi.vercel.app"

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        
        # 1. Desktop Viewport
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        page.goto(URL, wait_until="networkidle")
        time.sleep(2)
        
        # Click Guest / Sovereign access
        guest_btn = page.query_selector("#guest-login-btn")
        if guest_btn:
            guest_btn.click()
        else:
            page.fill("#auth-email", "operator@sovereign.local")
            page.fill("#auth-password", "Sovereign123!")
            page.click("#auth-submit")
            
        page.wait_for_selector("#active-project-name", timeout=12000)
        time.sleep(2)
        
        # Select first project
        projects = page.query_selector_all(".project-item")
        if projects:
            projects[0].click()
            time.sleep(1.5)
            
        page.screenshot(path=f"{ARTIFACT_DIR}/production_chat_and_harness.png", full_page=True)
        print("Captured production_chat_and_harness.png")
        
        # Open 32 Agents Tab
        page.click("button[data-tab='agents']")
        time.sleep(2)
        page.screenshot(path=f"{ARTIFACT_DIR}/production_32_agents_and_skills.png", full_page=True)
        print("Captured production_32_agents_and_skills.png")
        
        # Click on software-engineer agent card to inspect blueprint modal
        eng_card = page.query_selector(".agent-card:has-text('Software Engineer')")
        if eng_card:
            eng_card.click()
            time.sleep(1.5)
            page.screenshot(path=f"{ARTIFACT_DIR}/production_agent_blueprint_modal.png")
            print("Captured production_agent_blueprint_modal.png")
            page.click("#close-agent-modal-btn")
            time.sleep(0.5)

        # Open Admin Reports Tab
        page.click("button[data-tab='reports']")
        time.sleep(2)
        page.screenshot(path=f"{ARTIFACT_DIR}/production_admin_reports_dag.png", full_page=True)
        print("Captured production_admin_reports_dag.png")

        # 2. Mobile Viewport (iPhone 14)
        mobile_page = browser.new_page(viewport={"width": 390, "height": 844})
        mobile_page.goto(URL, wait_until="networkidle")
        time.sleep(1)
        m_guest = mobile_page.query_selector("#guest-login-btn")
        if m_guest:
            m_guest.click()
        mobile_page.wait_for_selector("#active-project-name", timeout=12000)
        time.sleep(2)
        
        # Click agents tab on mobile
        mobile_page.click("button[data-tab='agents']")
        time.sleep(2)
        mobile_page.screenshot(path=f"{ARTIFACT_DIR}/production_mobile_agents.png")
        print("Captured production_mobile_agents.png")

        browser.close()
        print("All QA Screenshots successfully captured!")

if __name__ == "__main__":
    run()
