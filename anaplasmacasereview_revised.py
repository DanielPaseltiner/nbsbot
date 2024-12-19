# -*- coding: utf-8 -*-
"""
Created on Wed Apr 17 10:50:29 2024

@author: Jared.Strauch
"""

from covidcasereview_revised import COVIDcasereview_revised
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



class Anaplasmacasereview_revised(COVIDcasereview_revised):
    """ A class inherits all basic NBS functionality from NBSdriver and adds
    methods for reviewing COVID case investigations for data accuracy and completeness. """
    def __init__(self, production=False):
        super(COVIDcasereview_revised, self).__init__(production)
        self.num_approved = 0
        self.num_rejected = 0
        self.num_fail = 0
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
        
    def CheckRaceAna(self):
        """ Must provide race and selection must make sense. """
        self.race = self.CheckForValue('//*[@id="patientRacesViewContainer"]','Race is blank.')
        #If white is selected, other should not be selected
        if "White" in self.race and "Unknown" in self.race:
            self.issues.append("White and Unknown race should not be selected at the same time.")
            print(f"race: {self.race}")
        definitive_races = ['White', 'Black or African American', 'Asian', 'American Indian or Alaska Native', 'Native Hawaiian or Other Pacific Islander']  #New code
        if any(race in self.race for race in definitive_races) and 'Other' in self.race:                                                  #New code
            self.issues.append('Case rejected: Definitive race and Other race should not be selected together.')                            #New code
            print(f"race: {self.race}")
        if "Other" in self.race:
            self.CheckForValue('//*[@id="DEM196"]', "If Other race is selected there needs to be a comment.")
        # Race should only be unknown if no other options are selected.
        ambiguous_answers = ['Unknown', 'Other', 'Refused to answer', 'Not Asked']
        for answer in ambiguous_answers:
            if (answer in self.race) and (self.race != answer) and (self.race == 'Native Hawaiian or Other Pacific Islander'):
                self.issues.append('"'+ answer + '"' + ' selected in addition to other options for race.')
                print(f"race: {self.race}")
    
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
        
    def read_city(self):
        """Read the current city/town."""
        self.city_path = '//*[@id="DEM161"]'
        self.city = self.find_element(By.XPATH, self.city_path).text
        
    def CheckCityCountyMatch(self):
        """Look up the county using the city and check to see if matches the listed county. """
        self.read_city()
        if self.county_lookup(self.city, 'Maine') != '':
            if (self.county_lookup(self.city, 'Maine') + " County") != self.county:
                self.issues.append('City and County do not match.')

    def CheckCurrentSex(self):
        """ Ensure patient current sex is not blank. """
        patient_sex = self.ReadText('//*[@id="DEM113"]')
        if not patient_sex:
            self.issues.append('Patient sex is blank.')
        elif patient_sex == "Unknown":
            comment = self.ReadText('//*[@id="DEM196"]')
            if not comment:
                self.issues.append('Patient sex is Unknown without a note.')
        
    ####################### Investigator Check Methods ############################
    def GoToTickBorne(self):
        Tickborne_path = '//*[@id="tabs0head1"]'
        WebDriverWait(self,self.wait_before_timeout).until(EC.element_to_be_clickable((By.XPATH, Tickborne_path)))
        self.find_element(By.XPATH, Tickborne_path).click()
    
    #Needs to be around lab date, can be after if immediately notifiable
    def CheckInvestigationStartDate(self):
        """ Verify investigation start date is on or after report date. """
        self.investigation_start_date = self.ReadDate('//*[@id="INV147"]')
        self.report_date = self.ReadDate('//*[@id="INV111"]')
        if not self.investigation_start_date:
            self.issues.append('Investigation start date is blank.')
            print(f"investigation_start_date: {self.investigation_start_date}")
        elif self.investigation_start_date < (self.report_date - relativedelta(weeks=1)):
            self.issues.append('Investigation start date must be within one week before report date or after report date.')
            print(f"investigation_start_date: {self.investigation_start_date}")
        elif self.investigation_start_date > self.now:
            self.issues.append('Investigation start date cannot be in the future.')
            print(f"investigation_start_date: {self.investigation_start_date}")

    def CheckInvestigatorAna(self):
        """ Check if an investigator was assigned to the case. """
        investigator = self.ReadText('//*[@id="INV180"]')
        self.investigator_name = investigator
        if not investigator:
            self.issues.append('Investigator is blank.')
            print(f"investigator: {investigator}")
            

    def CheckInvestigatorAssignDateAna(self):
        """ If an investigator was assigned then there should be an investigator
        assigned date. """
        if self.investigator_name:
            self.assigned_date = self.ReadDate('//*[@id="INV110"]')
            if not self.assigned_date:
                self.issues.append('Missing investigator assigned date.')
                print(f"investigator_assigned_date: {self.assigned_date}")
            elif self.assigned_date and self.investigation_start_date:
                if self.assigned_date < self.investigation_start_date:
                    self.issues.append('Investigator assigned date is before investigation start date.')
                    print(f"investigator_assigned_date: {self.assigned_date}")
    
    ####################### Patient Status Check Methods ############################
    def CheckDeath(self):
        """If died from illness is yes or no, need a death date """
        self.death_indicator =  self.CheckForValue('//*[@id="INV145"]','Died from illness must be yes or no.')
        if self.death_indicator == "Yes":
            """ Death date must be present."""
            death_date = self.ReadDate('//*[@id="INV146"]')
            if not death_date:
                self.issues.append('Date of death is blank.')
                print(f"death: {self.death_indicator}")
            elif death_date > self.now:
                self.issues.append('Date of death date cannot be in the future')
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
            elif self.admission_date > self.now:
                self.issues.append('Admission date cannot be in the future.')
                print(f"hospitalization, admission_date: {self.admission_date}")
        elif self.hospitalization_indicator != "Yes":                     #new code
            self.issues.append('Hospitalization status not indicated')    #new code
            print(f"hospitalization: {self.hospitalization_indicator}")
    def CheckIllnessDurationUnits(self):
        """ Read Illness duration units, should be either Day, Month, or Year """
        self.IllnessDurationUnits = self.ReadText('//*[@id="INV140"]')
        if self.IllnessDurationUnits != "":
            if self.IllnessDurationUnits != "Day" and self.IllnessDurationUnits != "Month" and self.IllnessDurationUnits != "Year":
                self.issues.append('Illness Duration is not in Days, Months, or Years.')
                print(f"illness_duration_units: {self.IllnessDurationUnits}")
    
    ################# Anaplasma Specific Check Methods ###############################
    def CheckTickBite(self):
        """ If Tick bite is yes, need details """
        self.TickBiteIndicator = self.ReadText('//*[@id="ME23117"]')
        #if not self.TickBiteIndicator:                                           #code commented. not necessary to have tickbite history
            #self.issues.append('Missing tick bite history.')                    #code commented. not necessary
        if self.TickBiteIndicator == "Yes":
            self.TickBiteNote = self.ReadText('//*[@id="ME23119"]')
            if not self.TickBiteNote:
                self.issues.append('History of tick bite, but no details.')
                print(f"tick_bite: {self.TickBiteIndicator}")
    def CheckOutbreak(self):
        """ Outbreak should not be yes """
        self.OutbreakIndicator = self.ReadText('//*[@id="INV150"]')
        if self.OutbreakIndicator == "Yes":
            self.issues.append('Outbreak should not be yes.')
            print(f"out_break: {self.OutbreakIndicator}")
    def CheckImmunosupressed(self):
        """ If patient is immunosupressed, need condition info """
        self.ImmunosupressedIndicator = self.ReadText('//*[@id="ME24123"]')
        if self.ImmunosupressedIndicator == "Yes":
            self.ImmunosupressedNote = self.ReadText('//*[@id="ME15113"]')
            if not self.ImmunosupressedNote:
                self.issues.append('Patient is immunosurpressed, but the condition is not listed.')
                print(f"Immunosuppressed: {self.ImmunosupressedIndicator}")
    def CheckLifeThreatening(self):
        """ If patient has a life threatening condition, need condition info """
        self.LifeThreateningIndicator = self.ReadText('//*[@id="ME24117"]')
        if self.LifeThreateningIndicator == "Other":
            self.LifeThreateningNote = self.ReadText('//*[@id="ME24124"]')
            if not self.LifeThreateningNote:
                self.issues.append('Patient has other life-threatening condition, but the condition is not listed.')
                print(f"life_threatening: {self.LifeThreateningIndicator}")
    def CheckPhysicianVisit(self):                                                                                   #new method defined here. -JH
        """If patient saw physician, but there is no visit date, then reject case"""
        saw_physician = self.ReadText('//*[@id="ME8169"]')
        physician_visit_date = self.ReadDate('//*[@id="ME12169"]')
        if saw_physician == 'No':
            if not physician_visit_date:
                self.issues.append("Case rejected: No physician visit date documented")
                print(f"physician_visit_date: {physician_visit_date}")
        else:
            if not physician_visit_date:
                self.issues.append("Case rejected: Physician visit date is missing despite seeing physician")
                print(f"physician_visit_date: {physician_visit_date}")
                
                
    def CheckSerology(self):
        """ If patient has reported positive serology the serology section needs to be filled out. """
        #Serology info is only displayed if you click on the button next to the lab report. There could be more than one.
        html = self.find_element(By.XPATH, '//*[@id="ME24112"]/tbody/tr[1]/td/table/tbody/tr/td[2]/table').get_attribute('outerHTML')
        soup = BeautifulSoup(html, 'html.parser')
        self.Sero_table = pd.read_html(StringIO(str(soup)))[0]
        if len(self.Sero_table) > 0:
            if any(pd.isnull(self.Sero_table["Serology Collection Date"].values)):
                self.issues.append('Patient has a reported serology test, but the collection date is not listed.')
                print(f"serology_collection_date]: {self.Sero_table["Serology Collection Date"].values}")
            if any(pd.isnull(self.Sero_table["Serology Test Type"].values)):
                self.issues.append('Patient has a reported serology test, but the test type is not listed.')
                print(f"serology_test_type: {self.Sero_table["Serology Test Type"].values}")
            if any(pd.isnull(self.Sero_table["Serology Positive?"].values)):
                self.issues.append('Patient has a reported serology test, but the result is not listed.')
                print(f"serology_positive: {self.Sero_table["Serology Positive?"].values}")
    def CheckClinicallyCompatible(self):
        """ Check if a patient is clinically compatible and make sure they have the correct case status. """
        self.ClinicCompIndicator = self.ReadText('//*[@id="ME12174"]')
        self.ConfirmationMethod = self.ReadText('//*[@id="INV161"]')
        self.CaseStatus = self.ReadText('//*[@id="INV163"]')
        if self.CaseStatus == "Confirmed" and (self.ClinicCompIndicator != "Yes" or self.ConfirmationMethod != "Laboratory confirmed"):
            self.issues.append('Patient has a confirmed case status, but is not clinically compatible or does not have a confirmatory lab.')
        elif self.CaseStatus == "Probable" and (self.ClinicCompIndicator != "Yes" or self.ConfirmationMethod != "Laboratory report"):
            self.issues.append('Patient has a probable case status, but is not clinically compatible or does not only have a serology lab.')
        elif self.CaseStatus == "Suspect" and self.ClinicCompIndicator != "Unknown":
            self.issues.append('Patient has a suspected case status, but does not have unknown clinically compatiblity.')
        elif self.isnull(self.ConfirmationMethod) or self.isnull(self.CheckDetectionMethod):                         #new code, but may not need since function defined in covidcasereview
            self.issues.append('Confirmation Method is Missing')                                                     #new code
            
    def CheckIllnessLength(self):
        """ Check if a patient has an illness onset date. """
        self.IllnessOnset = self.ReadText('//*[@id="INV137"]')
        if not self.IllnessOnset:
            self.issues.append('Patient is missing illness onset date.')
            print(f"Illness_length: {self.IllnessOnset}")
        
    def CheckSymptoms(self):
        """ Check patient symptoms, Patient needs one if they have a DNA test or two if there have an antibody test. """
        self.ClinicCompIndicator = self.ReadText('//*[@id="ME12174"]')
        if self.ClinicCompIndicator == 'Unknown':                                                                       #new code, this exits early without performing symptom checks if the indicator is unknown
            return                                                                                                      #new code
        self.Fever = self.CheckForValue('//*[@id="ME14101"]','Fever should not be left blank.')
        #self.Rash = self.ReadText('//*[@id="ME23100"]')
        self.Headache = self.CheckForValue('//*[@id="ME23101"]','Headache should not be left blank.')
        self.Myalgia = self.CheckForValue('//*[@id="ME23102"]','Myalgia should not be left blank.')
        self.Anemia = self.CheckForValue('//*[@id="ME24118"]','Anemia should not be left blank.')
        self.Leukopenia = self.CheckForValue('//*[@id="ME24119"]','Leukopenia should not be left blank.')
        self.Thrombocytopenia = self.CheckForValue('//*[@id="ME24120"]','Thrombocytopenia should not be left blank.')
        self.ElevatedHepaticTransaminase =  self.CheckForValue('//*[@id="ME24121"]','Elevated Heaptic Transaminases should not be left blank.')
        #self.Eschar = self.CheckForValue('//*[@id="ME24125"]','Eschar should not be left blank.')
        self.Chills =  self.CheckForValue('//*[@id="ME24126"]','Sweats/Chills should not be left blank.')
        #self.Sweats = self.ReadText('//*[@id="ME24127"]')
        self.FatigueMalaise = self.CheckForValue('//*[@id="ME18116"]','Fatigue/Malaise should not be left blank.')
        #self.ElevatedCRP = self.CheckForValue('//*[@id="NBS729"]','CRP Interpretation should not be left blank.')
        self.ElevatedCRP = self.ReadText('//*[@id="NBS729"]')
        self.symptoms_list = [self.Fever, self.Chills, self.Headache, self.Myalgia, self.FatigueMalaise, self.Anemia, self.Leukopenia, self.Thrombocytopenia, self.ElevatedHepaticTransaminase, self.ElevatedCRP]
        if self.ClinicCompIndicator == "Yes" and any(symptom == 'Yes' for symptom in self.symptoms_list):
            return
        else:
            self.issues.append("Clinically compatible illness is 'Yes' but no symptom is 'Yes'")
            print(f"symptoms__clinically_compatible: {self.ClinicCompIndicator}")

    def CheckCase(self):
        """ Check if a patient's case status matches the case definition using test type and symptoms. """
        self.CaseStatus = self.ReadText('//*[@id="INV163"]')
        self.DNATest = self.ReadText('//*[@id="ME24175"]')
        self.DNAResult = self.ReadText('//*[@id="ME24149"]')
        self.AntibodyTest = self.ReadText('//*[@id="ME24115"]')
        # symptoms = [self.Fever, self.Chills, self.Headache, self.Myalgia, self.FatigueMalaise, self.Anemia, self.Leukopenia, self.Thrombocytopenia, self.ElevatedHepaticTransaminase, self.ElevatedCRP]
        if(any(symptom == 'Yes' for symptom in self.symptoms_list) and self.CaseStatus == "Confirmed"):
            return
        if self.ClinicCompIndicator == 'unknown' and self.CaseStatus != 'probable':
            self.issues.append("Clinically compatible is unknown but case status isn't probable")
            print(f"case_status: {self.CaseStatus}")

        if self.DNAResult == "Yes" and self.DNATest == "Yes":
            if self.Fever == "Yes" or self.Chills == "Yes" or self.Headache == "Yes" or self.Myalgia == "Yes" or self.FatigueMalaise == "Yes" or self.Anemia == "Yes" or self.Leukopenia == "Yes" or self.Thrombocytopenia == "Yes" or self.ElevatedHepaticTransaminase == "Yes" or self.ElevatedCRP == "Yes":
                if self.CaseStatus != "Confirmed":
                    self.issues.append("Meets case definition for a confirmed case but is not a confirmed case.")
                    print(f"case_status: {self.CaseStatus}")
            elif self.Fever != "Yes" and self.Chills != "Yes" and self.Headache != "Yes" and self.Myalgia != "Yes" and self.FatigueMalaise != "Yes" and self.Anemia != "Yes" and self.Leukopenia != "Yes" and self.Thrombocytopenia != "Yes" and self.ElevatedHepaticTransaminase != "Yes" and self.ElevatedCRP != "Yes":
                if self.CaseStatus != "Not a Case" and self.CaseStatus != "Suspect":                                                                             #new code. changed from 'or' to 'and' statement
                    self.issues.append("Does not meet the case definition, but does not have Not a Case or Suspect status.")
                    print(f"case_status: {self.CaseStatus}")
        elif any(self.Sero_table["Serology Positive?"] == "Yes"):
            titer_value = None
            if re.search(r":", str(self.Sero_table["Titer Value"])):
                print(f"titer: {str(self.Sero_table["Titer Value"])}")
                val = str(self.Sero_table["Titer Value"]).split("    ")[1].split(":")
                print(f"titer : {val}")
                titer_value = Fraction(int(val[0]), int(val[1].replace("\nName", "")))
                print(f"titer : {titer_value}")
            else:
                titer_value = int(self.Sero_table["Titer Value"])
            if all(float(titer_value) < 128):
                if self.CaseStatus != "Not a Case":
                    self.issues.append("Does not meet the case definition, but does not have Not a Case status.")
                    print(f"case_status: {self.CaseStatus}")
            else:
                if self.Fever != "Yes" and self.Chills != "Yes" and self.Headache != "Yes" and self.Myalgia != "Yes" and self.FatigueMalaise != "Yes" and self.Anemia != "Yes" and self.Leukopenia != "Yes" and self.Thrombocytopenia != "Yes" and self.ElevatedHepaticTransaminase != "Yes" and self.ElevatedCRP != "Yes":
                    if self.CaseStatus != "Suspect":
                        self.issues.append("Does not meet the case definition, but does not have Suspect status.")
                        print(f"case_status: {self.CaseStatus}")
                elif self.Fever == "Yes":
                    if self.Headache == "Yes" or self.Myalgia == "Yes" or self.FatigueMalaise == "Yes" or self.Anemia == "Yes" or self.Leukopenia == "Yes" or self.Thrombocytopenia == "Yes" or self.ElevatedHepaticTransaminase == "Yes" or self.ElevatedCRP == "Yes":
                        if self.CaseStatus != "Probable":
                            self.issues.append("Meets case definition for a probable case but is not a probable case.")
                            print(f"case_status: {self.CaseStatus}")
                    elif self.Headache != "Yes" and self.Myalgia != "Yes" and self.FatigueMalaise != "Yes" and self.Anemia != "Yes" and self.Leukopenia != "Yes" and self.Thrombocytopenia != "Yes" and self.ElevatedHepaticTransaminase != "Yes" and self.ElevatedCRP != "Yes":
                        if self.CaseStatus != "Not a Case":
                            self.issues.append("Does not meet the case definition, but does not have Not a Case status.")
                            print(f"case_status: {self.CaseStatus}")
                else:
                    if self.Chills == "Yes":
                        if self.Anemia == "Yes" or self.Leukopenia == "Yes" or self.Thrombocytopenia == "Yes" or self.ElevatedHepaticTransaminase == "Yes" or self.ElevatedCRP == "Yes":
                           if self.CaseStatus != "Probable":
                               self.issues.append("Meets case definition for a probable case but is not a probable case.")
                               print(f"case_status: {self.CaseStatus}")
                        else:
                            if (self.Headache == "Yes" and self.Myalgia == "Yes") or (self.Headache == "Yes" and self.FatigueMalaise == "Yes") or (self.FatigueMalaise == "Yes" and self.Myalgia == "Yes"):
                                if self.CaseStatus != "Probable":
                                    self.issues.append("Meets case definition for a probable case but is not a probable case.")
                                    print(f"case_status: {self.CaseStatus}")
                            else:
                                if self.CaseStatus != "Not a Case":
                                    self.issues.append("Does not meet the case definition, but does not have Not a Case status.")
                                    print(f"case_status: {self.CaseStatus}")
                    elif self.Chills != "Yes":
                        if self.CaseStatus != "Not a Case":
                            self.issues.append("Does not meet the case definition, but does not have Not a Case status.")
                            print(f"case_status: {self.CaseStatus}")
        else:
            if self.CaseStatus != "Not a Case":
                self.issues.append("Does not meet the case definition, but does not have Not a Case status.")
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
        