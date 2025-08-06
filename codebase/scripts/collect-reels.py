import json
import time
# import sys
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class ReelLinkCollector:
    """collects reel urls from target page"""
    
    def __init__(self, max_reels=6):
        """set max reels to collect"""
        self.max_reels = max_reels
    
    def load_existing_reels(self, json_file="../data/demo-stuff/demo-reels.json"):
        """load saved reels from file"""
        try:
            with open(json_file, "r") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []
    
    def save_reels_to_json(self, reels, json_file="../data/demo-stuff/demo-reels.json"):
        """save new reels to file"""
        existing_reels = self.load_existing_reels(json_file)
        updated_reels = existing_reels + [r for r in reels if r not in existing_reels]
        
        with open(json_file, "w") as f:
            json.dump(updated_reels, f, indent=2)
        print(f"saved {len(updated_reels)} reels to {json_file}")
    
    def get_reels_with_scroll(self):
        """scroll page and collect reel links"""
        driver = webdriver.Chrome()
        driver.get("https://www.instagram.com/pubity/reels/")
        
        # manual step - handle popups first
        input("handle popups then press enter...")

        reels = set()
        last_position = 0
        retries = 0
        max_retries = 3

        while len(reels) < self.max_reels and retries < max_retries:
            # scroll down a bit
            driver.execute_script(f"window.scrollTo(0, {last_position + 900});")
            time.sleep(2)
            
            # find all reel links
            links = driver.find_elements(By.TAG_NAME, "a")
            new_links = [
                link.get_attribute("href") 
                for link in links 
                if link.get_attribute("href") and "/reel/" in link.get_attribute("href")
            ]
            
            # check if stuck
            if not new_links or len(new_links) == len(reels):
                retries += 1
                print(f"no new reels (retry {retries}/{max_retries})")
                # try alternate scroll
                driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.PAGE_DOWN)
                time.sleep(3)
            else:
                retries = 0
                reels.update(new_links)
                print(f"found {len(reels)}/{self.max_reels} reels")
            
            last_position = driver.execute_script("return window.pageYOffset")
            
            # instagram sometimes blocks further loading
            if len(reels) >= 24 and not new_links:
                print("hit instagram limit - try later")
                break

        driver.quit()
        return list(reels)[:self.max_reels]
    
    def run_collection(self):
        """main function to run collection"""
        print("starting reel collection...")
        print("note: handle popups when browser opens")
        reels = self.get_reels_with_scroll()
        self.save_reels_to_json(reels)
        print("\ndone!")

if __name__ == "__main__":
    collector = ReelLinkCollector(max_reels=6)
    collector.run_collection()