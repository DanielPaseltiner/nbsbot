from nbsdriver import NBSdriver
from datetime import datetime
import configparser
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import pandas as pd

class COVIDcasereview(NBSdriver):
    """ A class inherits all basic NBS functionality from NBSdriver and adds
    methods for reviewing COVID case investigations for data accuracy and completeness. """
    def __init__(self, production=False):
        self.Reset()
        self.GetObInvNames()
        self.not_a_case_log = []
        self.lab_data_issues_log = []
        super(COVIDcasereview, self).__init__(production)

    def GetObInvNames(self):
        """ Read list of congregate setting outbreak investigators from config file. """
        outbreak_investigators = configparser.ConfigParser()
        outbreak_investigators.read('cong_outbreak_investigators.cfg')
        self.outbreak_investigators = outbreak_investigators.get('OutbreakInvestigators', 'Investigators').split(', ')

    def Reset(self):
        """ Clear values of attributes assigned during case investigation review.
        To be used on initialization and between case reviews. """
        self.issues = []
        self.now = datetime.now().date()
        self.collection_date = None
        self.cong_aoe = None
        self.cong_setting_indicator = None
        self.county = None
        self.current_report_date = None
        self.current_status = None
        self.death_indicator = None
        self.dob = None
        self.first_responder = None
        self.fr_aoe = None
        self.hcw_aoe = None
        self.healthcare_worker = None
        self.hosp_aoe = None
        self.hospitalization_indicator = None
        self.icu_aoe = None
        self.icu_indicator = None
        self.immpact = None
        self.investigation_start_date = None
        self.investigator = None
        self.labs = None
        self.ltf = None
        self.preg_aoe = None
        self.report_date = None
        self.status = None
        self.symp_aoe = None
        self.symptoms = None
        self.vax_recieved = None

######################### Name Information Check Methods #######################
    def CheckFirstName(self):
        """ Must provide first name. """
        first_name = self.CheckForValue( '//*[@id="DEM104"]', 'First name is blank.')

    def CheckLastName(self):
        """ Must provide last name. """
        last_name = self.CheckForValue( '//*[@id="DEM102"]', 'last name is blank.')

###################### Other Personal Details Check Methods ####################
    def CheckDOB(self):
        """ Must provide DOB. """
        self.dob = self.ReadDate('//*[@id="DEM115"]')
        if not self.dob:
            self.issues.append('DOB is blank.')
        elif self.dob > self.now:
            self.issues.append('DOB cannot be in the future.')

    def CheckCurrentSex(self):
        """ Ensure patient current sex is not blank. """
        patient_sex = self.CheckForValue('//*[@id="DEM113"]','Current Sex is blank.')

#################### Reporting Address Check Methods ###########################
    def CheckStAddr(self):
        """ Must provide street address. """
        street_address = self.CheckForValue( '//*[@id="DEM159"]', 'Street address is blank.')

    def CheckCity(self):
        """ Must provide city. """
        city = self.CheckForValue( '//*[@id="DEM161"]', 'City is blank.')

    def CheckState(self):
        """ Must provide state and if it is not Maine case should be not a case. """
        state = self.CheckForValue( '//*[@id="DEM162"]', 'State is blank.')
        if state != 'Maine':
            self.issues.append('State is not Maine.')

    def CheckZip(self):
        """ Must provide zip code. """
        zipcode = self.CheckForValue( '//*[@id="DEM163"]', 'Zip code is blank.')

    def CheckCounty(self):
        """ Must provide county. """
        self.county = self.CheckForValue( '//*[@id="DEM165"]', 'County is blank.')

    def CheckCountry(self):
        """ Must provide country. """
        country = self.CheckForValue( '//*[@id="DEM167"]', 'Country is blank.')
        if country != 'UNITED STATES':
            self.issues.append('Country listed is not USA.')

############ Ethnicity and Race Information Check Methods #####################
    def CheckEthnicity(self):
        """ Must provide ethnicity. """
        ethnicity = self.CheckForValue('//*[@id="DEM155"]','Ethnicity is blank.')

    def CheckRace(self):
        """ Must provide race and selection must make sense. """
        race = self.CheckForValue('//*[@id="patientRacesViewContainer"]','Race is blank.')
        # Race should only be unknown if no other options are selected.
        if ('Unknown' in race) and (race != 'Unknown'):
            self.issues.append('Unknown selected in addition to other options for race.')

