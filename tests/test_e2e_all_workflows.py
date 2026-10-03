"""Comprehensive E2E Playwright verification script for Knowra RAG Chatbot.

Executes and validates all 7 end-to-end workflows:
  Test 1: Persistence & Refresh
  Test 2: Multi-Turn Conversation Switching
  Test 3: Intelligent Title Generation
  Test 4: Real Stop Functionality (Level B/C/D)
  Test 5: Header Mode Switcher Cleanliness & Composer Switcher
  Test 6: Data Management Modal & Tab Return
  Test 7: Dark / Light Mode Switching & Persistence
"""

import asyncio
import json
import os
import subprocess
import sys
import time
from playwright.async_api import async_playwright

SERVER_PORT = 8000
BASE_URL = f"http://localhost:{SERVER_PORT}"
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


async def wait_for_server(timeout: int = 30):
    import urllib.request
    start = time.time()
    while time.time() - start < timeout:
        try:
            req = urllib.request.urlopen(f"{BASE_URL}/api/health", timeout=2)
            if req.status == 200:
                print(f"[OK] Server healthy at {BASE_URL}")
                return True
        except Exception:
            await asyncio.sleep(0.5)
    raise RuntimeError(f"Server did not start within {timeout}s")


async def run_all_tests():
    print("=" * 70)
    print("STARTING E2E VERIFICATION TEST SUITE (7 WORKFLOWS)")
    print("=" * 70)

    # 1. Start uvicorn server
    log_path = os.path.join(PROJECT_ROOT, "server_e2e.log")
    log_file = open(log_path, "w", encoding="utf-8")
    server_process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "src.api.main:app", "--port", str(SERVER_PORT), "--host", "127.0.0.1"],
        cwd=PROJECT_ROOT,
        stdout=log_file,
        stderr=log_file,
    )

    results = {}

    try:
        await wait_for_server()

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(viewport={"width": 1440, "height": 900})
            page = await context.new_page()

            # Helper for message bubbles count
            async def get_msg_count():
                return await page.locator("div.flex.justify-end, div.flex.justify-start:has-text('Multi-Source Assistant')").count()

            # -----------------------------------------------------------------
            # TEST 7: Dark / Light Mode Switching & Persistence (Test upfront)
            # -----------------------------------------------------------------
            print("\n>>> Running Test 7: Dark / Light Mode Switching & Persistence...")
            await page.goto(BASE_URL)
            await page.wait_for_selector("h1", timeout=10000)
            await asyncio.sleep(1)

            # Check initial dark mode
            is_dark_initial = await page.evaluate("() => document.documentElement.classList.contains('dark')")
            print(f"  - Initial dark mode active: {is_dark_initial}")

            # Toggle to Light Mode
            theme_btn = page.locator("main header button").filter(has=page.locator("svg.lucide-sun, svg.lucide-moon")).first
            await theme_btn.click()
            await asyncio.sleep(0.5)
            is_light = await page.evaluate("() => !document.documentElement.classList.contains('dark') && localStorage.getItem('rag_theme') === 'light'")
            print(f"  - Toggled to light mode & localStorage='light': {is_light}")

            # Toggle back to Dark Mode
            await theme_btn.click()
            await asyncio.sleep(0.5)
            is_dark_again = await page.evaluate("() => document.documentElement.classList.contains('dark') && localStorage.getItem('rag_theme') === 'dark'")
            print(f"  - Toggled back to dark mode & localStorage='dark': {is_dark_again}")

            # Reload and verify persistence
            await page.reload()
            await page.wait_for_selector("h1", timeout=10000)
            persisted_dark = await page.evaluate("() => document.documentElement.classList.contains('dark') && localStorage.getItem('rag_theme') === 'dark'")
            print(f"  - Dark mode persisted after page reload: {persisted_dark}")

            results["Test 7: Dark/Light Mode & Persistence"] = (
                is_dark_initial and is_light and is_dark_again and persisted_dark
            )

            # -----------------------------------------------------------------
            # TEST 5: Header Mode Switcher Removed & Composer Switcher
            # -----------------------------------------------------------------
            print("\n>>> Running Test 5: Header Mode Switcher Cleanliness & Composer Switcher...")
            main_header_text = await page.locator("main header").inner_text()
            has_duplicate_pill = "Evaluation Mode" in main_header_text or "Chat Mode" in main_header_text
            print(f"  - Duplicate pill in Main Header: {has_duplicate_pill} (Expected: False)")

            # Switch to Evaluation via composer button
            composer_eval_btn = page.locator("button:has-text('Evaluation Mode')").first
            await composer_eval_btn.click()
            await asyncio.sleep(1)
            eval_view_visible = await page.locator("text=Benchmark Evaluation Suite").is_visible()
            print(f"  - Evaluation view opened via composer: {eval_view_visible}")

            # Switch back to Chat
            back_btn = page.locator("button:has-text('Back to Chat')").first
            await back_btn.click()
            await asyncio.sleep(1)
            chat_view_visible = await page.locator("textarea[placeholder*='Ask']").is_visible()
            print(f"  - Back to Chat view: {chat_view_visible}")

            results["Test 5: Header Cleanliness & Composer Switcher"] = (
                not has_duplicate_pill and eval_view_visible and chat_view_visible
            )

            # -----------------------------------------------------------------
            # TEST 6: Data Management Modal & Tab Return
            # -----------------------------------------------------------------
            print("\n>>> Running Test 6: Data Management Modal & Tab Return...")
            data_tab = page.locator("aside button:has-text('Data Management')").first
            await data_tab.click()
            await asyncio.sleep(1)

            modal_visible = await page.locator("text=Document & Vectorstore Management").is_visible()
            print(f"  - Data management modal opened: {modal_visible}")

            # Close modal via 'Done' button
            close_btn = page.locator("button:has-text('Done')").first
            await close_btn.click()
            await asyncio.sleep(1)

            # Verify tab returned to Chat Configuration
            chat_config_tab = page.locator("aside button:has-text('Chat Configuration')").first
            chat_config_classes = await chat_config_tab.get_attribute("class") or ""
            is_chat_tab_active = "from-[#009bff]" in chat_config_classes
            print(f"  - Chat Configuration tab active after modal close: {is_chat_tab_active}")

            results["Test 6: Data Modal & Tab Return"] = modal_visible and is_chat_tab_active

            # -----------------------------------------------------------------
            # TEST 1: Persistence & Refresh
            # -----------------------------------------------------------------
            print("\n>>> Running Test 1: Persistence & Refresh...")
            # Click New Chat to start fresh
            new_chat_btn = page.locator("aside button:has-text('New Chat'), aside button[title='Start New Chat']").first
            await new_chat_btn.click()
            await asyncio.sleep(0.5)

            textarea = page.locator("textarea[placeholder*='Ask']")
            await textarea.fill("Explain in one short sentence what a vector database is.")
            send_btn = page.locator("button[title*='Send Prompt']").first
            await send_btn.click()

            # Wait for response completion (Wait for Stop button to vanish)
            print("  - Streaming query...")
            await asyncio.sleep(1)
            for _ in range(40):
                await asyncio.sleep(0.5)
                is_generating = await page.locator("button[title*='Stop Generation']").is_visible()
                if not is_generating:
                    break
            await asyncio.sleep(1.5)

            # Verify messages rendered
            msg_count = await get_msg_count()
            print(f"  - Message bubbles rendered: {msg_count} (Expected >= 2)")

            # Check conversations.json on disk
            conv_file = os.path.join(PROJECT_ROOT, "data", "conversations.json")
            with open(conv_file, "r", encoding="utf-8") as f:
                disk_convs = json.load(f)
            print(f"  - Conversations stored on disk: {len(disk_convs)}")

            # Reload page and verify messages persist
            await page.reload()
            await page.wait_for_selector("h1", timeout=10000)
            await asyncio.sleep(2)
            reloaded_msg_count = await get_msg_count()
            print(f"  - Message bubbles after reload: {reloaded_msg_count} (Expected >= 2)")

            results["Test 1: Persistence & Refresh"] = msg_count >= 2 and reloaded_msg_count >= 2

            # -----------------------------------------------------------------
            # TEST 3: Intelligent Title Generation
            # -----------------------------------------------------------------
            print("\n>>> Running Test 3: Intelligent Title Generation...")
            # Start new chat for topic test
            await new_chat_btn.click()
            await asyncio.sleep(0.5)

            await textarea.fill("Can you explain how attention mechanisms work in transformer models?")
            await send_btn.click()

            print("  - Streaming query for title generation...")
            await asyncio.sleep(1)
            for _ in range(40):
                await asyncio.sleep(0.5)
                is_generating = await page.locator("button[title*='Stop Generation']").is_visible()
                if not is_generating:
                    break
            # Give background title generation 3 seconds
            await asyncio.sleep(3)

            # Check title in history panel
            recent_titles = await page.locator("aside p.text-xs.font-medium.truncate").all_inner_texts()
            print(f"  - Recent conversation titles in panel: {recent_titles}")
            first_title = recent_titles[0] if recent_titles else ""
            is_good_title = (
                bool(first_title)
                and first_title != "New Chat"
                and first_title != "Can you explain how attention mechanisms work in transformer models?"
            )
            print(f"  - Generated concise title: '{first_title}' (Is intelligent: {is_good_title})")

            results["Test 3: Intelligent Title Generation"] = is_good_title

            # -----------------------------------------------------------------
            # TEST 2: Multi-Turn Conversation Switching
            # -----------------------------------------------------------------
            print("\n>>> Running Test 2: Multi-Turn Conversation Switching...")
            # History items in the right sidebar
            history_items = page.locator("aside .group.relative.flex.items-center.justify-between")
            item_count = await history_items.count()
            print(f"  - Total history items: {item_count}")
            if item_count >= 2:
                print("  - Switching to previous conversation...")
                await history_items.nth(1).click()
                await asyncio.sleep(2)
                conv_a_msgs = await get_msg_count()
                print(f"  - Loaded messages in Conv A: {conv_a_msgs}")

                print("  - Switching back to active conversation...")
                await history_items.nth(0).click()
                await asyncio.sleep(2)
                conv_b_msgs = await get_msg_count()
                print(f"  - Loaded messages in Conv B: {conv_b_msgs}")

                results["Test 2: Conversation Switching"] = conv_a_msgs >= 2 and conv_b_msgs >= 2
            else:
                results["Test 2: Conversation Switching"] = False

            # -----------------------------------------------------------------
            # TEST 4: Real Stop Functionality (Level B/C/D)
            # -----------------------------------------------------------------
            print("\n>>> Running Test 4: Real Stop Functionality...")
            await new_chat_btn.click()
            await asyncio.sleep(0.5)

            # Long query to ensure active streaming
            await textarea.fill("Write an extensive, comprehensive guide on the mathematical history of cryptography with 20 paragraphs.")
            await send_btn.click()

            # Wait for Stop button to appear
            stop_btn = page.locator("button[title*='Stop Generation']").first
            await stop_btn.wait_for(state="visible", timeout=10000)
            print("  - Stop button active during streaming. Clicking Stop...")
            await asyncio.sleep(0.8)  # Let a few tokens stream
            await stop_btn.click()

            # Wait for generation to stop
            await asyncio.sleep(1.5)

            # Check stopped badge
            stopped_badge_visible = await page.locator("text=Stopped").is_visible()
            print(f"  - 'Stopped' badge rendered on assistant bubble: {stopped_badge_visible}")

            # Send immediate follow-up query
            await textarea.fill("What is 2 + 2?")
            await send_btn.click()
            print("  - Streaming follow-up query after stop...")
            await asyncio.sleep(1)
            for _ in range(40):
                await asyncio.sleep(0.5)
                is_generating = await page.locator("button[title*='Stop Generation']").is_visible()
                if not is_generating:
                    break
            await asyncio.sleep(1.5)
            final_msg_count = await get_msg_count()
            print(f"  - Messages after follow-up: {final_msg_count} (Expected >= 4)")

            results["Test 4: Real Stop Functionality"] = stopped_badge_visible and final_msg_count >= 4

            await browser.close()

    finally:
        server_process.terminate()
        try:
            server_process.wait(timeout=5)
        except Exception:
            server_process.kill()
        try:
            log_file.close()
        except Exception:
            pass

    print("\n" + "=" * 70)
    print("E2E VERIFICATION RESULTS SUMMARY:")
    print("=" * 70)
    all_passed = True
    for name, passed in results.items():
        status = "[PASS]" if passed else "[FAIL]"
        if not passed:
            all_passed = False
        print(f"  {status} : {name}")
    print("=" * 70)
    print(f"OVERALL STATUS: {'ALL 7 WORKFLOWS PASSED' if all_passed else 'SOME WORKFLOWS FAILED'}")
    print("=" * 70)
    return all_passed


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)
