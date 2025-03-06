from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

BASE_URL = "https://awardsdatabase.oscars.org/"
driver = webdriver.Chrome()

try:
    driver.get(BASE_URL)
    
    # Wait until the search form is present
    WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.ID, "searchForm"))
    )
    
    # Wait until the Award Category select element is present (even if hidden)
    award_category_element = WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.ID, "BasicSearchView_AwardCategory"))
    )
    
    # List of desired values to select
    desired_values = ['1', '3', '10', '19']
    
    # Use JavaScript to iterate over options and mark the desired ones as selected
    driver.execute_script("""
        var select = arguments[0];
        var values = arguments[1];
        for (var i = 0; i < select.options.length; i++) {
            if (values.indexOf(select.options[i].value) > -1) {
                select.options[i].selected = true;
            }
        }
        // Trigger the change event so that any listeners update accordingly
        select.dispatchEvent(new Event('change'));
    """, award_category_element, desired_values)
    
    # Wait for the search button to be clickable and click it
    search_button = WebDriverWait(driver, 15).until(
        EC.element_to_be_clickable((By.ID, "btnbasicsearch"))
    )
    search_button.click()
    
    # Wait for the results page to load
    time.sleep(3)
    
    # Scroll to the bottom of the page
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    
    # Optional: wait a bit to observe the scrolled page
    time.sleep(3)
    
finally:
    driver.quit()