################### Investigation Details Check Methods ########################
    def CheckJurisdiction(self):
        """ Jurisdiction and county must match. """
        jurisdiction = self.CheckForValue('//*[@id="INV107"]','Jurisdiction is blank.')
        if jurisdiction not in self.county:
            self.issues.append('County and jurisdiction mismatch.')

    def CheckProgramArea(self):
        """ Program area must be Airborne. """
        program_area = self.CheckForValue('//*[@id="INV108"]','Program Area is blank.')
        if program_area != 'Airborne and Direct Contact Diseases':
            self.issues.append('Program Area is not "Airborne and Direct Contact Diseases".')

    def CheckInvestigationStartDate(self):
        """ Verify investigation start date is on or after report date. """
        self.investigation_start_date = self.ReadDate('//*[@id="INV147"]')
        if not self.investigation_start_date:
            self.issues.append('Investigation start date is blank.')
        elif self.investigation_start_date < self.report_date:
            self.issues.append('Investigation start date must be on or after report date.')
        elif self.investigation_start_date > self.now:
            self.issues.append('Investigation start date cannot be in the future.')

    def CheckInvestigationStatus(self):
        """ Only accept closed investigations for review. """
        inv_status = self.ReadText('//*[@id="INV109"]')
        if not inv_status:
            self.issues.append('Investigation status is blank.')
        elif inv_status == 'Open':
            self.issues.append('Investigation status is open.')

    def CheckSharedIndicator(self):
        """ Ensure shared indicator is yes. """
        shared_indicator = self.ReadText('//*[@id="NBS_UI_19"]/tbody/tr[5]/td[2]')
        if shared_indicator != 'Yes':
            self.issues.append('Shared indicator not selected.')

    def CheckStateCaseID(self):
        """ State Case ID must be provided. """
        case_id = self.ReadText('//*[@id="INV173"]')
        if not case_id:
            self.issues.append('State Case ID is blank.')

####################### Investigator Check Methods ############################
    def CheckInvestigator(self):
        """ Check if an investigator was assigned to the case. """
        investigator = self.ReadText('//*[@id="INV180"]')
        self.investigator_name = investigator
        if investigator:
            self.investigator = True
        else:
            self.investigator = False

    def CheckInvestigatorAssignDate(self):
        """ If an investigator was assinged then there should be an investigator
        assigned date. """
        if self.investigator:
            assigned_date = self.ReadText('//*[@id="INV110"]')
            if not assigned_date:
                self.issues.append('Missing investigator assigned date.')

################# Key Report Dates Check Methods ###############################
    def CheckReportDate(self):
        """ Check if the current value of Report Date matches the earliest
        Report Date from the associated labs. """
        self.current_report_date = self.ReadDate('//*[@id="INV111"]')
        if not self.current_report_date:
            self.issues.append('Missing report date.')
        elif self.current_report_date > self.investigation_start_date:
            self.issues.append('Report date cannot be after investigation start date.')
        elif self.report_date != self.current_report_date:
            self.issues.append('Report date mismatch.')

    def CheckCountyStateReportDate(self):
        """ Check if the current value of county report date is consistent with
        the current value of earliest report to state date and the report date. """
        current_county_date = self.ReadDate('//*[@id="INV120"]')
        current_state_date = self.ReadDate('//*[@id="INV121"]')

        if not current_county_date:
            self.issues.append('Report to county date missing.')
        elif current_county_date < self.current_report_date:
            self.issues.append('Earliest report to county cannot be prior to inital report date.')
        elif current_county_date > self.investigation_start_date:
            self.issues.append('Earliest report to county date cannot be after investigation start date')

        if not current_state_date:
            self.issues.append('Report to state date missing.')
        elif current_state_date < self.current_report_date:
            self.issues.append('Earliest report to state cannot be prior to inital report date.')
        elif current_state_date > self.investigation_start_date:
            self.issues.append('Earliest report to state date cannot be after investigation start date.')

        if current_county_date:
            if current_state_date:
                if current_county_date != current_state_date:
                    self.issues.append('Earliest dates reported to county and state do not match.')

################### Reporting Organization Check Methods #######################
    def CheckReportingSourceType(self):
        """ Ensure that reporting source type is not empty. """
        reporting_source_type = self.ReadText('//*[@id="INV112"]')
        if not reporting_source_type:
            self.issues.append('Reporting source type is blank.')

    def CheckReportingOrganization(self):
        """ Ensure that reporting organization is not empty. """
        reporting_organization = self.ReadText('//*[@id="INV183"]')
        if not reporting_organization:
            self.issues.append('Reporting organization is blank.')
############### Preforming Lab Check Methods ##################################
    def CheckPreformingLaboratory(self):
        """ Ensure that preforming laboratory is not empty. """
        reporting_organization = self.ReadText('//*[@id="ME6105"]')
        if not reporting_organization:
            self.issues.append('Performing laboratory is blank.')

    def CheckCollectionDate(self):
        """ Check if collection date is present and matches earliest date from
        associated labs. """
        current_collection_date = self.ReadDate('//*[@id="NBS550"]')
        if not current_collection_date:
            self.issues.append('Collection date is missing.')
        elif current_collection_date != self.collection_date:
            self.issues.append('Collection date mismatch.')
        elif current_collection_date > self.investigation_start_date:
            self.issues.append('Collection date cannot be after investigation start date.')

