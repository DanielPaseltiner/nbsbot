# -*- coding: utf-8 -*-
"""
Created on Wed Apr 17 10:50:29 2024

@author: Jared.Strauch
"""

from covidcasereview import COVIDcasereview
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime
import re
from dateutil.relativedelta import relativedelta


class Anaplasmacasereview(COVIDcasereview):
    """ A class inherits all basic NBS functionality from NBSdriver and adds
    methods for reviewing COVID case investigations for data accuracy and completeness. """
    ####################### Patient Demographics Check Methods ############################
    def CheckAge(self):
        """ Must provide age. """
        self.age = self.ReadDate('//*[@id="INV2001"]')
        if not self.age:
            self.issues.append('Age is blank.')
        
    def CheckAgeType(self):
        """ Must age type must be one of Days, Months, Years. """
        self.age_type = self.ReadDate('//*[@id="INV2002"]')
        if not self.age_type:
            self.issues.append('Age Type is blank.')
        elif self.age_type != "Days" or self.age_type != "Months" or self.age_type != "Years":
            self.issues.append('Age Type is not one of Days, Months, or Years.')
        
    def CheckPhone(self):
        """ If a phone number is provided make sure it is ten digits. """
        home_phone = self.ReadText('//*[@id="DEM177"]')
        work_phone = self.ReadText('//*[@id="NBS002"]')
        cell_phone = self.ReadText('//*[@id="NBS006"]')
        if home_phone:
            #check if phone is ten digits if it exists
            if len(re.findall(r'\d', str(home_phone))) != 10:
                self.issues.append('Phone number is not ten digits.')
        elif work_phone:
            #check if phone is ten digits if it exists
            if len(re.findall(r'\d', str(work_phone))) != 10:
                self.issues.append('Phone number is not ten digits.')
        elif cell_phone:
            #check if phone is ten digits if it exists
            if len(re.findall(r'\d', str(cell_phone))) != 10:
                self.issues.append('Phone number is not ten digits.')
        
    #check if city is in county

    def CheckCurrentSex(self):
        """ Ensure patient current sex is not blank. """
        patient_sex = self.ReadText('//*[@id="DEM113"]')
        if not patient_sex:
            self.issues.append('Patient sex is blank.')
        elif self.patient_sex == "Unknown":
            comment = self.ReadText('//*[@id="DEM196"]')
            if not comment:
                self.issues.append('Patient sex is Unknown without a note.')
        
    ####################### Investigator Check Methods ############################
    #Needs to be around lab date, can be after if immediately notifiable
    def CheckInvestigationStartDate(self):
        """ Verify investigation start date is on or after report date. """
        self.investigation_start_date = self.ReadDate('//*[@id="INV147"]')
        if not self.investigation_start_date:
            self.issues.append('Investigation start date is blank.')
        elif self.investigation_start_date < (self.report_date + relativedelta(weeks=1)):
            self.issues.append('Investigation start date must be one week before or after report date.')
        elif self.investigation_start_date > self.now:
            self.issues.append('Investigation start date cannot be in the future.')

    def CheckInvestigator(self):
        """ Check if an investigator was assigned to the case. """
        investigator = self.ReadText('//*[@id="INV180"]')
        self.investigator_name = investigator
        if not investigator:
            self.issues.append('Investigator is blank.')
            

    def CheckInvestigatorAssignDate(self):
        """ If an investigator was assinged then there should be an investigator
        assigned date. """
        if self.investigator_name:
            assigned_date = self.ReadText('//*[@id="INV110"]')
            if not assigned_date:
                self.issues.append('Missing investigator assigned date.')
            elif assigned_date <= self.investigation_start_date:
                self.issues.append('Investigator assigned date is before investigation start date.')
    
    ####################### Patient Status Check Methods ############################
    def CheckDeath(self):
        """If died from illness is yes or no, need a death date """
        self.death_indicator =  self.CheckForValue('//*[@id="INV145"]','Died from illness must be yes or no.')
        if self.death_indicator == "Yes":
            """ Death date must be present."""
            death_date = self.ReadDate('//*[@id="INV146"]')
            if not death_date:
                self.issues.append('Date of death is blank.')
            elif death_date > self.now:
                self.issues.append('Date of death date cannot be in the future')
    def CheckHospitalization(self):
        """ Read hospitalization status. If yes need date and hospital """
        self.hospitalization_indicator = self.ReadText('//*[@id="INV128"]')
        if self.hospitalization_indicator == "Yes":
            hospital_name = self.ReadText('//*[@id="INV184"]')
            if not hospital_name:
                self.issues.append('Hospital name missing.')
            self.admission_date = self.ReadDate('//*[@id="INV132"]')
            if not self.admission_date:
                self.issues.append('Admission date is missing.')
            elif self.admission_date > self.now:
                self.issues.append('Admission date cannot be in the future.')
    def CheckIllnessDurationUnits(self):
        """ Read Illness duration units, should be either Day, Month, or Year """
        self.IllnessDurationUnits = self.ReadText('//*[@id="INV140"]')
        if self.IllnessDurationUnits != "Day" or self.IllnessDurationUnits != "Month" or self.IllnessDurationUnits != "Year":
            self.issues.append('Illness Duration is not in Days, Months, or Years.')
    
    ################# Anaplasma Specific Check Methods ###############################
    def CheckTickBite(self):
        """ If Tick bite is yes, need details """
        self.TickBiteIndicator = self.ReadText('//*[@id="ME23117"]')
        if not self.TickBiteIndicator:
            self.issues.append('Missing tick bite history.')
        elif self.TickBiteIndicator == "Yes":
            self.TickBiteNote = self.ReadText('//*[@id="ME23119"]')
            if not self.TickBiteNote:
                self.issues.append('History of tick bite, but no details.')
    def CheckOutbreak(self):
        """ Outbreak should not be yes """
        self.OutbreakIndicator = self.ReadText('//*[@id="INV150"]')
        if self.OutbreakIndicator == "Yes":
            self.issues.append('Outbreak should not be yes.')
    def CheckImmunosupressed(self):
        """ If patient is immunosupressed, need condition info """
        self.ImmunosupressedIndicator = self.ReadText('//*[@id="ME24123"]')
        if self.ImmunosupressedIndicator == "Yes":
            self.ImmunosupressedNote = self.ReadText('//*[@id="ME15113"]')
            if not self.ImmunosupressedNote:
                self.issues.append('Patient is immunosurpressed, but the condition is not listed.')
    def CheckLifeThreatening(self):
        """ If patient has a life threatening condition, need condition info """
        self.LifeThreateningIndicator = self.ReadText('//*[@id="ME24117"]')
        if self.LifeThreateningIndicator != "":
            self.LifeThreateningNote = self.ReadText('//*[@id="ME24124"]')
            if not self.LifeThreateningNote:
                self.issues.append('Patient has a life-threatening condition, but the condition is not listed.')
    def CheckSerology(self):
        """ If patient has reported positive serology the serology section needs to be filled out. """
        self.SerologyIndicator = self.ReadText('//*[@id="ME24113"]')
        if self.SerologyIndicator == "Yes":
            self.SerologyCollectionDate = self.ReadText('//*[@id="ME24110"]')
            if not self.SerologyCollectionDate:
                self.issues.append('Patient has positive serology, but the collection date is not listed.')
            self.SerologyTestType = self.ReadText('//*[@id="ME24111"]')
            if not self.SerologyTestType:
                self.issues.append('Patient has positive serology, but the test type is not listed.')
            self.SerologyTiterValue = self.ReadText('//*[@id="ME23133"]')
            if not self.SerologyTiterValue:
                self.issues.append('Patient has positive serology, but the titer value is not listed.')

        