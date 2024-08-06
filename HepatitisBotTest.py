# -*- coding: utf-8 -*-
"""
Created on Tue Jan  9 13:14:44 2024

@author: Jared.Strauch
"""

from covidnotificationreview import COVIDnotificationreview
from tqdm import tqdm
import time
import traceback
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import NoSuchElementException
import pandas as pd

NBS = COVIDnotificationreview(production=False)
NBS.get_credentials()
NBS.log_in()

partial_link = 'Documents Requiring Review'
NBS.find_element(By.PARTIAL_LINK_TEXT, partial_link).click()
time.sleep(3)

""" Sort review queue so that only hepatitis cases are listed """
clear_filter_path = '//*[@id="removeFilters"]/table/tbody/tr/td[2]/a'
description_path = '/html/body/div[2]/form/div/table[2]/tbody/tr/td/table/thead/tr/th[5]/img'

#clear all filters
NBS.find_element(By.XPATH, clear_filter_path).click()
time.sleep(3)

#open description dropdown menu
NBS.find_element(By.XPATH, description_path).click()
time.sleep(3)

#clear checkboxes
NBS.find_element(By.XPATH,'//*[@id="parent"]/thead/tr/th[5]/div/label[2]/input').click()
time.sleep(3)

#select all hepatitis tests
#This is probably not the most efficient method but it works for now
tests = ["Hepatitis B virus surface Ab [Presence] in Serum by Immunoassay", "Hepatitis B virus surface Ab [Units/volume] in Serum by Immunoassay", "Hepatitis B virus surface Ag [Presence] in Serum", "Hepatitis C virus Ab [Presence] in Serum", "Hepatitis C virus RNA", "Hepatitis C virus Ab.IgG", "Hepatitis C virus genotype", "HCV RNA SERPL NAA+PROBE-ACNC", "HCV RNA SERPL NAA+PROBE-LOG IU", "HCV AB SERPL QL IA", "Hepatitis C virus RNA [Units/volume] (viral load) in Serum or Plasma by Probe and target amplification method", "Hepatitis C virus RNA [Units/volume] (viral load) in Serum or Plasma by NAA with probe detection", "Hepatitis B virus core Ab [Presence] in Serum", "Hepatitis B virus surface Ag [Presence] in Serum or Plasma by Confirmatory method", "Hepatitis A virus IgM Ab [Presence] in Serum", "Hepatitis B virus core IgM Ab [Presence] in Serum", "HCV RNA SerPl NAA+probe-aCnc", "HCV Ab SerPl Ql IA", "HBV DNA SerPl NAA+probe-Log IU", "HBV DNA SerPl NAA+probe-aCnc", "Hepatitis C virus Ab [Presence] in Serum or Plasma by Immunoassay", "Hepatitis C virus genotype [Identifier] in Serum or Plasma by NAA with probe detection", "HCV Ab Ser Ql", "Hepatitis C virus genotype [Identifier] in Unspecified specimen by Probe and target amplification method", "HBV core IgG+IgM Ser Ql", "HCV RNA SerPl PCR-aCnc", "HBV Core IgM Ser QL"]
for test in tests:
    try:
        NBS.find_element(By.XPATH,f"//label[contains(text(),'{test}')]").click()
    except NoSuchElementException:
        pass
time.sleep(3)

#click ok
NBS.find_element(By.XPATH,'/html/body/div[2]/form/div/table[2]/tbody/tr/td/table/thead/tr/th[5]/div/label[1]/input[1]').click()
time.sleep(3)

#grab all ELRs in queue to reference later
#review_queue_table_path = '//*[@id="parent"]/tbody/tr[1]/td[8]'
#review_queue_table = NBS.ReadTableToDF(review_queue_table_path)
#print(review_queue_table)

#Grab the event ID from the first report in the queue. I'm not a huge fan of this, might need to change later if we aren't updating the queue.
event = NBS.find_element(By.XPATH, '//*[@id="parent"]/tbody/tr[1]/td[8]')
event_id = event.text
print(event_id)
#what if we went to the patient instead of the lab report so we could look for investigations? this might make it difficult to find the right lab. Need to keep track of the ELR somehow, maybe by event id. How do we get event Id and then pick the ELR from the patient page with the correct event ID?
#read table from review queue and select first row and event id?
#find Xpath that contains Event ID? Should be able to find index in lab table by event ID then use that index to click on the correct lab
NBS.find_element(By.XPATH,'/html/body/div[2]/form/div/table[2]/tbody/tr/td/table/tbody/tr[1]/td[4]/a').click()
time.sleep(3)

""" Review the Investigations table in the Events tab of a patient profile
to determine if the case already has an existing investigation. """
try:
    investigation_table = NBS.read_investigation_table()
    if type(investigation_table) == pd.core.frame.DataFrame:
        existing_investigations = investigation_table[investigation_table["Condition"].str.contains("Hepatitis")]
        if len(existing_investigations) >= 1:
            NBS.existing_investigation_index = existing_investigations.index.tolist()[0]
            NBS.existing_investigation_index = int(NBS.existing_investigation_index) + 1
            inv_found = True
            if len(existing_investigations.loc[existing_investigations['Case Status'] == 'Not a Case']) > 0:
                existing_not_a_case = True
            else:
                existing_not_a_case = False
        else:
                NBS.existing_investigation_index = None
                inv_found = False
                existing_not_a_case = False
    else:
            inv_found = False
            existing_not_a_case = False
except NoSuchElementException:
    inv_found = False
    existing_not_a_case = False

print(inv_found)
print(existing_not_a_case)

#Navigate to the lab report to be processed using the Event ID from the patient page
lab_report_table_path = '//*[@id="lab1"]'
lab_report_table = NBS.ReadTableToDF(lab_report_table_path)

with pd.option_context('display.max_rows', None,
                       'display.max_columns', None,
                       'display.precision', 3,
                       ):
    print(lab_report_table)

lab_row = lab_report_table[lab_report_table['Event ID'] == event_id]
lab_index = int(lab_row.index.to_list()[0]) + 1

if index > 1:
    lab_path = f'/html/body/div[2]/form/div/table[4]/tbody/tr[2]/td/div[2]/table/tbody/tr/td/div[1]/div[3]/div/table/tbody/tr[2]/td/table/tbody/tr[{str(index)}]/td[1]/a'
elif index == 1:
    lab_path = f'/html/body/div[2]/form/div/table[4]/tbody/tr[2]/td/div[2]/table/tbody/tr/td/div[1]/div[3]/div/table/tbody/tr[2]/td/table/tbody/tr/td[1]/a'
self.find_element(By.XPATH, lab_path).click()
        