###################### COVID-19 Case Details Check Methods #####################
    def CheckCurrentStatus(self):
        """ Check if current status in the investigation is consistent with the
        associated labs. """
        self.current_status = self.ReadText('//*[@id="NBS548"]')
        if (self.current_status == 'Probable Case') & (self.status != 'P'):
            self.issues.append('Current status mismatch.')
        elif (self.current_status == 'Laboratory-confirmed case') & (self.status != 'C'):
            self.issues.append('Current status mismatch.')
        elif not self.current_status:
            self.issues.append('Current status is blank.')

    def CheckProbableReason(self):
        """ Check if probable reason is consistent with current status and case
        status. """
        probable_reason = self.ReadText('//*[@id="NBS678"]')
        probable_reason = probable_reason.replace('\n','')
        if (probable_reason == 'Meets Presump Lab and Clinical or Epi') & ((self.status != 'P') | (self.current_status != 'Probable Case')):
            self.issues.append('Status inconsistency.')
        elif probable_reason in ['Meets Clinical/Epi, No Lab Conf', 'Meets Vital Records, No Lab Confirm']:
            self.issues.append('Probable reason does not include a lab. Human review required.')
        elif (not probable_reason) & (self.status not in ['C', 'S']):
            self.issues.append('Probable reason is blank and correct status is not confirmed or suspect.')

######################## Administrative Questions Check Methods ###############
    def CheckFirstAttemptDate(self):
        """ Verify that first attempt to contact date is provided and greater
        than or equal to investigation start date. """
        first_attempt_date = self.ReadDate('//*[@id="ME64102"]')
        if not first_attempt_date:
            self.issues.append('First attempt to contact date is blank.')
        elif first_attempt_date < self.investigation_start_date:
            self.issues.append('First attempt to contact must be on or after investigation start date.')
        elif first_attempt_date > self.now:
            self.issues.append('First attempt to contact date cannot be in the future.')

#################### Hospital Check Methods ###################################
    def CheckHospitalizationIndicator(self):
        """ Read hospitalization status. If an investigation was conducted it must be Yes or No """
        self.hospitalization_indicator = self.ReadText('//*[@id="INV128"]')
        if (self.ltf != 'Yes') & (self.investigator):
            if self.hospitalization_indicator not in ['Yes', 'No']:
                self.issues.append("Patient hospitalized must be 'Yes' or 'No'.")

    def CheckHospitalName(self):
        """" If the case is hospitalized then a hospital name must be provided. """
        hospital_name = self.ReadText('//*[@id="INV184"]')
        if not hospital_name:
            self.issues.append('Hospital name missing.')

    def CheckAdmissionDate(self):
        """ Check for hospital admission date."""
        self.admission_date = self.ReadDate('//*[@id="INV132"]')
        if not self.admission_date:
            self.issues.append('Admission date is missing.')
        elif self.admission_date > self.now:
            self.issues.append('Admission date cannot be in the future.')

    def CheckDischargeDate(self):
        """ Check for hospital discharge date."""
        discharge_date = self.ReadDate('//*[@id="INV133"]')
        if not discharge_date:
            self.issues.append('Discharge date is missing.')
        elif discharge_date < self.admission_date:
            self.issues.append('Discharge date must be after admission date.')
        elif discharge_date > self.now:
            self.issues.append('Discharge date cannot be in the future.')

    def CheckIcuIndicator(self):
        """ If case is hospitalized then we should know if they were ever in the ICU."""
        self.icu_indicator = self.ReadText('//*[@id="309904001"]')
        if (self.ltf != 'Yes') & (self.hospitalization_indicator == 'Yes') & (self.investigator):
            if not self.icu_indicator:
                self.issues.append('ICU indicator is blank.')

    def CheckIcuAdmissionDate(self):
        """ Check for ICU admission date."""
        self.icu_admission_date = self.ReadDate('//*[@id="NBS679"]')
        if not self.icu_admission_date:
            self.issues.append('ICU admission date is missing.')
        elif self.icu_admission_date > self.now:
            self.issues.append('ICU admission date cannot be in the future.')

    def CheckIcuDischargeDate(self):
        """ Check for ICU discharge date. """
        icu_discharge_date = self.ReadDate('//*[@id="NBS680"]')
        if not icu_discharge_date:
            self.issues.append('ICU discharge date is missing.')
        elif icu_discharge_date < self.icu_admission_date:
            self.issues.append('ICU discharge date must be after admission date.')
        elif icu_discharge_date > self.now:
            self.issues.append('ICU discharge date cannot be in the future.')

    def CheckDieFromIllness(self):
        """ Died from illness should be yes or no. """
        self.death_indicator =  self.CheckForValue('//*[@id="INV145"]','Died from illness must be yes or no.')

    def CheckDeathDate(self):
        """ Death date must be present."""
        death_date = self.ReadDate('//*[@id="INV146"]')
        if not death_date:
            self.issues.append('Date of death is blank.')
        elif death_date > self.now:
            self.issues.append('Date of death date cannot be in the future')

