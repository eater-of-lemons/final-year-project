import json
import time
import random
import os
import re
from datetime import datetime
from selenium import webdriver
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import StaleElementReferenceException, TimeoutException

class ReelDataCollector:
    """collects likes, comments and metadata for reels"""
    
    def __init__(self):
        """set default config values"""
        self.reels_file = "../data/demo-stuff/demo-reels.json"
        self.output_file = "../data/demo-stuff/demo-reels-data.json"
        self.target_comments = 100
        self.delay_range = (5, 10)
        self.max_load_attempts = 10
        self.batch_size = 3
        self.comment_load_delay = (1, 2)
        self.max_tabs = 3
    
    def get_driver(self, headless=True):
        """setup chrome browser"""
        options = Options()
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--no-sandbox")
        if headless:
            options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        return webdriver.Chrome(options=options)
    
    def manual_login(self):
        """login to instagram manually"""
        print("\n=== login required ===")
        driver = self.get_driver(headless=False)
        driver.get("https://www.instagram.com/accounts/login/")
        input("press enter after login...")
        
        cookies = driver.get_cookies()
        driver.quit()
        
        headless_driver = self.get_driver(headless=True)
        headless_driver.get("https://www.instagram.com/")
        
        for cookie in cookies:
            try:
                headless_driver.add_cookie(cookie)
            except Exception as e:
                print(f"skipping bad cookie: {cookie.get('name', 'unknown')}")
        
        return headless_driver
    
    def extract_meta_data(self, html):
        """get likes, comments, date from html"""
        soup = BeautifulSoup(html, 'html.parser')
        meta = soup.find('meta', attrs={'name': 'description'})
        
        if not meta:
            return None, None, None
        
        content = meta.get('content', '')
        
        likes_match = re.search(r'(\d+\.?\d*[KkMm]?) likes', content)
        comments_match = re.search(r'(\d+\.?\d*[KkMm]?) comments', content)
        date_match = re.search(r'on (\w+ \d{1,2}, \d{4}):', content)
        
        likes = likes_match.group(1) if likes_match else '0'
        comments = comments_match.group(1) if comments_match else '0'
        post_date = datetime.strptime(date_match.group(1), "%B %d, %Y").strftime("%Y-%m-%d") if date_match else None
        
        return likes, comments, post_date
    
    def load_all_comments(self, driver):
        """load and collect comments"""
        comments_dict = {}
        attempts = 0
        last_count = 0
        
        while attempts < self.max_load_attempts and len(comments_dict) < self.target_comments:
            current_count = len(comments_dict)
            
            try:
                comment_elements = driver.find_elements(
                    By.XPATH, "//ul[.//h3 and .//span[contains(@dir, 'auto')]]"
                )
                
                for ul in comment_elements:
                    try:
                        _ = ul.location_once_scrolled_into_view
                        author = ul.find_element(By.TAG_NAME, "h3").text.strip()
                        text = ul.find_element(By.XPATH, ".//span[contains(@dir, 'auto')]").text.strip()
                        unique_id = f"{author[:10]}_{text[:30]}"
                        
                        if unique_id not in comments_dict:
                            comments_dict[unique_id] = {
                                "text": text,
                                "author": author,
                            }
                            
                            if len(comments_dict) >= self.target_comments:
                                break
                    except StaleElementReferenceException:
                        continue
                    except Exception as e:
                        print(f"error processing comment: {str(e)}")
                        continue
                
                if len(comments_dict) > last_count:
                    attempts = 0
                    last_count = len(comments_dict)
                else:
                    attempts += 1
                
                try:
                    load_button = WebDriverWait(driver, 3).until(
                        EC.presence_of_element_located(
                            (By.XPATH, "//button[.//*[local-name()='svg'][@aria-label='Load more comments']]")
                        )
                    )
                    driver.execute_script("arguments[0].click();", load_button)
                    time.sleep(random.uniform(*self.comment_load_delay))
                except:
                    attempts += 1
            
            except Exception as e:
                print(f"error getting comments: {str(e)}")
                attempts += 1
                time.sleep(1)
        
        return [{"text": v["text"], "author": v["author"]} for v in comments_dict.values()][:self.target_comments]
    
    def process_reel_in_tab(self, driver, tab_index, reel_url):
        """process one reel in browser tab"""
        try:
            driver.switch_to.window(driver.window_handles[tab_index])
            driver.get(reel_url)
            
            WebDriverWait(driver, 10).until(
                lambda d: "reel" in d.current_url
            )
            time.sleep(2)
            
            html = driver.page_source
            meta_likes, meta_comments, post_date = self.extract_meta_data(html)
            
            likes = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located(
                    (By.XPATH, "//a[contains(@href, '/liked_by/')]")
                )
            ).text.split()[0]

            comments = self.load_all_comments(driver)
            
            shortcode = reel_url.split("/reel/")[1].strip("/")
            return {
                "shortcode": shortcode,
                "data": {
                    "url": reel_url,
                    "likes": likes,
                    "meta_likes": meta_likes,
                    "meta_comments": meta_comments,
                    "post_date": post_date,
                    "comments": comments,
                }
            }
        
        except Exception as e:
            print(f"error scraping {reel_url}: {str(e)}")
            shortcode = reel_url.split("/reel/")[1].strip("/")
            return {"shortcode": shortcode, "error": str(e)}
    
    def save_progress(self, results, output_file):
        """save results to file"""
        temp_file = output_file + ".tmp"
        
        existing = {}
        if os.path.exists(output_file):
            try:
                with open(output_file, 'r') as f:
                    existing = json.load(f)
            except:
                pass
        
        merged = {**existing, **results}
        
        with open(temp_file, 'w') as f:
            json.dump(merged, f, indent=2, ensure_ascii=False)
        
        os.replace(temp_file, output_file)
        print(f"saved progress ({len(results)} new reels, {len(merged)} total)")
    
    def run_collection(self):
        """main function to run data collection"""
        driver = self.manual_login()
        
        with open(self.reels_file) as f:
            reels = json.load(f)
        
        processed = set()
        if os.path.exists(self.output_file):
            try:
                with open(self.output_file, 'r') as f:
                    processed = set(json.load(f).keys())
            except:
                pass
        
        todo_reels = [url for url in reels if url.split("/reel/")[1].strip("/") not in processed]
        
        print(f"\ntotal reels to process: {len(todo_reels)} (skipping {len(reels) - len(todo_reels)} done)")
        
        for _ in range(1, self.max_tabs):
            driver.switch_to.new_window('tab')
            time.sleep(1)
        
        results = {}
        current_batch = []
        
        for i, reel_url in enumerate(todo_reels, 1):
            current_batch.append(reel_url)
            
            if len(current_batch) == self.max_tabs or i == len(todo_reels):
                print(f"\nprocessing batch of {len(current_batch)} reels...")
                
                for tab_index, reel_url in enumerate(current_batch):
                    result = self.process_reel_in_tab(driver, tab_index, reel_url)
                    
                    if "data" in result:
                        results[result["shortcode"]] = result["data"]
                        print(f"tab {tab_index}: got {result['data']['likes']} likes, {len(result['data']['comments'])} comments")
                        print(f"meta: {result['data']['meta_likes']} likes, {result['data']['meta_comments']} comments, posted {result['data']['post_date']}")
                    elif "error" in result:
                        print(f"failed {result['shortcode']}: {result['error']}")
                    
                    if tab_index < len(current_batch) - 1:
                        time.sleep(random.uniform(1, 3))
                
                current_batch = []
                
                if i % self.batch_size == 0 or i == len(todo_reels):
                    self.save_progress(results, self.output_file)
                    results = {}
                
                if i < len(todo_reels):
                    delay = random.uniform(*self.delay_range)
                    print(f"waiting {delay:.1f} seconds...")
                    time.sleep(delay)
        
        print(f"\ndone processing {len(todo_reels)} reels")
        driver.quit()

if __name__ == "__main__":
    collector = ReelDataCollector()
    collector.run_collection()