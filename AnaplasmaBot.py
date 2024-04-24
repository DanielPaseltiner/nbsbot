# -*- coding: utf-8 -*-
"""
Created on Wed Apr 17 10:35:46 2024

@author: Jared.Strauch
"""

from anaplasmacasereview import Anaplasmanotificationreview
from tqdm import tqdm
import time
import traceback

def generator():
    while True:
        yield

NBS = COVIDnotificationreview(production=False)
NBS.get_credentials()
NBS.log_in()
NBS.GoToApprovalQueue()

for _ in tqdm(generator()):
    try:
        #clear all filters
        WebDriverWait(NBS,NBS.wait_before_timeout).until(EC.element_to_be_clickable((By.XPATH, clear_filter_path)))
        NBS.find_element(By.XPATH, clear_filter_path).click()
        time.sleep(5)

        #NBS.find_element(By.XPATH, '//*[@id="myQueues"]/div/div[3]/ul/li[3]/a').click()
        #open description dropdown menu
        WebDriverWait(NBS,NBS.wait_before_timeout).until(EC.presence_of_element_located((By.XPATH, description_path)))
        WebDriverWait(NBS,NBS.wait_before_timeout).until(EC.element_to_be_clickable((By.XPATH, description_path)))
        NBS.find_element(By.XPATH, description_path).click()
        time.sleep(1)

        #clear checkboxes
        WebDriverWait(NBS,NBS.wait_before_timeout).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="parent"]/thead/tr/th[6]/div/label[2]/input')))
        NBS.find_element(By.XPATH,'//*[@id="parent"]/thead/tr/th[6]/div/label[2]/input').click()
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
            WebDriverWait(NBS,NBS.wait_before_timeout).until(EC.element_to_be_clickable((By.XPATH, '/html/body/div[2]/form/div/table[2]/tbody/tr/td/table/thead/tr/th[6]/div/label[1]/input[1]')))
            NBS.find_element(By.XPATH,'/html/body/div[2]/form/div/table[2]/tbody/tr/td/table/thead/tr/th[6]/div/label[1]/input[1]').click()
        except NoSuchElementException:
            #click cancel and go back to home page to wait for more ELRs
            WebDriverWait(NBS,NBS.wait_before_timeout).until(EC.element_to_be_clickable((By.XPATH, '/html/body/div[2]/form/div/table[2]/tbody/tr/td/table/thead/tr/th[6]/div/label[1]/input[2]')))
            NBS.find_element(By.XPATH,'/html/body/div[2]/form/div/table[2]/tbody/tr/td/table/thead/tr/th[6]/div/label[1]/input[2]').click()
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



            NBS.CheckFirstName()
            NBS.CheckLastName()
            NBS.CheckDOB()
            NBS.CheckAge()
            NBS.CheckAgeType()
            NBS.CheckCurrentSex()
            NBS.CheckStAddr()
            NBS.CheckCity()
            NBS.CheckState()
            NBS.CheckZip()
            NBS.CheckCounty()
            NBS.CheckCountry()
            NBS.CheckPhone()
            NBS.CheckEthnicity()
            NBS.CheckRace()
            NBS.CheckReportDate()
            NBS.CheckCountyStateReportDate()
            NBS.CheckJurisdiction()
            NBS.CheckInvestigationStartDate()
            NBS.CheckInvestigationStatus()
            NBS.CheckInvestigator()
            NBS.CheckInvestigatorAssignDate()
            NBS.CheckMmwrWeek()
            NBS.CheckMmwrYear()
            NBS.CheckReportingSourceType()
            NBS.CheckReportingOrganization()
            NBS.CheckConfirmationDate()
            NBS.CheckIllnessDurationUnits()
            NBS.CheckDeath()
            NBS.CheckHospitalization()
            NBS.read_city()
            NBS.county_lookup(NBS.city, 'Maine')
            
            ###Anaplasma Specific Checks###
            #Check immunosuppressive or life threatening condition
            NBS.CheckImmunosupressed()
            NBS.CheckLifeThreatening()
            #Check lab name
            NBS.CheckPerformingLaboratory()
            
            #check history of tick bite
            NBS.CheckTickBite()
            #check clinically compatible
            #symptom onset
            #travel info
            #titer value
            #outbreak
            NBS.CheckOutbreak()