# -*- coding: utf-8 -*-
"""
Created on Wed Apr 17 10:50:29 2024

@author: Jared.Strauch
"""

from base import NBSdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime
from fractions import Fraction
import re
from dateutil.relativedelta import relativedelta
from geopy.geocoders import Nominatim
import pandas as pd
from io import StringIO
from bs4 import BeautifulSoup
import smtplib
from email.message import EmailMessage



class Giardia(NBSdriver):
    """ A class inherits all basic NBS functionality from NBSdriver and adds
    methods for reviewing COVID case investigations for data accuracy and completeness. """
    def __init__(self, production=False):
        super().__init__(production)
        self.num_approved = 0
        self.num_rejected = 0
        self.num_fail = 0

    def StandardChecks(self):
        self.Reset()
        self.initial_name = self.patient_name
        
        self.CheckFirstName()
        self.CheckLastName()
        self.CheckDOB()
        self.CheckAge()
        self.CheckAgeType()
        self.CheckCurrentSex()#removed Ana
        self.CheckMortality()
        #self.CheckStAddr()
        street_address = self.ReadText( '//*[@id="DEM159"]') #, 'Street address is blank.'
        if any(x in street_address for x in ["HOMELESS", "NO ADDRESS", "NO FIXED ADDRESS", "UNSHELTERED"]):
            pass
        else: 
            self.CheckCity()
            self.CheckZip()
            self.CheckCounty()
            
        self.CheckState()
        self.CheckCountry()
        self.CheckPhone()
        self.GoToGiardiasis()
        self.CheckCaseStatus()
        self.CheckLabTestResult()
        if self.case_status == "Confirmed":
            self.CheckLabName()
            self.CheckLabTestType()
            
            self.CheckSpecimenSource()
            self.CheckDateSpecimenCollected()

        self.CheckIllnessOnset()
        self.CheckAgeData()
        self.CheckWasSymptomatic()
        self.CheckHospitalization()   
        self.CheckDeath()
        self.CheckPregnancyStatus()
        self.CheckPatientTreated()
        self.CheckImmuneCompromised()  
        self.CheckCoInfection()
        self.CheckDiseaseAcquired()
        self.CheckTransmissionMode()
        self.CheckDetectionMethod()
        self.CheckConfirmationMethod() 
        self.VerifyCaseStatus()
        self.CheckDateClosed()

    ####################### Patient Demographics Check Methods ############################
    def CheckAge(self):
        """ Must provide age. """
        self.age = self.ReadText('//*[@id="INV2001"]')
        if not self.age:
            self.issues.append('Age is blank.')
            print(f"age: {self.age}")
        
    def CheckAgeType(self):
        """ Must age type must be one of Days, Months, Years. """
        self.age_type = self.ReadText('//*[@id="INV2002"]')
        if not self.age_type:
            self.issues.append('Age Type is blank.')
            print(f"age_type: {self.age_type}")
        elif self.age_type != "Days" and self.age_type != "Months" and self.age_type != "Years":
            self.issues.append('Age Type is not one of Days, Months, or Years.')
            print(f"age_type: {self.age_type}")
        
    
    def CheckPhone(self):
        """ If a phone number is provided make sure it is ten digits. """
        home_phone = self.ReadText('//*[@id="DEM177"]')
        work_phone = self.ReadText('//*[@id="NBS002"]')
        cell_phone = self.ReadText('//*[@id="NBS006"]')
        if home_phone:
            #check if phone is ten digits if it exists
            if len(re.findall(r'\d', str(home_phone))) != 10:
                self.issues.append('Phone number is not ten digits.')
                print(f"home_phone: {home_phone}")
        elif work_phone:
            #check if phone is ten digits if it exists
            if len(re.findall(r'\d', str(work_phone))) != 10:
                self.issues.append('Phone number is not ten digits.')
                print(f"work_phone: {work_phone}")
        elif cell_phone:
            #check if phone is ten digits if it exists
            if len(re.findall(r'\d', str(cell_phone))) != 10:
                self.issues.append('Phone number is not ten digits.')
                print(f"cell_phone: {cell_phone}")

    def CheckCurrentSex(self):
        """ Ensure patient current sex is not blank. """
        self.patient_sex = self.ReadText('//*[@id="DEM113"]')
        if not self.patient_sex:
            self.issues.append('Patient sex is blank.')
        elif self.patient_sex == "Unknown":
            comment = self.ReadText('//*[@id="DEM196"]')
            if not comment:
                self.issues.append('Patient sex is Unknown without a note.')

    def CheckMortality(self):
        mortality_as_of_date = self.CheckForValue('//*[@id="NBS097"]', "Mortality fields on patient page should not be blank")
        is_deceased = self.CheckForValue('//*[@id="DEM127"]', "Mortality fields on patient page should not be blank")
        
    ####################### Navigation Methods ############################
    def GoToGiardiasis(self):
        giardiasis_path = '//*[@id="tabs0head1"]'
        WebDriverWait(self,self.wait_before_timeout).until(EC.element_to_be_clickable((By.XPATH, giardiasis_path)))
        self.find_element(By.XPATH, giardiasis_path).click()
    
    ####################### Patient Status Check Methods ############################
    def CheckDeath(self):
        """If died from illness is yes or no, need a death date """
        self.death_indicator =  self.ReadText('//*[@id="INV145"]') #,'Died from illness must be yes or no.'
        print(f"death: {self.death_indicator}")
        # if self.death_indicator in ['Yes', 'No'] and not self.discharge_date:
        #     self.issues.append('Death indicator should be unknown if no discharge date.')
        if self.death_indicator == "Yes":
            """ Death date must be present."""
            death_date = self.ReadDate('//*[@id="INV146"]')
            if not death_date:
                self.issues.append('Date of death is blank.')
                print(f"death: {self.death_indicator}")
            elif death_date > self.now:
                self.issues.append('Date of death date cannot be in the future.')
                print(f"death: {self.death_indicator}")
        elif self.death_indicator not in ['Yes', 'No', 'Unknown']:
            self.issues.append('Death indicator cannot be blank')
            print(f"death: {self.death_indicator}")

    def CheckHospitalization(self):
        """ Read hospitalization status. If yes need date and hospital """
        self.hospitalization_indicator = self.ReadText('//*[@id="INV128"]')
        if self.hospitalization_indicator == "Yes":
            hospital_name = self.ReadText('//*[@id="INV184"]')
            if not hospital_name:
                self.issues.append('Hospital name missing.')
                print(f"hospitalization, hospital_name: {hospital_name}")
            self.admission_date = self.ReadDate('//*[@id="INV132"]')
            if not self.admission_date:
                self.issues.append('Admission date is missing.')
                print(f"hospitalization, admission_date: {self.admission_date}")
            self.discharge_date = self.ReadDate('//*[@id="INV133"]')
            if not self.discharge_date:                                                         #commented out
                self.issues.append('Missing discharge date.')
                print(f"discharge_date: {self.discharge_date}")
            self.duration_in_hospital = self.ReadText('//*[@id="INV134"]')
            if not self.duration_in_hospital:
                self.issues.append('Missing Total duration in hospital.')
                print(f"duration in hospital: {self.duration_in_hospital}")
            # if self.admission_date and self.admission_date > self.now:
            #     self.issues.append('Admission date cannot be in the future.')
            #     print(f"hospitalization, admission_date: {self.admission_date}")

        elif self.hospitalization_indicator not in ['Yes', 'No']: 
            self.issues.append("Patient hospitalization status should not be blank.")
            
    
    def CheckPregnancyStatus(self):
        """ Check that pregnancy status isn't blank."""
        pregnant_status = self.ReadText('//*[@id="INV178"]')
        if pregnant_status not in ['Yes', 'No', 'Unknown'] and self.patient_sex != "Male":
            self.issues.append('Pregnant status is blank.')

    def CheckImmuneCompromised(self):
        """ If patient is immune compromised, need condition info """
        self.Immune_compromised = self.CheckForValue('//*[@id="ME3129"]', 'Immuno compressed cannot be blank.')
    
    def CheckCoInfection(self):
        """ Check that pregnancy status isn't blank."""
        co_infection = self.CheckForValue('//*[@id="ME11173"]', 'Co infection cannot be blank.')
    
    def CheckDiseaseAcquired(self):
        """ Check that pregnancy status isn't blank."""
        disease_acquired = self.CheckForValue('//*[@id="INV152"]', "Where was Disease Acquired cannot be blank.")
    
    def CheckTransmissionMode(self):
        """ Check that pregnancy status isn't blank."""
        transmission_mode = self.CheckForValue('//*[@id="INV157"]', "Transmission mode cannot be blank.")

    def CheckDateClosed(self):
        date_closed = self.CheckForValue('//*[@id="ME11163"]', "Date closed should not be blank")

    def CheckPatientTreated(self):
        patient_treated = self.CheckForValue('//*[@id="ME8171"]', 'Patient treated cannot be blank.')

    def CheckCaseStatus(self):
        self.case_status = self.ReadText('//*[@id="INV163"]')

    def VerifyCaseStatus(self):
        confirmed = self.laboratory_test_result == "Positive" and self.symptomatic == "Yes"
        probable = self.symptomatic == "Yes" and self.confirmation_method == "Epidemiologically linked"
        if confirmed:
            if self.case_status != "Confirmed":
                self.issues.append("Meets case definition for a confirmed case but isn't a confirmed case")
        elif probable:
            if self.case_status != "Probable":
                self.issues.append("Meets case definition for a probable case but isn't a probable case")
        elif confirmed is False and probable is False and self.CaseStatus != "Not a Case":
            self.issues.append("Meets case definition for Not a Case case but isn't Not a Case")
    
    """
        checks for confirmed case status
    """

    def CheckLabName(self):
        """ Check for follow-up tests """
        self.laboratory_name = self.ReadText('//*[@id="ME6105"]')
        if not self.laboratory_name:
            self.issues.append("laboratory name cannot be blank when Case status is confirmed.")
        print(f"laboratory name: {self.laboratory_name}")
    
    def CheckLabTestType(self):
        """ Check for follow-up tests """
        self.laboratory_test_type = self.ReadText('//*[@id="ME15109"]')
        if not self.laboratory_test_type:
            self.issues.append("laboratory test type cannot be blank when Case status is confirmed.")
        print(f"laboratory test type: {self.laboratory_test_type}")

    def CheckLabTestResult(self):
        """ Check for follow-up tests """
        self.laboratory_test_result = self.ReadText('//*[@id="ME15110"]')
        if self.laboratory_test_result != "Positive" and self.CaseStatus == 'Confirmed':
            self.issues.append("laboratory test result must be positive.")
        print(f"laboratory test result: {self.laboratory_test_result}")

    def CheckSpecimenSource(self):
        """ Check for follow-up tests """
        specimen_source = self.ReadText('//*[@id="ME11165"]')
        if not specimen_source:
            self.issues.append("specimen source cannot be blank when Case status is confirmed.")
        print(f"specimen source: {specimen_source}")
        
    def CheckDateSpecimenCollected(self):
        """ Check for follow-up tests """
        date_specimen_collected = self.ReadText('//*[@id="ME8117"]')
        if not date_specimen_collected:
            self.issues.append("date specimen collected cannot be blank when Case status is confirmed.")
        print(f"date specimen collected: {date_specimen_collected}")

    """
    end
    """
    
    def CheckDiagnosisDate(self):
        diagnosis_date = self.CheckForValue('//*[@id="INV136"]', 'Diagnosis date cannot be blank.')
        if diagnosis_date and diagnosis_date != self.collection_date:
            self.issues.append('Diagnosis date should be same as collection date.')

            
    def CheckIllnessOnset(self):
        """ Check if a patient has an illness onset date. """
        self.IllnessOnset = self.ReadDate('//*[@id="INV137"]')
        self.IllnessEnd = self.ReadDate('//*[@id="INV138"]')
        print(f"Illness_length: {self.IllnessOnset}")
        if self.IllnessOnset and self.IllnessEnd  and self.IllnessEnd < self.IllnessOnset:
            self.issues.append('Illness end date cannot precede illness onset date.')
            print(f"Illness_length: {self.IllnessOnset}")

        if not self.IllnessOnset:
            self.issues.append('“Illness onset date” should not be blank.')
            print(f"Illness_onset: {self.IllnessOnset}")

    def CheckAgeData(self):
        """ Check for follow-up tests """
        self.age_at_onset = self.CheckForValue('//*[@id="INV143"]', 'Age at onset cannot be blank')
        print(f"age at onset: {self.age_at_onset}")
        self.age_at_onset_units = self.CheckForValue('//*[@id="INV144"]', 'Age at onset units cannot be blank')
        print(f"age at onset units: {self.age_at_onset}")
        

    def CheckWasSymptomatic(self):
        """ Check for follow-up tests """
        self.symptomatic = self.CheckForValue('//*[@id="ME12174"]', 'Symptomatic cannot be blank')
        print(f"was symptomatic: {self.symptomatic}")

    def RejectNotification(self):
        """ Reject notification on first case in notification queue.
        To be used when issues were encountered during review of the case."""
        reject_path = '//*[@id="parent"]/tbody/tr[1]/td[2]/img'
        main_window_handle = self.current_window_handle
        WebDriverWait(self,self.wait_before_timeout).until(EC.element_to_be_clickable((By.XPATH, reject_path)))
        self.find_element(By.XPATH,reject_path).click()
        rejection_comment_window = None
        for handle in self.window_handles:
            if handle != main_window_handle:
                rejection_comment_window = handle
                break
        if rejection_comment_window:
            self.switch_to.window(rejection_comment_window)
            timestamp = datetime.now().strftime("%m/%d/%Y, %H:%M:%S")
            self.issues.append('-nbsbot ' + timestamp)
            self.find_element(By.XPATH,'//*[@id="rejectComments"]').send_keys(' '.join(self.issues))
            self.find_element(By.XPATH,'/html/body/form/table/tbody/tr[3]/td/input[1]').click()
            self.switch_to.window(main_window_handle)
            self.num_rejected += 1
    def ApproveNotification(self):
        """ Approve notification on first case in notification queue. """
        main_window_handle = self.current_window_handle
        self.find_element(By.XPATH,'//*[@id="createNoti"]').click()
        for handle in self.window_handles:
            if handle != main_window_handle:
                approval_comment_window = handle
                break
        self.switch_to.window(approval_comment_window)
        self.find_element(By.XPATH,'//*[@id="botcreatenotId"]/input[1]').click()
        self.switch_to.window(main_window_handle)
        self.num_approved += 1
    
    def SendAnaplasmaEmail(self, body, inv_id):
        message = EmailMessage()
        message.set_content(body)
        message['Subject'] = f'AnA Bot {inv_id}'
        message['From'] = self.nbsbot_email
        message['To'] = ', '.join(["disease.reporting@maine.gov"])
        smtpObj = smtplib.SMTP(self.smtp_server)
        smtpObj.send_message(message)
        print('sent email', inv_id)