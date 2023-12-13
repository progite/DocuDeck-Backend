import os
import requests
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def extract_pdfs(url: str, query: str):
    #see ssl verification
    # url = "https://wbpwd.gov.in/ETender_Guideline"
    # url = "https://powermin.gov.in/content/guidelines-resolutions-notifications-transmission"
    # query = 'test'
    folder_loc = r'C:\Users\progg\Desktop\desktop_p\DocuDeck\policies\\' + query
    if not os.path.exists(folder_loc):
        os.mkdir(folder_loc)

    response = requests.get(url, verify=False)
    # print(response)
    soup = BeautifulSoup(response.text, "html.parser")
    with open ('doc.txt', 'w', encoding = 'utf-8') as file:
        file.write(str(list(link for link in soup.find_all('a'))))

    
    for link in soup.select("a[href$='.pdf']"):
        filename = os.path.join(folder_loc,link['href'].split('/')[-1])
        # print(filename)
        with open(filename, 'wb') as f:
            # print(filename)
            f.write(requests.get(urljoin(url,link['href']), verify=False).content)

#now search the web and go into the search results and extract the content from that page
#search the web

def search_web():
    base = "https://eprocure.gov.in/cppp/"
    queries = ["rulesandprocs", "staterulesandprocs"]
    
    for query in queries:
        extract_pdfs(base + query, query)
        # response = requests.get(base + query, verify=False)
        # soup = BeautifulSoup(response.text, "html.parser")
        # print(soup)
# search_web()
# extract_pdfs("")

def extract_nav_tabs():
    url = "https://eprocure.gov.in/cppp/rulesandprocs"
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

        
        folder_loc = r'C:\Users\progg\Desktop\desktop_p\DocuDeck\policies\\' + str(idx)
        if not os.path.exists(folder_loc):
            os.mkdir(folder_loc)


        for link in soup.select("a[href$='.pdf']"):
            filename = os.path.join(folder_loc,link['href'].split('/')[-1])
            # print(filename)
            with open(filename, 'wb') as f:
                # print(filename)
                f.write(requests.get(urljoin(url,link['href']), verify=False).content)

        # print(soup.prettify())
extract_nav_tabs()