#################### Housing Check Methods ###################################
    def CheckCongregateSetting(self):
        """ Check if a patient lives in congregate setting."""
        if self.site == 'https://nbstest.state.me.us/':
            xpath = '//*[@id="95421_4"]'
        else:
            xpath = '//*[@id="ME3130"]'
        self.cong_setting_indicator = self.ReadText(xpath)
        if self.investigator:
            if (self.investigator_name in self.outbreak_investigators) & (self.cong_setting_indicator not in ['Yes', 'No']):
                self.issues.append('Congregate setting question must be answered with "Yes" or "No".')
            elif (self.ltf != 'Yes') & (not self.cong_setting_indicator):
                self.issues.append('Congregate setting status must have a value.')

    def CheckCongregateFacilityName(self):
        """ Need a congregate faciltiy name if patient lives in congregate setting."""
        cong_fac_name = self.CheckForValue('//*[@id="ME134008"]','Name of congregate facility is missing.')

#################### First Responder Check Methods #############################
    def CheckFirstResponder(self):
        """ Check if a patient is a first responder."""
        self.first_responder =  self.ReadText('//*[@id="ME59100"]')
        if (self.investigator) & (self.investigator_name not in self.outbreak_investigators) & (self.ltf != 'Yes') & (not self.first_responder):
            self.issues.append('First responder question must be answered.')

    def CheckFirstResponderOrg(self):
        """ Check first responder organization."""
        first_responder_org = self.CheckForValue('//*[@id="ME59116"]','First responder organization is blank.')

#################### Healthcare Worker Check Methods ###########################
    def CheckHealthcareWorker(self):
        """ Check if patient is a healthcare worker."""
        self.healthcare_worker = self.ReadText('//*[@id="NBS540"]')
        if self.investigator:
            if (self.investigator_name in self.outbreak_investigators) & (self.healthcare_worker not in ['Yes', 'No']):
                self.issues.append('Healthcare worker questions must be answered with "Yes" or "No".')
            elif (self.ltf != 'Yes') & (not self.healthcare_worker):
                self.issues.append('Healthcare worker question is blank.')

    def CheckHealtcareWorkerFacility(self):
        """ If the patient is a healthcare worker then a facility name must be provided."""
        if (self.ltf != 'Yes') & (self.investigator):
            healthcare_worker_fac =  self.CheckForValue('//*[@id="ME10103"]','Healthcare worker facility is blank.')

    def CheckHealthcareWorkerJob(self):
        """ If the patient is a healthcare worker then an occupation name must be provided."""
        xpath = '//*[@id="14679004"]'
        if (self.ltf != 'Yes') & (self.investigator):
            self.healthcare_worker_job =  self.CheckForValue(xpath,'Healthcare worker occupation is blank.')
        else:
            self.healthcare_worker_job = self.ReadText(xpath)

    def CheckHealthcareWorkerJobOther(self):
        """ If the patient is a healthcare worker and occupation is other then name must be provided."""
        if (self.ltf != 'Yes') & (self.investigator):
            healthcare_worker_job_other =  self.CheckForValue('//*[@id="14679004Oth"]','Healthcare worker other occupation is missing.')

    def CheckHealthcareWorkerSetting(self):
        """ If the patient is a healthcare worker then healthcare setting name must be provided."""
        xpath = '//*[@id="NBS683"]'
        if (self.ltf != 'Yes') & (self.investigator):
            self.healthcare_worker_setting =  self.CheckForValue(xpath, 'Healthcare worker setting is blank.')
        else:
            self.healthcare_worker_setting =  self.ReadText(xpath)

    def CheckHealthcareWorkerSettingOther(self):
        """ If the patient is a healthcare worker and setting is other then name must be provided."""
        healthcare_worker_setting_other =  self.CheckForValue('//*[@id="NBS683Oth"]','Healthcare worker other setting is missing.')

###################### Close Contact Check Methods #############################
    def GetNumListedCloseContacts(self):
        """Determine number of rows in close contact table to find the number of
        close contacts listed."""

        if self.production:
            xpath = '//*[@id="questionbodyUI_ME59100"]'
        else:
            xpath = '//*[@id="ME60100"]/tbody/tr[1]/td/table/tbody'
        try:
            table = self.ReadTableToDF(xpath)
            num_listed_contacts = len(table)
        except ValueError:
            num_listed_contacts = 0
        return num_listed_contacts

    def CheckNumCloseContacts(self):
        """ Ensure that the number of close contacts listed is consistent with
        the number of entries in the Sara Alert repeating block."""
        num_contacts = self.ReadText('//*[@id="ME59105"]')
        table_contacts = self.GetNumListedCloseContacts()
        if (not num_contacts) & (table_contacts > 0):
            self.issues.append(f'Number of close contacts is blanks, but {table_contacts} are listed in repeating block.')
        elif num_contacts:
            if int(num_contacts) < table_contacts:
                self.issues.append('Number of close contacts is less than the number of contacts listed in the repeating block.')

