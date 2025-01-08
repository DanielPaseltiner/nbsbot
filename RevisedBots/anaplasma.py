# -*- coding: utf-8 -*-
"""
Created on Wed Apr 17 10:35:46 2024

@author: Jared.Strauch
"""

from anaplasmacasereview_revised import Anaplasmacasereview_revised
from tqdm import tqdm
import time
import traceback
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import ElementNotInteractableException
from selenium.common.exceptions import StaleElementReferenceException
from selenium.common.exceptions import TimeoutException
import pandas as pd
from datetime import datetime
import smtplib
from email.message import EmailMessage

from dotenv import load_dotenv
import os

load_dotenv()

def generator():
    while True:
        yield

reviewed_ids = []
what_do = []

is_in_production = os.getenv('ENVIRONMENT', 'production') != 'development'

print("state", is_in_production)
NBS = Anaplasmacasereview_revised(production=True)
NBS.get_credentials()
NBS.log_in()
NBS.GoToApprovalQueue()

patients_to_skip = []
n = 1
attempt_counter = 0
with open("patients_to_skip.txt", "r") as patient_reader:
    patients_to_skip.append(patient_reader.readlines())

for _ in tqdm(generator()):
    try:
        #Sort review queue so that only Anaplasma investigations are listed
        clear_filter_path = '//*[@id="removeFilters"]/a/font'
        condition_path = '/html/body/div[2]/form/div/table[2]/tbody/tr/td/table/thead/tr/th[8]/img'
        
        #clear all filters
        WebDriverWait(NBS,NBS.wait_before_timeout).until(EC.element_to_be_clickable((By.XPATH, clear_filter_path)))
        NBS.find_element(By.XPATH, clear_filter_path).click()
        time.sleep(5)

        
        #open condition dropdown menu
        WebDriverWait(NBS,NBS.wait_before_timeout).until(EC.presence_of_element_located((By.XPATH, condition_path)))
        WebDriverWait(NBS,NBS.wait_before_timeout).until(EC.element_to_be_clickable((By.XPATH, condition_path)))
        NBS.find_element(By.XPATH, condition_path).click()
        time.sleep(1)

        #clear checkboxes
        WebDriverWait(NBS,NBS.wait_before_timeout).until(EC.element_to_be_clickable((By.XPATH, '/html/body/div[2]/form/div/table[2]/tbody/tr/td/table/thead/tr/th[8]/div/label[2]/input')))
        NBS.find_element(By.XPATH,'/html/body/div[2]/form/div/table[2]/tbody/tr/td/table/thead/tr/th[8]/div/label[2]/input').click()
        time.sleep(1)

        #select all hepatitis tests
        tests = ["Anapla"]
        for test in tests:
            try:
                results = NBS.find_elements(By.XPATH,f"//label[contains(text(),'{test}')]")
                for result in results:
                    result.click()
            except (NoSuchElementException, ElementNotInteractableException) as e:
                pass
        time.sleep(1)

        #click ok
        try:
            WebDriverWait(NBS,NBS.wait_before_timeout).until(EC.element_to_be_clickable((By.XPATH, '/html/body/div[2]/form/div/table[2]/tbody/tr/td/table/thead/tr/th[8]/div/label[1]/input[1]')))
            NBS.find_element(By.XPATH,'/html/body/div[2]/form/div/table[2]/tbody/tr/td/table/thead/tr/th[8]/div/label[1]/input[1]').click()
        except (NoSuchElementException, TimeoutException):
            #click cancel and go back to home page to wait for more ELRs
            WebDriverWait(NBS,NBS.wait_before_timeout).until(EC.element_to_be_clickable((By.XPATH, '/html/body/div[2]/form/div/table[2]/tbody/tr/td/table/thead/tr/th[8]/div/label[1]/input[2]')))
            NBS.find_element(By.XPATH,'/html/body/div[2]/form/div/table[2]/tbody/tr/td/table/thead/tr/th[8]/div/label[1]/input[2]').click()
            #NBS.go_to_home()
            time.sleep(3)
            NBS.Sleep()
            #this wont work if we are not running the for loop to cycle through the queue,
            #comment out if not running the whole thing
            continue
        time.sleep(1)

        #sort chronologically, oldest first
        submit_date_path = '/html/body/div[2]/form/div/table[2]/tbody/tr/td/table/thead/tr/th[3]/a'
        WebDriverWait(NBS,NBS.wait_before_timeout).until(EC.element_to_be_clickable((By.XPATH, submit_date_path)))
        NBS.find_element(By.XPATH, submit_date_path).click()
        WebDriverWait(NBS,NBS.wait_before_timeout).until(EC.element_to_be_clickable((By.XPATH, submit_date_path)))
        NBS.find_element(By.XPATH, submit_date_path).click() #---here

        if NBS.queue_loaded:
            NBS.queue_loaded = None
            continue
        elif NBS.queue_loaded == False:
            NBS.queue_loaded = None
            NBS.SendManualReviewEmail()
            NBS.Sleep()
            continue
        
        NBS.CheckFirstCase()
        if NBS.condition == 'Anaplasma phagocytophilum':
            NBS.GoToNCaseInApprovalQueue(n)
            if NBS.queue_loaded:
                NBS.queue_loaded = None
                continue
            inv_id = NBS.find_element(By.XPATH,'//*[@id="bd"]/table[3]/tbody/tr[2]/td[1]/span[2]').text 
            if any(inv_id in skipped_patients for skipped_patients in patients_to_skip):
                print(f"present, {inv_id}")
                NBS.ReturnApprovalQueue()
                n = n + 1
                continue
            # inv_id = "CASE01dummy_patient"
            # while any(inv_id in skipped_patients for skipped_patients in patients_to_skip):
            #     NBS.GoToNCaseInApprovalQueue(n + 1)
            #     if NBS.queue_loaded:
            #         NBS.queue_loaded = None
            #         continue
            #     inv_id = NBS.find_element(By.XPATH,'//*[@id="bd"]/table[3]/tbody/tr[2]/td[1]/span[2]').text #patient id?

            NBS.Reset()
            NBS.initial_name = NBS.patient_name
            
            NBS.CheckFirstName()
            NBS.CheckLastName()
            NBS.CheckDOB()
            NBS.CheckAge()
            NBS.CheckAgeType()
            NBS.CheckCurrentSex()#removed Ana
            #NBS.CheckStAddr()
            street_address = NBS.CheckForValue( '//*[@id="DEM159"]', 'Street address is blank.')
            if any(x in street_address for x in ["HOMELESS", "NO ADDRESS", "NO FIXED ADDRESS", "UNSHELTERED"]):
                pass
            else:
                NBS.CheckCity()
                NBS.CheckZip()
                NBS.CheckCounty()
                #NBS.CheckCityCountyMatch()
            NBS.CheckState()
            NBS.CheckCountry()
            NBS.CheckPhone()
            NBS.CheckEthnicity()
            NBS.CheckRaceAna()
            NBS.GoToTickBorne()
            NBS.CheckInvestigationStartDate()#removed Ana
            NBS.CheckReportDate()
            NBS.CheckCountyStateReportDate()
            if NBS.county:
                NBS.CheckCounty()                 #new code
            NBS.CheckJurisdiction()              #new code
            NBS.CheckInvestigationStatus()
            NBS.CheckInvestigatorAna()
            NBS.CheckInvestigatorAssignDateAna()
            NBS.CheckMmwrWeek()
            NBS.CheckMmwrYear()
            NBS.CheckReportingSourceType()
            NBS.CheckReportingOrganization()
            NBS.CheckConfirmationDate()
            NBS.CheckAdmissionDate() #new code to get admission date and compare to discharge
            NBS.CheckDischargeDate()                                   #new code, added this from covidcase review. modified method logic
            NBS.CheckIllnessDurationUnits()
            NBS.CheckHospitalization()
            NBS.CheckDeath()                         #removed '77' after parenthesis
            ###Anaplasma Specific Checks###
            NBS.CheckImmunosupressed()
            NBS.CheckLifeThreatening()
            #Check lab name, spelling is wrong but that is how it is defined in the legacy code
            NBS.CheckPreformingLaboratory()
            NBS.CheckTickBite()
            NBS.CheckPhysicianVisit()                                  #new code
            NBS.CheckSerology()
            NBS.CheckOutbreak()
            NBS.CheckSymptoms()#removed Ana
            NBS.CheckIllnessLength()
            NBS.CheckCase()
            # if NBS.CaseStatus == "Not a Case":
            #     continue
            NBS.CheckDetectionMethod() #new code                           #new code reject if not detectionmethod
            NBS.CheckConfirmationMethod() #removed Ana
            if not NBS.issues:
                reviewed_ids.append(inv_id)
                what_do.append("Approve Notification")
                NBS.ApproveNotification()
            NBS.ReturnApprovalQueue()
            if NBS.queue_loaded:
                NBS.queue_loaded = None
                continue
            if len(NBS.issues) > 0:
                #Sort review queue so that only Anaplasma investigations are listed
                clear_filter_path = '//*[@id="removeFilters"]/a/font'
                condition_path = '/html/body/div[2]/form/div/table[2]/tbody/tr/td/table/thead/tr/th[8]/img'
                
                #clear all filters
                WebDriverWait(NBS,NBS.wait_before_timeout).until(EC.element_to_be_clickable((By.XPATH, clear_filter_path)))
                NBS.find_element(By.XPATH, clear_filter_path).click()
                time.sleep(5)

                

                #open condition dropdown menu
                WebDriverWait(NBS,NBS.wait_before_timeout).until(EC.presence_of_element_located((By.XPATH, condition_path)))
                WebDriverWait(NBS,NBS.wait_before_timeout).until(EC.element_to_be_clickable((By.XPATH, condition_path)))
                NBS.find_element(By.XPATH, condition_path).click()
                time.sleep(1)

                #clear checkboxes
                WebDriverWait(NBS,NBS.wait_before_timeout).until(EC.element_to_be_clickable((By.XPATH, '/html/body/div[2]/form/div/table[2]/tbody/tr/td/table/thead/tr/th[8]/div/label[2]/input')))
                NBS.find_element(By.XPATH,'/html/body/div[2]/form/div/table[2]/tbody/tr/td/table/thead/tr/th[8]/div/label[2]/input').click()
                time.sleep(1)

                #select all hepatitis tests
                tests = ["Anapla"]
                for test in tests:
                    try:
                        results = NBS.find_elements(By.XPATH,f"//label[contains(text(),'{test}')]")
                        for result in results:
                            result.click()
                    except (NoSuchElementException, ElementNotInteractableException) as e:
                        pass
                time.sleep(1)

                #click ok
                try:
                    WebDriverWait(NBS,NBS.wait_before_timeout).until(EC.element_to_be_clickable((By.XPATH, '/html/body/div[2]/form/div/table[2]/tbody/tr/td/table/thead/tr/th[8]/div/label[1]/input[1]')))
                    NBS.find_element(By.XPATH,'/html/body/div[2]/form/div/table[2]/tbody/tr/td/table/thead/tr/th[8]/div/label[1]/input[1]').click()
                except (NoSuchElementException, TimeoutException):
                    #click cancel and go back to home page to wait for more ELRs
                    WebDriverWait(NBS,NBS.wait_before_timeout).until(EC.element_to_be_clickable((By.XPATH, '/html/body/div[2]/form/div/table[2]/tbody/tr/td/table/thead/tr/th[8]/div/label[1]/input[2]')))
                    NBS.find_element(By.XPATH,'/html/body/div[2]/form/div/table[2]/tbody/tr/td/table/thead/tr/th[8]/div/label[1]/input[2]').click()
                    #NBS.go_to_home()
                    time.sleep(3)
                    NBS.Sleep()
                    #this wont work if we are not running the for loop to cycle through the queue,
                    #comment out if not running the whole thing
                    continue
                time.sleep(1)

                #sort chronologically, oldest first
                submit_date_path = '/html/body/div[2]/form/div/table[2]/tbody/tr/td/table/thead/tr/th[3]/a'
                WebDriverWait(NBS,NBS.wait_before_timeout).until(EC.element_to_be_clickable((By.XPATH, submit_date_path)))
                NBS.find_element(By.XPATH, submit_date_path).click()
                WebDriverWait(NBS,NBS.wait_before_timeout).until(EC.element_to_be_clickable((By.XPATH, submit_date_path)))
                NBS.find_element(By.XPATH, submit_date_path).click()
                if NBS.queue_loaded:
                    NBS.queue_loaded = None
                    continue
                NBS.CheckFirstCase()

                NBS.final_name = NBS.patient_name
                if NBS.country != 'UNITED STATES' or NBS.CaseStatus == "Not a Case":
                    print("Skipping patient. No action carried out")
                    patients_to_skip.append(inv_id)
                elif NBS.final_name == NBS.initial_name:
                    reviewed_ids.append(inv_id)
                    what_do.append("Reject Notification")
                    
                    NBS.RejectNotification()
                    NBS.ReturnApprovalQueue()
                elif NBS.final_name != NBS.initial_name:
                    print(f"here : {NBS.final_name} {NBS.initial_name}")
                    print('Case at top of queue changed. No action was taken on the reviewed case.')
                    NBS.num_fail += 1
        else:
            if attempt_counter < NBS.num_attempts:
                attempt_counter += 1
            else:
                attempt_counter = 0
                print("No Anaplasma cases in notification queue.")
                NBS.SendManualReviewEmail()
                NBS.Sleep()
    except:
        tb = traceback.format_exc()
        print(tb)
        #NBS.send_smtp_email(NBS.covid_informatics_list, 'ERROR REPORT: NBSbot(Anaplasma Notification Review) AKA Athena', tb, 'error email')
        break

