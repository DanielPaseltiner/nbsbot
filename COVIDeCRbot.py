# -*- coding: utf-8 -*-
"""
Created on Fri May  3 12:43:41 2024

@author: Jared.Strauch
"""
from covidlabreview import COVIDlabreview
from tqdm import tqdm
import time
import traceback
from selenium.webdriver.common.alert import Alert
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import ElementNotInteractableException
from selenium.common.exceptions import StaleElementReferenceException
import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)
import pandas as pd
pd.options.mode.chained_assignment = None
from bs4 import BeautifulSoup
from datetime import datetime
from io import StringIO
import re
import numpy as np
from dateutil.relativedelta import relativedelta
from pandas._libs.tslibs.parsing import DateParseError
from epiweeks import Week

def generator():
    while True:
        yield

reviewed_ids = []
what_do = []

NBS = COVIDlabreview(production=False)
NBS.get_credentials()
NBS.log_in()
attempt_counter = 0
for _ in tqdm(generator()):
    partial_link = 'Documents Requiring Review'
    WebDriverWait(NBS,NBS.wait_before_timeout).until(EC.element_to_be_clickable((By.PARTIAL_LINK_TEXT, partial_link)))
    NBS.find_element(By.PARTIAL_LINK_TEXT, partial_link).click()
    time.sleep(1)
    
    #Sort review queue so that only case reports are listed
    clear_filter_path = '//*[@id="removeFilters"]/table/tbody/tr/td[2]/a'
    document_path = '/html/body/div[2]/form/div/table[2]/tbody/tr/td/table/thead/tr/th[2]/img'
    
    #clear all filters
    WebDriverWait(NBS,NBS.wait_before_timeout).until(EC.element_to_be_clickable((By.XPATH, clear_filter_path)))
    NBS.find_element(By.XPATH, clear_filter_path).click()
    time.sleep(5)
    
    #open description dropdown menu
    WebDriverWait(NBS,NBS.wait_before_timeout).until(EC.presence_of_element_located((By.XPATH, document_path)))
    WebDriverWait(NBS,NBS.wait_before_timeout).until(EC.element_to_be_clickable((By.XPATH, document_path)))
    NBS.find_element(By.XPATH, document_path).click()
    time.sleep(1)
    
    #clear checkboxes
    WebDriverWait(NBS,NBS.wait_before_timeout).until(EC.element_to_be_clickable((By.XPATH, '/html/body/div[2]/form/div/table[2]/tbody/tr/td/table/thead/tr/th[2]/div/label[2]')))
    NBS.find_element(By.XPATH,'/html/body/div[2]/form/div/table[2]/tbody/tr/td/table/thead/tr/th[2]/div/label[2]').click()
    time.sleep(1)
    
    #select Case Reports
    try:
        results = NBS.find_elements(By.XPATH,"//label[contains(text(),'Case')]")
        for result in results:
            result.click()
    except (NoSuchElementException, ElementNotInteractableException) as e:
        pass
    time.sleep(1)
    
    #click ok
    try:
        WebDriverWait(NBS,NBS.wait_before_timeout).until(EC.element_to_be_clickable((By.XPATH, '/html/body/div[2]/form/div/table[2]/tbody/tr/td/table/thead/tr/th[2]/div/label[1]/input[1]')))
        NBS.find_element(By.XPATH,'/html/body/div[2]/form/div/table[2]/tbody/tr/td/table/thead/tr/th[2]/div/label[1]/input[1]').click()
    except NoSuchElementException:
        #click cancel and go back to home page to wait for more ELRs
        WebDriverWait(NBS,NBS.wait_before_timeout).until(EC.element_to_be_clickable((By.XPATH, '/html/body/div[2]/form/div/table[2]/tbody/tr/td/table/thead/tr/th[2]/div/label[1]/input[2]')))
        NBS.find_element(By.XPATH,'/html/body/div[2]/form/div/table[2]/tbody/tr/td/table/thead/tr/th[2]/div/label[1]/input[2]').click()
        NBS.go_to_home()
        time.sleep(3)
        NBS.Sleep()
        #this wont work if we are not running the for loop to cycle through the queue,
        #comment out if not running the whole thing
        continue
    time.sleep(1)
    
    #sort chronologically, oldest first
    submit_date_path = '//*[@id="parent"]/thead/tr/th[3]/a'
    WebDriverWait(NBS,NBS.wait_before_timeout).until(EC.element_to_be_clickable((By.XPATH, submit_date_path)))
    NBS.find_element(By.XPATH, submit_date_path).click()
    WebDriverWait(NBS,NBS.wait_before_timeout).until(EC.element_to_be_clickable((By.XPATH, submit_date_path)))
    NBS.find_element(By.XPATH, submit_date_path).click()
    
    #Grab all ECRs in the queue to reference later. Grab the event ID so we can make sure that we
    #don't get stuck in a loop at the top of the queue if an ECR doesn't get cleared out of the queue
    
    #Grab the ECR table 
    review_queue_table_path = '//*[@id="parent"]'
    html = NBS.find_element(By.XPATH, review_queue_table_path).get_attribute('outerHTML')
    soup = BeautifulSoup(html, 'html.parser')
    review_queue_table = pd.read_html(StringIO(str(soup)))[0]
    review_queue_table.fillna('', inplace = True)
    #maybe change above '' to None
    
    #Check to see if we have looked at this ECR before by the local ID
    i = 0
    while review_queue_table["Local ID"].iloc[i] in reviewed_ids:
        i += 1
    #grab the first local ID we haven't reviewed and append it to the list for later use 
    doc_id = review_queue_table["Local ID"].iloc[i]
    reviewed_ids.append(doc_id)
    #identify the element that has the document ID to be reviewed and navigate to that Lab Report
    
    try:
        anc = NBS.find_element(By.XPATH,f"//td[contains(text(),'{doc_id}')]/../td/a")
    except NoSuchElementException:
        anc = NBS.find_element(By.XPATH,f"//font[contains(text(),'{doc_id}')]/../../td/a")
    anc.click()
    #grab from the results section, check for the various test names. Maybe use a while loop?
    tests = ["SARS", "COVID", "nCoV", "qPCR (Rutgers)", "Severe Acute Respiratory Syndrome"]
    for test in tests:
        #test_elem = NBS.find_element(By.XPATH, f'//*[@id="xmlBlock"]/ul[1]/li[contains(text(),{test})]/table[1]')
        test_table_path = f'//*[@id="xmlBlock"]/ul[1]/li[contains(text(),{test})]/table[1]'
        html = NBS.find_element(By.XPATH, test_table_path).get_attribute('outerHTML')
        soup = BeautifulSoup(html, 'html.parser')
        test_table = pd.read_html(StringIO(str(soup)))[0]

        html = NBS.page_source
        soup = BeautifulSoup(html, "html.parser")
        for tag in soup.find_all("tr"):
            if "SARS" in tag.text or "COVID" in tag.text:
                print(tag.text)
                if "Detected" in tag.text:
                    print("True")
    #go to the patient file to review investigations
    WebDriverWait(NBS,NBS.wait_before_timeout).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="srtLink"]/div/a[1]')))
    NBS.find_element(By.XPATH, '//*[@id="srtLink"]/div/a[1]').click()
    
    #Go to events tab
    WebDriverWait(NBS,NBS.wait_before_timeout).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="tabs0head1"]')))
    NBS.find_element(By.XPATH, '//*[@id="tabs0head1"]').click()
    
    #read investigations
    try:
        investigation_table = NBS.read_investigation_table()
    except NoSuchElementException:
        inv_found = False

    
    #Navigate to the lab report to be processed using the Document ID from the patient page
    case_report_table_path = '//*[@id="caseReports"]'
    case_report_table = NBS.ReadTableToDF(case_report_table_path)
    
    case_row = case_report_table[case_report_table['Event ID'] == re.findall(r'DOC\d+ME\d+',doc_id)[0]]
    case_index = int(case_row.index.to_list()[0]) + 1
    
    if case_index > 1:
        case_path = f'//*[@id="eventCaseReports"]/tbody/tr[{str(case_index)}]/td[1]/a'
    elif case_index == 1:
        case_path = '//*[@id="eventCaseReports"]/tbody/tr[1]/td[1]/a'
    WebDriverWait(NBS,NBS.wait_before_timeout).until(EC.element_to_be_clickable((By.XPATH, case_path)))
    NBS.find_element(By.XPATH, case_path).click()

    existing_investigations = None
    if type(investigation_table) == pd.core.frame.DataFrame:
        existing_investigations = investigation_table[investigation_table["Condition"].str.contains("2019 Novel Coronavirus (2019-nCoV)")]
        #existing_investigations = existing_investigations[existing_investigations["Case Status"].str.contains("Confirmed|Probable")]
        if len(existing_investigations) >= 1:
            inv_found = True
        else:
            inv_found = False     
    else:
            inv_found = False
            
    if inv_found and cov_pos:
        #associate to previous investigation
        what_do.append("Associate to investigation")
    else: 
        what_do.append("Do not associate to investigation")
        NBS.go_to_home
