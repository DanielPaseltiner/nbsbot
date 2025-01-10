# -*- coding: utf-8 -*-
"""
Created on Wed Apr 17 10:35:46 2024

@author: Jared.Strauch
"""

from anaplasmacasereview import Anaplasmacasereview
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


def generator():
    while True:
        yield

NBS = Anaplasmacasereview(production=True)
NBS.get_credentials()
NBS.log_in()
NBS.GoToApprovalQueue()


attempt_counter = 0
for _ in tqdm(generator()):
    try:
        #Sort review queue so that only hepatitis cases are listed
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
            WebDriverWait(NBS,NBS.wait_before_timeout).until(EC.element_to_be_clickable((By.XPATH, '/html/body/div[2]/form/div/table[2]/tbody/tr/td/table/thead/tr/th[8]/div/label[8]/input[1]')))
            NBS.find_element(By.XPATH,'/html/body/div[2]/form/div/table[2]/tbody/tr/td/table/thead/tr/th[8]/div/label[8]/input[1]').click()
        except (NoSuchElementException, TimeoutException):
            #click cancel and go back to home page to wait for more ELRs
            WebDriverWait(NBS,NBS.wait_before_timeout).until(EC.element_to_be_clickable((By.XPATH, '/html/body/div[2]/form/div/table[2]/tbody/tr/td/table/thead/tr/th[8]/div/label[7]/input[2]')))
            NBS.find_element(By.XPATH,'/html/body/div[2]/form/div/table[2]/tbody/tr/td/table/thead/tr/th[8]/div/label[7]/input[2]').click()
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
        elif NBS.queue_loaded == False:
            NBS.queue_loaded = None
            NBS.SendManualReviewEmail()
            NBS.Sleep()
            continue

        NBS.CheckFirstCase()
        NBS.initial_name = NBS.patient_name
        if NBS.condition == 'Anaplasmosis':
            NBS.GoToFirstCaseInApprovalQueue()
            if NBS.queue_loaded:
                NBS.queue_loaded = None
                continue
            NBS.Reset()


            NBS.CheckFirstName()
            NBS.CheckLastName()
            NBS.CheckDOB()
            NBS.CheckAge()
            NBS.CheckAgeType()
            NBS.CheckCurrentSex()
            #NBS.CheckStAddr()
            street_address = NBS.CheckForValue( '//*[@id="DEM159"]', 'Street address is blank.')
            if any(x in street_address for x in ["HOMELESS", "NO ADDRESS", "NO FIXED ADDRESS", "UNSHELTERED"]):
                pass
            else:
                NBS.CheckCity()
                NBS.CheckZip()
                NBS.CheckCounty()
                NBS.CheckCityCountyMatch()
            NBS.CheckState()
            NBS.CheckCountry()
            NBS.CheckPhone()
            NBS.CheckEthnicity()
            NBS.CheckRaceAna()
            NBS.GoToTickBorne()
            NBS.CheckInvestigationStartDate()
            NBS.CheckReportDate()
            NBS.CheckCountyStateReportDate()
            if NBS.county:
                NBS.CheckJurisdiction()
            else:
                pass
            NBS.CheckInvestigationStatus()
            NBS.CheckInvestigator()
            NBS.CheckInvestigatorAssignDateAna()
            NBS.CheckMmwrWeek()
            NBS.CheckMmwrYear()
            NBS.CheckReportingSourceType()
            NBS.CheckReportingOrganization()
            NBS.CheckConfirmationDate()
            NBS.CheckIllnessDurationUnits()
            NBS.CheckDeath()
            NBS.CheckHospitalization()
            #do we need to check lab name in lab section?

            ###Anaplasma Specific Checks###
            NBS.CheckImmunosupressed()
            NBS.CheckLifeThreatening()
            #Check lab name, spelling is wrong but that is how it is defined in the legacy code
            NBS.CheckPreformingLaboratory()
            NBS.CheckTickBite()
            #titer value
            NBS.CheckSerology()
            NBS.CheckIllnessLength()
            NBS.CheckOutbreak()
            NBS.CheckSymptoms()
            NBS.CheckCase() #We need to figure out what to do with suspect cases
            if not NBS.issues:
                NBS.ApproveNotification()
            NBS.ReturnApprovalQueue()
            if NBS.queue_loaded:
                NBS.queue_loaded = None
                continue
            if len(NBS.issues) > 0:
                #Sort review queue so that only hepatitis cases are listed
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
                    WebDriverWait(NBS,NBS.wait_before_timeout).until(EC.element_to_be_clickable((By.XPATH, '/html/body/div[2]/form/div/table[2]/tbody/tr/td/table/thead/tr/th[8]/div/label[8]/input[1]')))
                    NBS.find_element(By.XPATH,'/html/body/div[2]/form/div/table[2]/tbody/tr/td/table/thead/tr/th[8]/div/label[8]/input[1]').click()
                except NoSuchElementException:
                    #click cancel and go back to home page to wait for more ELRs
                    WebDriverWait(NBS,NBS.wait_before_timeout).until(EC.element_to_be_clickable((By.XPATH, '/html/body/div[2]/form/div/table[2]/tbody/tr/td/table/thead/tr/th[8]/div/label[8]/input[2]')))
                    NBS.find_element(By.XPATH,'/html/body/div[2]/form/div/table[2]/tbody/tr/td/table/thead/tr/th[8]/div/label[8]/input[2]').click()
                    NBS.go_to_home()
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
                if NBS.final_name == NBS.initial_name:
                    #NBS.RejectNotification()
                    NBS.ReturnApprovalQueue()
                elif NBS.final_name != NBS.initial_name:
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
