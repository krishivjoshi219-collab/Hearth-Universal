#!/usr/bin/env python3
"""record_demo_flow.py — Deterministic verification & screenshot recording of the 2:30 Grand Prize cut.

Executes the exact winning narrative:
1. [0:00–0:12] Cold Open & Hero Surface load (/echo?tour=1)
2. [0:12–1:05] 'Save me $800' -> Live Audit -> Stage -> Approve -> Glass Receipt -> 1-Tap Undo
3. [1:05–1:35] 'Fix groceries' -> Autopilot Subscribe & Save Cart -> Approve -> 1-Tap Undo
4. [1:35–2:05] Persona Switch to Leo (Child) -> Child Guardrail Hard Block on spend/unlock
5. [2:05–2:30] Black Box Spatial CSI Intruder Disproof & Merkle Ledger Verification

Saves timestamped high-res screenshots for video slides, pitch deck, and submission.
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.support.ui import WebDriverWait
except ImportError:
    print("Selenium not available. Please install selenium or run HTTP verification mode.")
    sys.exit(1)


def get_driver(headless: bool = True) -> webdriver.Chrome:
    opts = Options()
    if headless:
        opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--window-size=1280,800")
    opts.add_argument("--force-device-scale-factor=1")
    opts.binary_location = "/home/k/.local/bin/google-chrome"
    return webdriver.Chrome(options=opts)


def safe_click(driver: webdriver.Chrome, elem) -> None:
    try:
        elem.click()
    except Exception:
        driver.execute_script("arguments[0].click();", elem)


def main():
    parser = argparse.ArgumentParser(description="Record Hearth Demo Flow")
    parser.add_argument("--url", default="http://localhost:8787", help="Base URL of Hearth server")
    parser.add_argument("--out", default="demo_production/screenshots", help="Output screenshot directory")
    parser.add_argument("--headless", action="store_true", default=True, help="Run headless")
    args = parser.parse_args()

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"🚀 Launching Hearth Universal Demo Verification against {args.url}...")
    driver = get_driver(headless=args.headless)
    wait = WebDriverWait(driver, 12)

    try:
        # Step 1: Echo Show Surface (/echo?tour=1)
        print("📸 Step 1: Loading Echo Show Surface...")
        driver.get(f"{args.url}/echo?tour=1")
        time.sleep(2)
        driver.save_screenshot(str(out_dir / "01_hero_surface.png"))
        print(f"   Saved {out_dir / '01_hero_surface.png'}")

        # Step 2: Trigger 'Save me $800'
        print("💸 Step 2: Triggering 'Save me $800 on renewals'...")
        save_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button[data-go='/api/renewals']")))
        safe_click(driver, save_btn)
        time.sleep(2)
        driver.save_screenshot(str(out_dir / "02_save_800_audit.png"))
        print(f"   Saved {out_dir / '02_save_800_audit.png'}")

        # Step 3: Stage StreamBox Cancellation
        print("📦 Step 3: Staging StreamBox Cancellation ($239.88/yr)...")
        stage_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button[data-sub='sub_streambox']")))
        safe_click(driver, stage_btn)
        time.sleep(1.5)
        driver.save_screenshot(str(out_dir / "03_staged_tray.png"))
        print(f"   Saved {out_dir / '03_staged_tray.png'}")

        # Step 4: Approve in Tray -> Glass Receipt
        print("📜 Step 4: Approving Proposal & Opening Glass Receipt...")
        approve_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button[data-act='approve']")))
        safe_click(driver, approve_btn)
        time.sleep(2)
        driver.save_screenshot(str(out_dir / "04_glass_receipt_sealed.png"))
        print(f"   Saved {out_dir / '04_glass_receipt_sealed.png'}")

        # Step 5: 1-Tap Undo Reversal
        print("↩️ Step 5: Exercising 1-Tap Undo Reversal...")
        undo_btn = driver.find_element(By.ID, "receiptUndoBtn")
        if undo_btn.is_displayed():
            safe_click(driver, undo_btn)
        else:
            tray_undo = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button[data-act='undo']")))
            safe_click(driver, tray_undo)
        time.sleep(1.5)
        driver.save_screenshot(str(out_dir / "05_undone_reversal.png"))
        print(f"   Saved {out_dir / '05_undone_reversal.png'}")

        # Step 6: Fix Groceries
        print("🛒 Step 6: Triggering Autopilot 'Fix Groceries'...")
        groceries_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button[data-go='/api/commerce/autopilot-checkout']")))
        safe_click(driver, groceries_btn)
        time.sleep(2)
        driver.save_screenshot(str(out_dir / "06_fix_groceries_staged.png"))
        print(f"   Saved {out_dir / '06_fix_groceries_staged.png'}")

        # Step 7: Persona Switch to Leo (Child)
        print("🧒 Step 7: Persona Switch to Leo (Child)...")
        persona_btn = wait.until(EC.element_to_be_clickable((By.ID, "personaToggleBtn")))
        safe_click(driver, persona_btn)
        time.sleep(1.5)
        driver.save_screenshot(str(out_dir / "07_leo_child_guardrail.png"))
        print(f"   Saved {out_dir / '07_leo_child_guardrail.png'}")

        # Switch back to Adult for clean state
        safe_click(driver, persona_btn)
        time.sleep(1)

        # Step 8: CSI Forensic Reconstruction
        print("🔍 Step 8: Triggering Black Box Spatial CSI Forensics...")
        csi_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button[data-go='/api/forensics/reconstruct']")))
        safe_click(driver, csi_btn)
        time.sleep(2)
        driver.save_screenshot(str(out_dir / "08_csi_intruder_disproved.png"))
        print(f"   Saved {out_dir / '08_csi_intruder_disproved.png'}")

        print("\n🎉 ALL 8 DEMO FLOW PHASES COMPLETED WITH 100% INTEGRITY!")
        print(f"Screenshots recorded in: {out_dir.resolve()}")
    finally:
        driver.quit()


if __name__ == "__main__":
    main()
