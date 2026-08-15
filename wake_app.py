import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

# Set up headless Chrome options for GitHub Actions environment
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")

driver = webdriver.Chrome(options=chrome_options)

# ⚠️ CHANGE THIS TO YOUR OTHER STREAMLIT APPLICATION'S URL
APP_URL = "https://talentalign.streamlit.app/"

print(f"Visiting {APP_URL}...")
driver.get(APP_URL)
time.sleep(12)  # Give the page ample time to load all elements

try:
    # Target Streamlit's specific "Yes, get this app back up!" button text
    buttons = driver.find_elements(By.TAG_NAME, "button")
    woke_up = False
    for button in buttons:
        if "get this app back up" in button.text.lower():
            button.click()
            print("Detected sleeping app! Successfully clicked the wake-up button.")
            time.sleep(15)  # Wait for the cloud container to spin back up
            woke_up = True
            break
    
    if not woke_up:
        print("Application is already awake and operational.")
        
except Exception as e:
    print(f"An error occurred while inspecting the page: {e}")

driver.quit()