###################### Exposure Information Check Methods ######################
    def CheckExposureSection(self):
        """ Make sure that exposure section contains at least one 'Yes' and if
        more than one that "Uknown exposure" is not included."""
        html = self.find_element(By.XPATH, '//*[@id="NBS_UI_GA21014"]/tbody').get_attribute('innerHTML')
        soup = BeautifulSoup(html, 'html.parser')
        num_exposures = str(soup).count('Yes')
        unknown_exposure = self.ReadText('//*[@id="NBS667"]')
        if num_exposures == 0:
            self.issues.append('Exposure section is not complete.')
        elif (unknown_exposure == 'Yes') & (num_exposures > 1):
            self.issues.append('If unknown exposure is selected then no other exposures should be indicated.')

    def CheckDomesticTravel(self):
        """ If domestic travel is indicated states involved must be specified."""
        parent_xpath = '//*[@id="INV664"]'
        child_xpath = '//*[@id="82754_3"]'
        message = "State(s) must be specified when domestic travel is 'Yes'."
        self.CheckIfField(parent_xpath, child_xpath, 'Yes', message)

    def CheckShipTravel(self):
        """ If travel by boat is indicated vessel name must be specified."""
        parent_xpath = '//*[@id="473085002"]'
        child_xpath = '//*[@id="NBS690"]'
        message = "When travel by boat is indicated vessel name must be specified."
        self.CheckIfField(parent_xpath, child_xpath, 'Yes', message)

    def CheckSchoolExposure(self):
        """ If school/daycare exposure is indicated ensure that facility name is
        provided."""
        if self.site == 'https://nbs.iphis.maine.gov/':
            school_exposure = self.ReadText('//*[@id="NBS688"]')
            if school_exposure == 'Yes':
                school_name = self.ReadText('//*[@id="ME62100"]')
                university_name = self.ReadText('//*[@id="ME62101"]')
                daycare_name = self.ReadText('//*[@id="ME10106"]')
                if (not school_name) & (not university_name) & (not daycare_name):
                    self.issues.append("If school/daycare/university exposure is indicated then school/daycare/university name must be specified.")
                if school_name == 'Other':
                    other_school_name = self.ReadText('//*[@id="ME62100Oth"]')
                    if not other_school_name:
                        self.issues.append('Other school name is blank.')
                if university_name == 'Other':
                    other_university_name = self.ReadText('//*[@id="ME62101Oth"]')
                    if not other_university_name:
                        self.issues.append('Other university name is blank.')

    def CheckOutbreakExposure(self):
        """ If outbreak exposure is indicated then outbreak name must be provided.
        If the case is assigned to outbreak investigator outbreak exposure section must be complete."""
        outbreak_exposure_path = '//*[@id="INV150"]'
        outbreak_name_path = '//*[@id="ME125032"]'
        check_condition = 'Yes'
        message = "Outbreak name must be provided if outbreak exposure is indicated."

        if self.investigator_name in self.outbreak_investigators:
            ob_exposure = self.ReadText(outbreak_exposure_path)
            if ob_exposure != 'Yes':
                self.issues.append('Outbreak exposure must be "Yes" and outbreak name must be specified.')
            else:
                self.CheckForValue(outbreak_name_path, 'Outbreak name in exposure section is blank.')
        else:
            self.CheckIfField(outbreak_exposure_path, outbreak_name_path, check_condition, message)

######################### Case Status Check Methods ############################
    def CheckTransmissionMode(self):
        """ Transmission mode should blank or airborne"""
        transmission_method =  self.ReadText('//*[@id="INV157"]')
        if transmission_method not in ['', 'Airborne']:
            self.issues.append('Transmission mode should be blank or airborne.')

    def CheckConfirmationMethod(self):
        """ Confirmation Method must be blank or consistent with correct case status."""
        confirmation_method =  self.ReadText('//*[@id="INV161"]')
        if confirmation_method:
            if (self.status == 'C') & ('Laboratory confirmed' not in confirmation_method):
                self.issues.append('Since correct case status is confirmed confirmation method should include "Laboratory confirmed".')
            elif (self.status == 'P') & ('Laboratory report' not in confirmation_method):
                self.issues.append('Since correct case status is probable confirmation method should include "Laboratory report".')
            elif (self.status == 'S') & ('Clinical diagnosis (non-laboratory confirmed)' not in confirmation_method):
                self.issues.append('Since correct case status is probable confirmation method should include "Clinical diagnosis (non-laboratory confirmed)".')

    def CheckDetectionMethod(self):
        """ Ensure Detection Method is not blank. """
        detection_method = self.CheckForValue( '//*[@id="INV159"]', 'Detection method is blank.')

    def CheckConfirmationDate(self):
        """ Confirmation date must be on or after report date. """
        confirmation_date = self.ReadDate('//*[@id="INV162"]')
        if not confirmation_date:
            self.issues.append('Confirmation date is blank.')
        elif confirmation_date < self.report_date:
            self.issues.append('Confirmation date cannot be prior to report date.')
        elif confirmation_date > self.now:
            self.issues.append('Confirmation date cannot be in the future.')

    def CheckCaseStatus(self):
        """ Case status must be consistent with associated labs. """
        current_case_status = self.ReadText('//*[@id="INV163"]')
        status_pairs = {'Confirmed':'C', 'Probable':'P', 'Suspect':'S', 'Not a Case':'N'}
        if current_case_status == 'Not a Case':
            self.issues.insert(0,'**NOT A CASE: CENTRAL EPI REVIEW REQUIRED**')
            self.not_a_case_log.append(self.ReadPatientID())
        elif not current_case_status:
            self.issues.append('Case satus is blank.')
        elif status_pairs[current_case_status] != self.status:
            self.issues.append('Case status mismatch.')

    def CheckMmwrWeek(self):
        """ MMWR week must be provided."""
        mmwr_week = self.CheckForValue( '//*[@id="INV165"]', "MMWR Week is blank.")

    def CheckMmwrYear(self):
        """ MMWR year must be provided."""
        mmwr_year = self.CheckForValue( '//*[@id="INV166"]', "MMWR Year is blank.")

    def CheckLostToFollowUp(self):
        """ Check if case is lost to follow up. """
        self.ltf = self.ReadText('//*[@id="ME64100"]')
        self.ltf = self.ltf.replace('\n', '')
        if self.ltf == 'Unknown':
            self.issues.append('Lost to follow up inidicator cannot be unknown.')
        elif (not self.ltf) & self.investigator:
            self.issues.append('Lost to follow up cannot be blank.')

    def CheckClosedDate(self):
        """ Check if a closed date is provided and makes sense"""
        closed_date = self.ReadDate('//*[@id="ME11163"]')
        if not closed_date:
            self.issues.append('Investigation closed date is blank.')
        elif closed_date > self.now:
            self.issues.append('Closed date cannot be in the future.')
        elif closed_date < self.investigation_start_date:
            self.issues.append('Closed date cannot be before investigation start date.')

