import os
import pyautogui
import time

from os import path
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from core.config import PROJECT_SETTING
from core.database import SQLiteDB
from core.metadata_editor import edit_mp3_metadata
from core.update_chromedriver import ChromeDriverUpdater

class WebsiteDriver(webdriver.Chrome):
    def __init__(self, driver_path=PROJECT_SETTING.DRIVER_PATH, teardown=False, base_path=PROJECT_SETTING.JACKSON, title=None) -> None:
        self.mp3_urls = []
        self.default_path = PROJECT_SETTING.DEFAULT_PATH

        download_path = f"{base_path}\\{title}"
        os.makedirs(download_path, exist_ok=True)

        # Set the download directory
        chrome_options = Options()
        chrome_options.add_argument("--start-maximized")
        chrome_options.add_argument("--log-level=0")
        chrome_options.add_argument("--dns-prefetch-disable")
        chrome_options.add_experimental_option('excludeSwitches', ['enable-logging', 'enable-automation'])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_experimental_option("prefs", {
            "download.default_directory": self.default_path,
            "download.prompt_for_download": True,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True
        })

        self.driver_path = driver_path
        self.chrome_service = Service(self.driver_path)
        self.teardown = teardown
        self.download_path = download_path
        super(WebsiteDriver, self).__init__(service=self.chrome_service, options=chrome_options)
        self.implicitly_wait(5)

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.teardown:
            self.quit()

    def scrape_website(self, url):
        self.get(url)

        # Wait for the "plList" class to be visible
        wait = WebDriverWait(self, 100)
        pl_list = wait.until(EC.visibility_of_element_located((By.ID, "plList")))

        # Count the number of items in the list
        num_items = len(pl_list.find_elements(By.TAG_NAME, "li"))

        # Find the "btnNext" button
        btn_next = wait.until(EC.visibility_of_element_located((By.ID, "btnNext")))

        # Scroll the element into view
        self.execute_script("arguments[0].scrollIntoView(true);", btn_next)

        # Click the "btnNext" button for each item in the list
        for i in range(num_items):

            if i > 0:
                # Trigger the click event manually using JavaScript
                self.execute_script("arguments[0].click();", btn_next)
            
            # Wait for the "audio1" element to be present
            audio1_element = wait.until(EC.presence_of_element_located((By.XPATH, "//*[@id='audio1']")))
            # Get the "src" attribute value
            mp3_url = audio1_element.get_attribute("src")
            self.mp3_urls.append(mp3_url)


    def download_mp3_files(self, title) -> None:

        wait = WebDriverWait(self, 20)

        for ind, mp3_url in enumerate(self.mp3_urls):
            self.execute_script("window.open('');")
            self.switch_to.window(self.window_handles[-1])
            self.get(mp3_url)
            current_chapter_name = f"Chapter {ind} - {title}.mp3"
            num_attempts = 0
            max_attempts = 3
            
            # Wait for the page to load                 
            wait.until(EC.visibility_of_all_elements_located((By.TAG_NAME, "body")))
            
            time.sleep(2.5)
            pyautogui.press('tab', presses=5, interval=.1)
            
            time.sleep(.5)
            pyautogui.press('enter', presses=2)
            
            time.sleep(1)
            pyautogui.write(message=current_chapter_name, interval=.1)
            
            time.sleep(2)
            pyautogui.press('enter', presses=1)
            
            # Wait for files to finish downloading
            while num_attempts < max_attempts:
                try:
                    wait.until(lambda driver: self.filename_matches(current_chapter_name))
                    new_path = os.path.join(self.download_path, current_chapter_name)
                    os.rename(os.path.join(self.default_path, current_chapter_name), new_path)
                    break  # Success

                except TimeoutException:
                    num_attempts += 1
                    if num_attempts == max_attempts:
                        print(f"Download failed after {max_attempts} attempts for URL: {mp3_url}")
            
            # Close the current tab
            self.close()
            self.switch_to.window(self.window_handles[0])

    def filename_matches(self, current_chapter_name) -> bool: # Helper function for wait.until
        file_path = os.path.join(self.default_path, current_chapter_name)
        return path.exists(file_path) is True and file_path.endswith(".mp3")


def get_user_path(user_name):
    if user_name == "Jackson":
        return PROJECT_SETTING.JACKSON
    elif user_name == "Alicia":
        return PROJECT_SETTING.ALICIA
    else:
        print(f"Audiobook doesn't have a set user for path: {user_name}")
        return None

def check_and_add_audiobooks(db, audiobooks_to_add) -> None:
    books_to_add = []
    
    # Check each audiobook in the list
    for audiobook in audiobooks_to_add:
        title, author, series_name, book_number, url, user = audiobook
        
        # Check if the audiobook already exists in the database by title and author
        existing_books = db.get_audiobooks(column_name="title", value=title)
        
        # If no existing book with the same title and author is found, add it to the list to be added
        if not any(book for book in existing_books if book[2] == author):  # book[2] is author field
            books_to_add.append(audiobook)
    
    # If there are books to add, call the add_audiobooks method
    if books_to_add:
        db.add_audiobooks(books_to_add)
    else:
        print("No new books to add")


def download_books(db) -> None:
    audiobooks = db.get_audiobooks(column_name='downloaded', value=0)  # Get books from the database
    for audiobook in audiobooks:
        user_path = get_user_path(audiobook[6])
        if user_path:
            with WebsiteDriver(teardown=True, base_path=user_path, title=audiobook[1]) as driver:  # Index for 'title'
                driver.scrape_website(url=audiobook[5])  # Index for 'url'
                driver.download_mp3_files(title=audiobook[1])
            db.mark_audiobook_bool(column_name='downloaded', audiobook_id=audiobook[0])

def edit_books(db) -> None:
    audiobooks = db.get_audiobooks(column_name='edited', value=0)  # Get books from the database
    for audiobook in audiobooks:
        user_path = get_user_path(audiobook[6])
        if user_path:
            book_path = os.path.join(user_path, audiobook[1])
            print(f"book is: {audiobook}")

            edit_mp3_metadata(folder_path=book_path, audiobook_data=audiobook, db=db)
            db.mark_audiobook_bool(column_name='edited', audiobook_id=audiobook[0])


def check_chromedriver() -> None:
    # Initialize the updater with the ChromeDriver path and download directory
    updater = ChromeDriverUpdater(driver_path=PROJECT_SETTING.DRIVER_PATH, download_dir=PROJECT_SETTING.DEFAULT_PATH)
    
    # Update the ChromeDriver if needed
    updater.update_chromedriver()

    # Your main program logic here
    print("Finished downloading chromedriver. Now downloading books...")


# Example usage
if __name__ == "__main__":

    audiobooks_to_add = [
        #(title, author, series name, book # in series, url, user)
        ("Heretical Fishing - Book 3", "Haylock Jobson","Heretical Fishing: A Cozy Guide to Annoying the Cults, Outsmarting the Fish, and Alienating Oneself", 3,  "https://tokybook.com/heretical-fishing-3", "Jackson"),
        ("All the Skills - Book 4", "Honour Rae","All the Skills Series", 4,  "https://tokybook.com/all-the-skills-4-a-deck-building-litrpg", "Jackson"),
        # ... Add more audiobooks here 
    ]

    db = SQLiteDB()  # Create a database instance
    db.create_audiobook_table()  # Ensure the audiobooks table exists
    check_and_add_audiobooks(db=db, audiobooks_to_add=audiobooks_to_add)
    check_chromedriver()

    def main() -> None:
        download_books(db=db)
        edit_books(db=db)
    main()