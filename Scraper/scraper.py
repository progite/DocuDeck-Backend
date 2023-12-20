import os
import requests
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def download_file(filename: str, link: str):
    with open(filename, 'wb') as file:
        file.write(requests.get(link, verify=False).content)

def extract_pdfs(base: str):
    
    # queries = ["rulesandprocs", "staterulesandprocs"]
    queries = ['policies']
    for query in queries:
        # url = base + query
        url = base
        folder_loc = r'C:\Users\progg\Desktop\desktop_p\DocuDeck\Scraper\policies\deptDefence'
        folder_loc = os.path.join(folder_loc, query)
        if not os.path.exists(folder_loc):
            os.mkdir(folder_loc)

        response = requests.get(url, verify=False)
        soup = BeautifulSoup(response.text, "html.parser")
        
        
        for link in soup.select("a[href$='.pdf']"):
            filename = os.path.join(folder_loc,link['href'].split('/')[-1])
            download_file(filename, urljoin(url, link['href']))
        
        for idx, td_tag in enumerate(soup.find_all('td')):
            a_tag = td_tag.find('a', href=True)
            if a_tag:
                filename = os.path.join(folder_loc, str(idx) + '.pdf')
                download_file(filename, a_tag['href'])
        
# extract_pdfs("https://eprocure.gov.in/cppp/")
# extract_pdfs(r"https://powermin.gov.in/en/circular?field_division_value=All&field_date_value%5Bvalue%5D%5Bdate%5D=&title=procurement%20policy")

extract_pdfs(r"https://cgda.nic.in/index.php?page=manuals")
def extract_nav_tabs(url: str):
    driver = webdriver.Firefox()
    driver.get(url)
    
    nav_tabs = driver.find_element(By.CLASS_NAME, 'nav-tabs')
    tabs = nav_tabs.find_elements(By.TAG_NAME, 'li')
    for idx, tab in enumerate(tabs):
        tab.click()
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'tab-content')))

        # Use BeautifulSoup to parse the current tab's content
        tab_content = driver.find_element(By.CLASS_NAME,'tab-content')
        soup = BeautifulSoup(tab_content.get_attribute('outerHTML'), 'html.parser')

        with open ('doc'+str(idx)+'.txt', 'w', encoding = 'utf-8') as file:
            file.write(str(soup.prettify()))

        
        folder_loc = ''
        if not os.path.exists(folder_loc):
            os.mkdir(folder_loc)


        for link in soup.select("a[href$='.pdf']"):
            filename = os.path.join(folder_loc,link['href'].split('/')[-1])
            download_file(filename, urljoin(url,link['href']))
            
# extract_nav_tabs()