######################### Symptom Check Methods ################################
    def CheckSymptoms(self):
        """" Check symptom status of case. """
        self.symptoms = self.ReadText('//*[@id="INV576"]')
        if (self.ltf != 'Yes') & (self.investigator):
            if not self.symptoms:
                self.issues.append("Symptom status is blank.")

    def CheckSymptomDatesAndStatus(self):
        """ Ensure date of symptom onset, resolution, and current symptom status
        are consistent."""
        symp_onset_date = self.ReadDate('//*[@id="INV137"]')
        symp_resolution_date = self.ReadDate('//*[@id="INV138"]')
        symp_status = self.ReadText('//*[@id="NBS555"]')

        if not symp_status:
            self.issues.append('Symptom status is blank.')
        elif symp_status == 'Still symptomatic':
            if not symp_onset_date:
                self.issues.append('Symptom onset date is blank.')
            elif symp_onset_date > self.now:
                self.issues.append('Symptom onset date cannot be in the future.')
            if symp_resolution_date:
                self.issues.append('Symptom resolution date should be blank if still symptomatic.')
        elif symp_status == 'Symptoms resolved':
            if not symp_onset_date:
                self.issues.append('Symptom onset date is blank.')
            elif symp_onset_date > self.now:
                self.issues.append('Symptom onset date cannot be in the future.')
            if not symp_resolution_date:
                self.issues.append('Symptom resolution date is blank. If date unknown choose "Symptoms resolved, unknown date" for symptom status.')
            elif symp_onset_date:
                if symp_resolution_date < symp_onset_date:
                    self.issues.append('Symptom resolution date cannot be prior to symptom onset date.')
            elif symp_resolution_date > self.now:
                self.issues.append('Symptom resolution date cannot be in the future.')
        elif symp_status == 'Symptoms resolved, unknown date':
            if not symp_onset_date:
                self.issues.append('Symptom onset date is blank.')
            if symp_resolution_date:
                self.issues.append('Symptom resolution date is not blank. If date known choose "Symptoms resolved" for symptom status.')
        elif symp_status == 'Unknown symptom status':
            self.issues.append('Symptom status cannot be "Unknown symptom status".')

########################### Isolation Check Methods ############################
    def CheckIsolation(self):
        """ Ensure isolation release indicator, release date, and died from illness
        indicator are all consistent."""
        isolation_release = self.ReadText('//*[@id="NBS555"]')
        isolation_release_date = self.ReadDate('//*[@id="INV138"]')
        if (self.death_indicator == 'Yes') & (isolation_release != 'No'):
            self.issues.append('Died from illness indicator and isolation release indicator are inconsistent.')
        if isolation_release == 'Yes':
            if not isolation_release_date:
                self.issues.append('Must provide release date if released from isolation.')
            elif isolation_release_date > self.now:
                self.issues.append('Isolation release date cannot be in the future.')

############### Pre-existing Medical Conditions Check Methods ##################
    def CheckPreExistingConditions(self):
        """ Ensure pre-exisiting condtions indicator is consistent with medical history."""
        pre_existing_conditions = self.ReadText('//*[@id="102478008"]')
        medical_hx = 'Yes' in self.ReadText('//*[@id="NBS_UI_GA21008"]/tbody')
        if not pre_existing_conditions:
            self.issues.append('Pre-existing medical conditions is not answered.')
        elif (pre_existing_conditions == 'Yes') & (not medical_hx):
            self.issues.append('Pre-existing medical conditions are indicated, but none are specified in medical history.')
        elif (pre_existing_conditions == 'No') & (medical_hx):
            self.issues.append('Pre-existing medical conditions are not indicated, but some are specified in medical history.')

