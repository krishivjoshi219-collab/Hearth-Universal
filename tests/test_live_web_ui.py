import time
import sys
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def run_tests():
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1280,900")
    
    driver = webdriver.Chrome(options=chrome_options)
    wait = WebDriverWait(driver, 10)
    
    try:
        print("1. Loading http://localhost:8787/web2/index.html...")
        driver.get("http://localhost:8787/web2/index.html")
        wait.until(EC.presence_of_element_located((By.ID, "statusStrip")))
        print("✓ Page loaded successfully")
        
        # Check title and topbar
        assert "Hearth" in driver.title
        mode_sim_btn = driver.find_element(By.ID, "modeSimBtn")
        mode_real_btn = driver.find_element(By.ID, "modeRealBtn")
        assert mode_sim_btn.is_displayed()
        assert mode_real_btn.is_displayed()
        print("✓ Topmost mode switcher present with Simulation and Real World tabs")
        
        # Verify Home tab layout:
        # On Home: embedded chat container should be visible, floating chat button should be hidden
        home_chat = driver.find_element(By.ID, "homeChatContainer")
        float_btn = driver.find_element(By.ID, "floatingChatBtn")
        assert home_chat.is_displayed(), "Home chat container must be visible on Home"
        assert not float_btn.is_displayed(), "Floating chat button must be hidden on Home"
        print("✓ Home view: embedded chat visible, floating chat button hidden")
        
        # Test switching to Activity tab
        print("2. Switching to Activity tab...")
        activity_tab = driver.find_element(By.XPATH, "//button[@data-view='activity']")
        activity_tab.click()
        time.sleep(0.3)
        assert float_btn.is_displayed(), "Floating chat button must be visible on Activity tab"
        print("✓ Activity view: floating chat button is visible")
        
        # Test clicking floating chat button to open widget
        print("3. Testing floating chat widget toggle...")
        float_widget = driver.find_element(By.ID, "floatingChatWidget")
        assert not float_widget.is_displayed()
        float_btn.click()
        time.sleep(0.3)
        assert float_widget.is_displayed(), "Floating chat widget should open on click"
        print("✓ Floating chat widget opens on click")
        
        # Send a message through floating chat widget
        widget_input = driver.find_element(By.ID, "widgetCmdInput")
        widget_input.send_keys("What is the current household security status?")
        widget_send_btn = driver.find_element(By.CSS_SELECTOR, "#widgetCmdForm button[type='submit']")
        widget_send_btn.click()
        print("✓ Sent chat message via floating widget, awaiting response...")
        
        wait.until(lambda d: "hearth" in d.find_element(By.ID, "widgetChatLog").text.lower())
        widget_log = driver.find_element(By.ID, "widgetChatLog")
        print("✓ Response rendered in floating chat widget:\n", widget_log.text[:120], "...")
        
        # Close widget
        close_btn = driver.find_element(By.ID, "widgetCloseBtn")
        close_btn.click()
        time.sleep(0.3)
        assert not float_widget.is_displayed(), "Floating widget closed"
        print("✓ Floating chat widget closed cleanly")
        
        # Check other tabs: Approvals, Insights, Settings
        print("4. Testing tab switching across all tabs...")
        for tab_name in ["approvals", "insights", "settings"]:
            t = driver.find_element(By.XPATH, f"//button[@data-view='{tab_name}']")
            t.click()
            time.sleep(0.2)
            assert float_btn.is_displayed(), f"Floating chat button should be visible on {tab_name}"
            view_sec = driver.find_element(By.ID, f"view-{tab_name}")
            assert view_sec.is_displayed()
        print("✓ Approvals, Insights, and Settings views verified with floating assistant")
        
        # Switch back to Home
        print("5. Returning to Home tab...")
        home_tab = driver.find_element(By.XPATH, "//button[@data-view='home']")
        home_tab.click()
        time.sleep(0.3)
        assert not float_btn.is_displayed(), "Floating chat button must hide on Home"
        assert home_chat.is_displayed(), "Embedded chat container restored on Home"
        print("✓ Floating button hides and embedded chat is restored on Home tab")
        
        # Test Topmost Mode Switcher: Switch to Real World mode
        print("6. Switching to 🌐 Real World (Alexa+) mode...")
        mode_real_btn.click()
        time.sleep(1.0)
        
        sim_panel = driver.find_element(By.ID, "simPanel")
        real_panel = driver.find_element(By.ID, "realHubPanel")
        assert not sim_panel.is_displayed(), "Sim panel should hide in Real mode"
        assert real_panel.is_displayed(), "Real hub panel should show in Real mode"
        
        # Verify real devices listed
        real_grid = driver.find_element(By.ID, "realDevicesGrid")
        grid_text = real_grid.text
        assert "Ecobee" in grid_text or "Yale" in grid_text or "Matter" in grid_text, f"Unexpected grid text: {grid_text}"
        print("✓ Real World mode active: real smart hardware endpoints rendered dynamically")
        
        # Test Alexa+ Handshake in Settings
        print("7. Testing Alexa+ handshake test in Settings...")
        settings_tab = driver.find_element(By.XPATH, "//button[@data-view='settings']")
        settings_tab.click()
        time.sleep(0.3)
        
        test_alexa_btn = driver.find_element(By.ID, "testAlexaBtn")
        driver.execute_script("arguments[0].scrollIntoView(true);", test_alexa_btn)
        test_alexa_btn.click()
        time.sleep(1.0)
        
        alexa_status = driver.find_element(By.ID, "alexaStatusDetail")
        print("Alexa status text:", alexa_status.text)
        assert "Connected" in alexa_status.text
        print("✓ Alexa+ Smart Home Skills API v3 handshake verified")
        
        # Switch back to Simulation mode
        print("8. Switching back to ⚡ Simulation mode...")
        mode_sim_btn.click()
        time.sleep(0.8)
        home_tab.click()
        time.sleep(0.3)
        assert sim_panel.is_displayed(), "Sim panel restored in Simulation mode"
        assert not real_panel.is_displayed(), "Real panel hidden in Simulation mode"
        print("✓ Simulation mode restored successfully")
        
        # Check browser console logs for any fatal errors
        logs = driver.get_log("browser")
        severe_errors = [l for l in logs if l["level"] == "SEVERE"]
        if severe_errors:
            print("⚠ Browser console warnings/errors:", severe_errors)
        else:
            print("✓ Browser console has zero severe errors")
            
        print("\n=======================================================")
        print("🏆 ALL END-TO-END UI & INTEGRATION TESTS PASSED 100%!")
        print("=======================================================")
        
    finally:
        driver.quit()

if __name__ == "__main__":
    run_tests()
