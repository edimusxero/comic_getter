import json
import re
import operator
import time
import os
import shutil
import requests

from pathlib import Path
from tqdm import tqdm
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.ui import Select
from selenium.webdriver.chrome.options import Options


class RCO_Comic:
    '''Collection of functions that allow to download a 
    readcomiconline.to comic with all it's issues.'''

    def __init__(self, *args):
        '''Initializes main_link attribute. '''
        # Seed link that contains all the links of the different issues.
        self.main_link = args[0]
        
        try:
            self.zip_these = args[1]
        except:
            pass
        # Extract data from config.json
        dir_path = Path(f"{os.path.dirname(os.path.abspath(__file__))}"
                        "/config.json")
        with open(dir_path) as config:
            data = json.load(config)

        self.driver_path = data["chromedriver_path"]
        self.download_directory_path = data["download_dir"]

        if not data.get("visibility"):
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument('--no-sandbox')
            self.options = chrome_options
        else:
            chrome_options = Options()
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--window-size=1,1')
            self.options = chrome_options

    def get_issues_links(self):
        '''Gather all individual issues links from main link.'''

        # A chrome window is opened to bypass cloudflare.
        driver = webdriver.Chrome(executable_path=self.driver_path,
                                  options=self.options)
        driver.get(self.main_link)
        # A 60 second margin is given for browser to bypass cloudflare and
        # load readcomiconline.to logo.
        wait = WebDriverWait(driver, 60)
        element = wait.until(ec.visibility_of_element_located(
            (By.LINK_TEXT, "ReadComicOnline.to")))
        # The whole html code is downloaded.
        body = driver.find_element_by_tag_name("body")
        body = str(body.get_attribute('innerHTML'))
        driver.quit()

        # Re module is used to extract relevant links.
        core_link = "https://readcomiconline.to"
        target_links = re.findall(r'(?<=")/[cC]omic/.+?id=\d+(?=")', body)
        issues_links = []
        for link in target_links:
            full_link = core_link + link
            issues_links.append(full_link)
        print("All issues links were gathered.", flush=True)
        return issues_links

    def get_pages_links(self, issue_link):
        ''' Gather the links of each page of an issue.'''

        driver = webdriver.Chrome(executable_path=self.driver_path,
                                  options=self.options)
        driver.set_window_size(1, 1)
        driver.get(issue_link)

        # A 3600 second = 1 hour time gap is given for browser to bypass
        # cloudflare and for browser to fetch all issues pages before
        # triggering an exception. Such a time is never to be reached
        # and as soon as these events happen the program will continue.
        driver.set_window_size(800, 600)
        wait = WebDriverWait(driver, 3600)
        wait.until(ec.visibility_of_element_located(
            (By.LINK_TEXT, "ReadComicOnline.to")))

        # An option to load all pages of the issue in the same tab is selected.
        select = Select(driver.find_element_by_id('selectReadType'))
        select.select_by_index(1)
        time.sleep(2)

        # An explicit wait is trigger to wait for imgLoader to disappear.
        wait.until(ec.invisibility_of_element((By.ID, "imgLoader")))
        element = driver.find_element_by_id("divImage")
        raw_pages_links = element.get_attribute('innerHTML')
        driver.quit()

        # Re module is used to extract relevant links.
        pages_links = re.findall(r'(?<=")https://2.bp.blogspot.com/.+?(?=")', raw_pages_links)

        # Pages links, comic name and issue name are packed inside issue_data
        # tuple.
        comic_issue_name = self.get_comic_and_issue_name(issue_link)
        issue_data = (pages_links, comic_issue_name[1], comic_issue_name[2])
        issue_name, issue_number = self.clean_title_name(comic_issue_name[1],comic_issue_name[2])
        print(f"All links to pages of {issue_name} {issue_number} were gathered.", flush=True)
        return issue_data

    def get_comic_and_issue_name(self, issue_link):
        '''Finds out comic and issue name from link.'''

        # Re module is used to get issue and comic name.
        name_and_issue = re.search(r"(?<=[cC]omic/)(.+?)/(.+?)(?=\?)", issue_link)

        # comic_issue_names[0] is the comic's link name, comic_issue_names[1]
        # is the comic name and comic_issue_names[2] is the issues name.
        comic_issue_name = [issue_link, name_and_issue[1], name_and_issue[2]]
        return comic_issue_name

    def is_comic_downloaded(self, comic_issue_name):
        '''Checks if comic has already been downloaded.'''

        download_path = Path(f"{self.download_directory_path}"
                             f"/{comic_issue_name[1]}/{comic_issue_name[2]}")
        if os.path.exists(download_path):
            print(f"{comic_issue_name[2]} has already been downloaded.", flush=True)
            return True
        else:
            return False

    def clean_title_name(self, issue_name, issue_number):
        clean_title = re.sub(r'-', r' ', issue_name).strip()   
        issue_match = re.match(r"^(\bIssue\b|\bAnnual\b)-([0-9-].*)$", issue_number.strip())
        issue_type = issue_match.group(1)
        number = issue_match.group(2)
        number = re.sub(r'-', r'.', number)

        if (float(number) < 10):
            number = '#00' + number
        elif (float(number) >= 10) and (float(number) < 100):
            number = '#0' + number
        else:
            number = '#' + number

        if issue_type == 'Annual':
            number = (f"Annual {number}")

        return(clean_title, number)

    def download_all_pages(self, issue_data):        
        comic_series_name = issue_data[1]
        comic_issue_number = issue_data[2]

        cleaned_name, cleaned_number = self.clean_title_name(comic_series_name, comic_issue_number)
        full_name = (f"{cleaned_name} {cleaned_number}")

        root_path = Path(f"{self.download_directory_path}/{cleaned_name}")
        download_path = Path(f"{root_path}/{full_name}")
        if not os.path.exists(download_path):
            os.makedirs(download_path)
        else:
            print(f"{full_name} has already been downloaded.", flush=True)
            return
        print(f"Started downloading {full_name}", flush=True)

        with tqdm(total=len(issue_data[0])) as pbar:
            for index, link in enumerate(issue_data[0]):
                page_path = Path(f"{download_path}/page{index}.jpg")
                page = requests.get(link, stream=True)
                with open(page_path, 'wb') as file:
                    file.write(page.content)
                pbar.update(1)

        print(f"Finished downloading {full_name}", flush=True)
        
        try:
            if(self.zip_these):
                self.create_zip(download_path, root_path, full_name)
        except:
            pass

    def create_zip(self, root, issue_loc, name):
        dl_name = (f"{issue_loc}/{name}")
        shutil.make_archive(dl_name, 'zip', root)
        if os.path.exists(str(root) + '.zip'):
            print(f"Zipping {name} complete!", flush=True)
            shutil.rmtree(str(root))
