# -*- coding: utf-8 -*-
"""
Created on Tue Feb 27 14:20:22 2024

@author: Jared.Strauch
"""
"""
Save the matched NBS/MVPS excel sheet filtered to only include investigations in NBS and not in MVPS to the nbsbot folder. Going to make this fairly limited for now.
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
from selenium.common.exceptions import TimeoutException
import pandas as pd


rejected_ids = []
reviewed_inv = []
df = pd.read_excel("2024matched_filtered_NBS_only.xlsx")

NBS = COVIDlabreview(production=True)
NBS.get_credentials()
NBS.log_in()

for i in tqdm(range(len(df))):
    inv_id = df.loc[i,'local_ID']
    
    if inv_id in reviewed_inv:
        print("Reviewed already")
        continue
    
    id_type_path = '//*[@id="patientSearchByDetails"]/table[2]/tbody/tr[3]/td[2]/img'
    WebDriverWait(NBS,NBS.wait_before_timeout).until(EC.presence_of_element_located((By.XPATH, id_type_path)))
    NBS.find_element(By.XPATH, id_type_path).click()
    
    WebDriverWait(NBS,NBS.wait_before_timeout).until(EC.presence_of_element_located((By.XPATH, '//*[@id="ESR100"]/option[6]')))
    NBS.find_element(By.XPATH, '//*[@id="ESR100"]/option[6]').click()
    
    
    event_id_path = '//*[@id="ESR101"]'
    WebDriverWait(NBS,NBS.wait_before_timeout).until(EC.presence_of_element_located((By.XPATH, event_id_path)))
    NBS.find_element(By.XPATH, event_id_path).send_keys(inv_id)
    
    search_path = '//*[@id="patientSearchByDetails"]/table[2]/tbody/tr[8]/td[2]/input[1]'
    WebDriverWait(NBS,NBS.wait_before_timeout).until(EC.element_to_be_clickable((By.XPATH, search_path)))
    NBS.find_element(By.XPATH, search_path).click()
    
    patient_file_path = '//*[@id="searchResultsTable"]/tbody/tr/td[1]/a'
    WebDriverWait(NBS,NBS.wait_before_timeout).until(EC.element_to_be_clickable((By.XPATH, patient_file_path)))
    NBS.find_element(By.XPATH, patient_file_path).click()
    
    events_path = '//*[@id="tabs0head1"]'
    WebDriverWait(NBS,NBS.wait_before_timeout).until(EC.element_to_be_clickable((By.XPATH, events_path)))
    NBS.find_element(By.XPATH, events_path).click()
    
    status_elem = NBS.find_element(By.XPATH,f"//td[contains(text(),'{inv_id}')]/../td[2]")
    status = status_elem.text
    condition_elem = NBS.find_element(By.XPATH,f"//td[contains(text(),'{inv_id}')]/../td[3]")
    condition = condition_elem.text
    case_status_elem = NBS.find_element(By.XPATH,f"//td[contains(text(),'{inv_id}')]/../td[4]")
    case_status = case_status_elem.text
    notification_elem = NBS.find_element(By.XPATH,f"//td[contains(text(),'{inv_id}')]/../td[5]")
    notification = notification_elem.text
    
    time.sleep(5)
    
    if status == "Closed" and condition.upper() == df.loc[i,"condition"].upper() and case_status == df.loc[i,"Case_Status"] and notification == "COMPLETED":
        anc = NBS.find_element(By.XPATH,f"//td[contains(text(),'{inv_id}')]/../td/a")
        anc.click()
        time.sleep(1)
        try:
            edit_path = '//*[@id="delete"]'
            WebDriverWait(NBS,NBS.wait_before_timeout).until(EC.element_to_be_clickable((By.XPATH, edit_path)))
            NBS.find_element(By.XPATH, edit_path).click()
        except TimeoutException:
            edit_path = '//*[@id="Edit"]'
            WebDriverWait(NBS,NBS.wait_before_timeout).until(EC.element_to_be_clickable((By.XPATH, edit_path)))
            NBS.find_element(By.XPATH, edit_path).click()
            
            WebDriverWait(NBS, 10).until(EC.alert_is_present())
            NBS.switch_to.alert.accept()
            time.sleep(1)
            
            submit_path = '//*[@id="Submit"]'
            WebDriverWait(NBS,NBS.wait_before_timeout).until(EC.element_to_be_clickable((By.XPATH, submit_path)))
            NBS.find_element(By.XPATH, submit_path).click()
            
            reviewed_inv.append(inv_id)
            
            NBS.go_to_home()
            time.sleep(3)
            print("Notification retriggered")
            continue
           
        WebDriverWait(NBS, 10).until(EC.alert_is_present())
        NBS.switch_to.alert.accept()
        time.sleep(1)
        
        submit_path = '//*[@id="SubmitTop"]'
        WebDriverWait(NBS,NBS.wait_before_timeout).until(EC.element_to_be_clickable((By.XPATH, submit_path)))
        NBS.find_element(By.XPATH, submit_path).click()
        
        reviewed_inv.append(inv_id)
        
        NBS.go_to_home()
        time.sleep(3)
        print("Notification retriggered")
    else: 
        print("Did not retrigger notification")
        rejected_ids.append(inv_id)
        reviewed_inv.append(inv_id)
        time.sleep(3)
        NBS.go_to_home()
        
        