########### Vaccination Interperative Information Check Methods ################
    def CheckImmPactQuery(self):
        """ Ensure ImmPact was queried when age eligible. """
        self.immpact = self.ReadText('//*[@id="ME71100"]')
        try:
            age = int((self.collection_date - self.dob).days//365.25)
            if (self.immpact != 'Yes') & (age >= 5):
                self.issues.append('ImmPact has not been queried.')
        except TypeError:
            self.issues.append('Unable to compute age because of bad/missing collection date or DOB -> ImmPact check applied regardless of age.')
            if self.immpact != 'Yes':
                self.issues.append('ImmPact has not been queried.')



    def CheckRecievedVax(self):
        """ Ever recieved vaccine should only be no when case not LTFU. """
        self.vax_recieved = self.ReadText('//*[@id="VAC126"]')
        if (self.vax_recieved == 'No') & (self.ltf != 'No'):
            self.issues.append('Unless lost to follow up is "No" vaccine recieved cannot be "No".')
        elif (self.ltf == 'No') & (not self.vax_recieved):
            self.issues.append('If the case is not lost to follow up then vaccine recieved must be answered.')
        elif self.vax_recieved == 'Yes':
            dose_number = self.ReadText('//*[@id="VAC140"]')
            if not dose_number:
                self.issues.append('Doses prior to onset cannot be blank if Vacinated is "Yes".')
            elif dose_number == '0':
                self.issues.append('Number of doses prior to onset cannot be zero.')
            last_dose_date = self.ReadDate('//*[@id="VAC142"]')
            first_vax_date = datetime(2020, 12, 15).date()
            if not last_dose_date:
                self.issues.append('Last dose date is blank.')
            elif last_dose_date < first_vax_date:
                self.issues.append('Last dose date is prior to when vaccinations become available.')
            elif last_dose_date > self.now:
                self.issues.append('Last dose date cannot be in the future.')

    def CheckFullyVaccinated(self):
        """ Validate fully vaccinated question"""
        fully_vaccinated = self.ReadText('//*[@id="ME70100"]')
        if (fully_vaccinated not in ['Yes', 'No']) & (self.ltf == 'No'):
            self.issues.append("Fully vaccinated cannot be blank or unknown when case is not lost to followup.")
        if (fully_vaccinated == 'Yes') & (self.vax_recieved == 'No'):
            self.issues.append("Fully vaccinated cannot be Yes is vaccine recieved is No.")

########################## COVID Testing Check Methods #########################
    def CheckTestingPreformed(self):
        """Ensure testing preformed is Yes or No."""
        self.testing_preformed = self.ReadText('//*[@id="INV740"]')
        if self.testing_preformed not in ['Yes', 'No']:
            self.issues.append("Laboratory testing preformed connot be blank or unknown.")

    def CheckLabTable(self):
        """ Ensure that labs listed in investigation support case status. """
        inv_labs = self.ReadTableToDF('//*[@id="NBS_UI_GA21011"]/tbody/tr[1]/td/table')
        if len(inv_labs) == 0:
            self.issues.append('No labs listed in investigation.')
        if len(inv_labs.loc[inv_labs['Test Result'] != 'Positive']) > 0:
            self.issues.append('All labs list in investigation must be positive.')
        status_lab_pairs = {'C':'PCR', 'P':'Ag', 'S':'Ab'}
        if self.status in status_lab_pairs.keys():
            if len(inv_labs.loc[inv_labs['Test Type'].str.contains(status_lab_pairs[self.status])]) == 0:
                self.issues.append('Lab(s) listed in investigation do not support correct case status.')

########################### Parse and process labs ############################
    def ReadAssociatedLabs(self):
        """ Read table of associated labs."""
        self.labs = self.ReadTableToDF('//*[@id="viewSupplementalInformation1"]/tbody')
        if self.labs['Date Received'][0] == 'Nothing found to display.':
            self.issues.append('No labs associated with investigation.')

    def AssignLabTypes(self):
        """ Determine lab type (PCR, Ag, or Ab) for each associated lab."""
        pcr_flags = ['RNA', 'PCR', 'NAA', 'GENE', 'PRL SCV2']
        ag_flags = ['AG', 'ANTIGEN', 'VERITOR']
        ab_flags = ['AB', 'IGG', 'IGM', 'IGA', 'Antibod', 'T-DETECT']
        test_types = [('pcr', pcr_flags), ('antigen', ag_flags), ('antibody', ab_flags)]
        for type in test_types:
            self.labs[type[0]] = self.labs['Test Results'].apply(lambda results: any(flag in results.upper() for flag in type[1]))

    def DetermineCaseStatus(self):
        """Review lab types to determine case status.
        PCR => confirmed
        Antigen => probable
        Antibody => suspect
        """
        if any(self.labs.pcr):
            self.status = 'C'
        elif any(self.labs.antigen):
            self.status = 'P'
        elif any(self.labs.antibody):
            self.status = 'S'
        else:
            self.status = ''
            self.issues.insert(0,'**UNABLE TO DETERMINE CORRECT STATUS: CENTRAL EPI REVIEW REQUIRED**')
            self.lab_data_issues_log.append(self.ReadPatientID())

    def GetReportDate(self):
        """Find earliest report date by reviewing associated labs"""
        if self.labs['Date Received'][0] == 'Nothing found to display.':
            self.report_date = datetime(1900, 1, 1).date()
        else:
            self.labs['Date Received'] = pd.to_datetime(self.labs['Date Received'], format = '%m/%d/%Y%I:%M %p').dt.date
            self.report_date = self.labs['Date Received'].min()

    def GetCollectionDate(self):
        """Find earliest collection date by reviewing associated labs"""
        if self.labs['Date Received'][0] == 'Nothing found to display.':
            self.report_date = datetime(1900, 1, 1).date()
        else:
            # Check for any associated labs missing collection date:
            # 1. Set collection date to 01/01/2100 to avoid type errors.
            # 2. Log patient id for manual review.
            no_col_dt_labs = self.labs.loc[self.labs['Date Collected'] == 'No Date']
            if len(no_col_dt_labs) > 0:
                self.labs.loc[self.labs['Date Collected'] == 'No Date', 'Date Collected'] = '01/01/2100'
                self.issues.insert(0,'**SOME ASSOCIATED LABS MISSING COLLECTION DATE: CENTRAL EPI REVIEW REQUIRED**')
                self.lab_data_issues_log.append(self.ReadPatientID())
            self.labs['Date Collected'] = pd.to_datetime(self.labs['Date Collected'], format = '%m/%d/%Y').dt.date
            self.collection_date = self.labs['Date Collected'].min()

    def ReadAoes(self):
        """ Read AOEs from associated labs. """
        aoe_flags = {'icu_aoe':'Admitted to ICU for condition:\xa0Y'
                    ,'hcw_aoe':'Hospitalized for condition of interest:\xa0Y'
                    ,'symp_aoe':'Has symptoms for condition:\xa0Y'
                    ,'hosp_aoe':'Hospitalized for condition of interest:\xa0Y'
                    ,'cong_aoe':'Resides in a congregate care setting:\xa0Y'
                    ,'fr_aoe':'First Responder:\xa0Y'
                    ,'preg_aoe': 'Pregnancy Status:\xa0Y'}
        for aoe in aoe_flags.keys():
            self.labs[aoe] = self.labs.apply(lambda row: aoe_flags[aoe] in row['Test Results'], axis=1 )
        self.icu_aoe =  any(self.labs.icu_aoe)
        self.hcw_aoe =  any(self.labs.hcw_aoe)
        self.symp_aoe =  any(self.labs.symp_aoe)
        self.hosp_aoe =  any(self.labs.hosp_aoe)
        self.cong_aoe =  any(self.labs.cong_aoe)
        self.fr_aoe = any(self.labs.fr_aoe)
        self.preg_aoe = any(self.labs.preg_aoe)

########################### AOE Check Methods ##################################
    def CheckHospAOE(self):
        """ Ensure that if AOEs show a patient as hosptialized the investigation matches."""
        if self.hosp_aoe & (self.hospitalization_indicator != 'Yes'):
            self.issues.append('AOEs indicate that the case is hospitalized, but the investigation does not.')

    def CheckIcuAOE(self):
        """ Ensure that if AOEs show a patient as in the ICU the investigation matches."""
        if self.hospitalization_indicator == 'Yes':
            if self.icu_aoe & (self.icu_indicator != 'Yes'):
                self.issues.append('AOEs indicate that the case is in the ICU, but the investigation does not.')

    def CheckHcwAOE(self):
        """ Ensure that if AOEs show a patient is a healthcare worker the investigation matches."""
        if self.hcw_aoe & (self.healthcare_worker != 'Yes'):
            self.issues.append('AOEs indicate that the case is a healthcare worker, but the investigation does not.')

    def CheckSympAOE(self):
        """ Ensure that if AOEs show a patient is symptomatic the investigation matches."""
        if self.symp_aoe & (self.symptoms != 'Yes'):
            self.issues.append('AOEs indicate that the case is symptomatic, but the investigation does not.')

    def CheckCongAOE(self):
        """ Ensure that if AOEs show a patient lives in a congregate setting the
        investigation matches."""
        if self.symp_aoe & (self.cong_setting_indicator != 'Yes'):
            self.issues.append('AOEs indicate that the case lives in a congregate setting, but the investigation does not.')

    def CheckFirstResponderAOE(self):
        """ Ensure that if AOEs show a patient is a first responder that the
        investigation matches."""
        if self.fr_aoe & (self.first_responder != 'Yes'):
            self.issues.append('AOEs indicate that the case lives is a first responder, but the investigation does not.')

    def CheckPregnancyAOE(self):
        """ Ensure that if AOEs show a patient is pregnany that the
        investigation matches."""
        pregnant_status = self.ReadText('//*[@id="INV178"]')
        if self.preg_aoe & (pregnant_status != 'Yes'):
            self.issues.append('AOEs indicate that the case is pregnant, but the investigation does not.')