bot_act = pd.DataFrame(
    {'Inv ID': reviewed_ids,
     'Action': what_do
    })
bot_act.to_excel(f"Anaplasma_bot_activity_{datetime.now().date().strftime('%m_%d_%Y')}.xlsx")

body = "The list of Anaplasma Phagocytophilum notifications that need to be manually reviewed are in the attached spreadsheet."
message = EmailMessage()
message.set_content(body)
message['Subject'] = 'Notification Review Report: NBSbot(Anaplasma Notification Review) AKA Anaplasma de Armas'
message['From'] = NBS.nbsbot_email
message['To'] = ', '.join(["disease.reporting@maine.gov"])
with open(f"Anaplasma_bot_activity_{datetime.now().date().strftime('%m_%d_%Y')}.xlsx", "rb") as f:
    message.add_attachment(
        f.read(),
        filename=f"Anaplasma_bot_activity_{datetime.now().date().strftime('%m_%d_%Y')}.xlsx",
        maintype="application",
        subtype="vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
with open("patients_to_skip.txt", "w") as patient_writer:
    for patient_id in patients_to_skip: patient_writer.write(f"{patient_id}\n")

smtpObj = smtplib.SMTP(NBS.smtp_server)
smtpObj.send_message(message)

#NBS.send_smtp_email("disease.reporting@maine.gov", 'Notification Review Report: NBSbot(Anaplasma Notification Review) AKA Anaplasma de Armas', body, 'Anaplasma Notification Review email')
