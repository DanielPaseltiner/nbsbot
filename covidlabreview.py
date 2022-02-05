from nbsdriver import NBSdriver
import configparser
import pyodbc
import pandas as pd
from selenium.webdriver.common.by import By
from datetime import datetime
from epiweeks import Week

class COVIDlabreview(NBSdriver):
    """ A class inherits all basic NBS functionality from NBSdriver and adds
    methods for reviewing unassigned COVID labs."""

    def __init__(self, production=False):
        super(COVIDlabreview, self).__init__(production)
        self.reset()

    def reset(self):
        """ Clear values of attributes assigned during case investigation review.
        To be used on initialization and between case reviews. """

        self.now = datetime.now().date()
        self.now_str = today = self.now.strftime('%m/%d/%Y')
        self.missing_address = []
        self.issue = []
        self.possible_merges = None
        self.address_complete = None
        self.possible_hospitalization = None
        self.num_investigations = None
        self.existing_investigation_index = None
        self.vax_table = None
        self.covid_vaccinations = None
        self.fully_vaccinated = None
        self.num_doses_prior_to_onset = None
        self.last_dose_date = None
        self.current_collection_date = None

    def get_db_connection_info(self):
        """ Read information required to connect to the NBS database."""
        self.nbs_db_driver = self.config.get('NBSdb', 'driver')
        self.nbs_db_server = self.config.get('NBSdb', 'server')
        self.nbs_rdb_name = self.config.get('NBSdb', 'rdb')
        self.nbs_odse_name = self.config.get('NBSdb', 'odse')
        self.nbs_unassigned_covid_lab_table = self.config.get('NBSdb', 'unassigned_covid_lab_table')
        self.nbs_patient_list_view = self.config.get('NBSdb', 'patient_list_view')

    def get_patient_table(self):
        """ Execute a view in the nbs_odse database to return all patients in
        NBS including firt name, last name, birth date, and parent id. This data
        is then stored in a DataFrame for future use."""

        # Connect to database
        print(f'Connecting to {self.nbs_odse_name} database...')
        Connection = pyodbc.connect("Driver={" + self.nbs_db_driver + "};"
                              fr"Server={self.nbs_db_server};"
                              f"Database={self.nbs_odse_name};"
                              "Trusted_Connection=yes;")
        # Execute query and close connection
        print (f'Connected to {self.nbs_odse_name}. Executing query...')
        query = f'SELECT PERSON_PARENT_UID, UPPER(FIRST_NM) AS FIRST_NM, UPPER(LAST_NM) AS LAST_NM, BIRTH_DT FROM {self.nbs_patient_list_view} WHERE (FIRST_NM IS NOT NULL) AND (LAST_NM IS NOT NULL) AND (BIRTH_DT IS NOT NULL)'
        self.patient_list = pd.read_sql_query(query, Connection)
        self.patient_list = self.patient_list.drop_duplicates(ignore_index=True)
        Connection.close()
        print ('Data recieved and database connection closed.')

    def get_unassigned_covid_labs(self):
        """ Connect to the analyis NBS database and execute a query to return a
        list of all unassociated labs along with the data required to create
        investigations for them.
        """
        self.select_counties()
        self.select_min_delay()
        self.get_db_connection_info()
        variables = ('Lab_Local_ID'
                        ,'CAST(Lab_Rpt_Received_By_PH_Dt AS DATE) AS Lab_Rpt_Received_By_PH_Dt'
                        ,'CAST(Specimen_Coll_DT AS DATE) AS Specimen_Coll_DT'
                        ,'Perform_Facility_Name'
                        ,'UPPER(First_Name) AS First_Name'
                        ,'UPPER(Middle_Name) AS Middle_Name'
                        ,'UPPER(Last_Name) AS Last_Name'
                        ,'Patient_Local_ID'
                        ,'Current_Sex_Cd'
                        ,'CAST(Birth_Dt AS DATE) AS Birth_Dt'
                        ,'Patient_Race_Calc'
                        ,"CASE WHEN Patient_Ethnicity = '2186-5' THEN 'Hispanic or Latino' "
                        "WHEN Patient_Ethnicity = '2135-2' THEN 'Not Hispanic or Latino' "
                        "ELSE 'Unknown' END AS Patient_Ethnicity"
                        ,'Patient_Death_Ind'
                        ,'Patient_Death_Date'
                        ,'Phone_Number'
                        ,'Address_One'
                        ,'Address_Two'
                        ,'City'
                        ,'State'
                        ,'County_Desc'
                        ,'Jurisdiction_Nm'
                        ,'Perform_Facility_Name'
                        ,'EMPLOYED_IN_HEALTHCARE'
                        ,'ILLNESS_ONSET_DATE'
                        ,'PATIENT_AGE'
                        ,'PREGNANT'
                        ,'RESIDENT_CONGREGATE_SETTING'
                        ,'SYMPTOMATIC_FOR_DISEASE'
                        ,'CAST(ILLNESS_ONSET_DATE AS DATE) AS ILLNESS_ONSET_DATE'
                        ,'TestType'
                        ,'DATEDIFF(DAY, Specimen_Coll_DT, GETDATE()) AS review_delay'
                        )
        variables = ', '.join(variables)
        # If a lab is not positive an investigation should not be created for it.
        # All cases with AOEs indicating hospitalization, or death should be assigned out for investigation. These cases should not be opened and closed.
        where = "WHERE (Result_Category = 'Positive') AND (State = 'ME') AND (TestType IN ('PCR', 'Antigen')) AND (HOSPITALIZED IS NULL OR UPPER(HOSPITALIZED) NOT LIKE 'Y%') AND (ICU IS NULL OR UPPER(ICU) NOT LIKE 'Y%') AND (Patient_Death_Ind IS NULL OR UPPER(Patient_Death_Ind) NOT LIKE 'Y%')"
        if self.min_delay:
            where = where + f'AND (DATEDIFF(DAY, Lab_Rpt_Received_By_PH_Dt ,GETDATE())) >= {self.min_delay}'
        order_by = 'ORDER BY Lab_Rpt_Received_By_PH_Dt'
        # Construct Query
        query = " ".join(['SELECT', variables, 'FROM', self.nbs_unassigned_covid_lab_table, where, order_by] )
        # Connect to database
        print(f'Connecting to {self.nbs_rdb_name} database...')
        Connection = pyodbc.connect("Driver={" + self.nbs_db_driver + "};"
                              fr"Server={self.nbs_db_server};"
                              f"Database={self.nbs_rdb_name};"
                              "Trusted_Connection=yes;")
        # Execute query and close connection
        print (f'Connected to {self.nbs_rdb_name}. Executing query...')
        self.unassociated_labs = pd.read_sql_query(query, Connection)
        self.unassociated_labs.County_Desc = self.unassociated_labs.County_Desc.str.replace(' County', '')
        Connection.close()
        if self.counties:
            self.unassociated_labs = self.unassociated_labs[self.unassociated_labs.Jurisdiction_Nm.isin(self.counties)].reset_index(drop=True)
        print ('Data recieved and database connection closed.')

    def select_counties(self):
        """A method to prompt the user to specify which counties unassociated labs should be review from."""
        maine_counties = ('Androscoggin'
                        ,'Aroostook'
                        ,'Cumberland'
                        ,'Franklin'
                        ,'Hancock'
                        ,'Kennebec'
                        ,'Knox'
                        ,'Lincoln'
                        ,'Oxford'
                        ,'Penobscot'
                        ,'Piscataquis'
                        ,'Sagadahoc'
                        ,'Somerset'
                        ,'Waldo'
                        ,'Washington'
                        ,'York')
        for idx, county in enumerate(maine_counties):
            print(f'{idx}: {county}')
        self.counties = input('COUNTY SLECTION:\n'
                                'Choose the counties from which to review unassocated labs.\n'
                                'Make your selection by entering the row numbers of the desired counties separated by commas.\n'
                                'For example, to select Cumberland and York counties enter "2,15".\n'
                                'Press enter to skip this step and review unassociated labs from all counties.\n'
                                '>>>')
        if self.counties:
            self.counties = self.counties.split(',')
            self.counties = [maine_counties[int(county)]for county in self.counties]

    def select_min_delay(self):
        """A method to prompt the user to specify the minimum delay in reviewing unassociated labs.
        If 3 is select then NBSbot will only review unassocated labs that were reported 3 or more days ago."""

        self.min_delay = input('\nSET MINIMUM REVIEW DELAY:\n'
                                'Enter the minimum integer number of days between the earliest date a lab was reported and today that unassociated labs should be reviewed from.\n'
                                'Press enter "0" or simply press enter to skip this step and review all unassociated labs regardless of reporting age.\n'
                                '>>>')
        if not self.min_delay:
            self.min_delay = 0
        else:
            self.min_delay = int(self.min_delay)

    def check_for_possible_merges(self, fname, lname, dob):
        """ Given a patient's first name, last name, and dob search for possible
        matches amoung all patients in NBS."""

        matches = self.patient_list.loc[(self.patient_list.FIRST_NM.str[:2] == fname[:2]) & (self.patient_list.LAST_NM.str[:2] == lname[:2]) & (self.patient_list.BIRTH_DT == dob)]
        unique_profiles = matches.PERSON_PARENT_UID.unique()
        if len(unique_profiles) >= 2:
            self.possible_merges = True
        else:
            self.possible_merges = False

    def check_for_existing_investigation(self, collection_date):
        """ Review the Investigations table in the Events tab of a patient profile
        to determine if the case already has an existing investigation. """
        investigation_table = self.read_investigation_table()
        investigation_table['days_prior'] = investigation_table['Start Date'].apply(lambda x: (x-collection_date).days)
        existing_investgations = investigation_table[(investigation_table.days_prior <= 90)
                                & (investigation_table.condition == '2019 Novel Coronavirus (2019-nCoV)')]
        self.num_investigations = len(existing_investgations)
        if self.num_investigations >= 1:
            self.existing_investigation_index = existing_investgations.index.tolist()[0]
            self.existing_investigation_index = str(int(self.existing_investigation_index) + 1)
        else:
            self.existing_investigation_index = None

    def check_patient_hospitalization_status(self):
        """ Check Patient Status at Specimen Collection from inside a lab report.
        Occasionally there are cases that indicate a status of 'inpatient' without an AOE inidicating a hospitalization.
        In this case the bot will not open and closed a case, but instead leave the lab for human review."""
        patient_status = self.ReadText(self, 'xpath').upper()
        if patient_status in ['HOSPITALIZED', 'INPATIENT']:
            self.possible_hospitalization = True
        else:
            self.possible_hospitalization = False

    def create_investigation(self):
        """Create a new investigation from within a lab report when one does not already exist ."""
        create_investigation_button_path = '//*[@id="doc3"]/div[2]/table/tbody/tr/td[2]/input[1]'
        self.find_element(By.XPATH, create_investigation_button_path).click()
        select_condition_field_path = '//*[@id="ccd_ac_table"]/tbody/tr[1]/td/input'
        condition = '2019 Novel Coronavirus (2019-nCoV)'
        self.find_element(By.XPATH, select_condition_field_path).send_keys(condition)
        self.click_submit()

    def go_to_existing_investigation(self):
        """Navigate to an existing investigation that a lab in question should be associated with."""
        if self.num_investigations > 1:
            existing_investigation_path = f'/html/body/div[2]/form/div/table[4]/tbody/tr[2]/td/div[2]/table/tbody/tr/td/div[1]/div[3]/div/table/tbody/tr[2]/td/table/tbody/tr[{self.existing_investigation_index}]/td[1]/a'
        else:
            existing_investigation_path = f'/html/body/div[2]/form/div/table[4]/tbody/tr[2]/td/div[2]/table/tbody/tr/td/div[1]/div[3]/div/table/tbody/tr[2]/td/table/tbody/tr/td[1]/a'
        self.find_element(By.XPATH, existing_investigation_path).click()

    def associate_lab_with_investigation(self, lab_id):
        """Associate a lab with an existing investigation when one for the case has already been started."""
        lab_report_table_path = '//*[@id="lablist"]'
        lab_report_table = self.ReadTableToDF(lab_report_table_path)
        if len(lab_report_table) > 1:
            lab_row_index = lab_report_table[lab_report_table['Event ID'] == lab_id].index.tolist()[0]
            lab_row_index = str(int(lab_row_index) + 1)
            lab_path = f'/html/body/div[2]/div/form/div/div/div/table[2]/tbody/tr/td/table/tbody/tr[{lab_row_index}]/td[1]/div/input'
        self.find_element(By.XPATH,lab_path).click()

    def go_to_lab(self, lab_id):
        """ Navigate to a lab from a patient profile navigate to a lab. """
        lab_report_table_path = '//*[@id="lab1"]'
        lab_report_table = self.ReadTableToDF(lab_report_table_path)
        if len(lab_report_table) > 1:
            lab_row_index = lab_report_table[lab_report_table['Event ID'] == lab_id].index.tolist()[0]
            lab_row_index = str(int(lab_row_index) + 1)
            lab_path = f'/html/body/div[2]/div/form/div/div/div/table[2]/tbody/tr/td/table/tbody/tr[{lab_row_index}]/td[1]/div/input'
        else:
            lab_path = '/html/body/div[2]/form/div/table[4]/tbody/tr[2]/td/div[2]/table/tbody/tr/td/div[1]/div[5]/div/table/tbody/tr/td/table/tbody/tr/td[1]/a'
        self.find_element(By.XPATH, lab_path).click()

    def query_immpact(self):
        """ Click the query registry button, submit the query to immpact, and read the results into a DataFrame."""
        query_registry_button = '//*[@id="events3"]/tbody/tr/td/div/input[1]'
        self.find_element(By.XPATH, query_registry_button).click()
        self.switch_to_secondary_window()
        submit_query = '//*[@id="doc4"]/div[2]/input[1]'
        self.find_element(By.XPATH, submit_query).click()
        self.switch_to_secondary_window()
        results_table_path = '//*[@id="section1"]/div/table'
        results_table = self.ReadTableToDF(results_table_path)
        if len(results_table) == 1:
            record_path = '//*[@id="parent"]/tbody/tr/td[1]/a'
            self.find_element(By.XPATH, record_path).click()
            self.switch_to_secondary_window()
            vax_table_path = '//*[@id="section1"]/div/table[2]'
            self.vax_table = self.ReadTableToDF(vax_table_path)
        else:
            print('Immpact returned more than one patient as a possible. Unable to proceed with the automated query.')

    def id_covid_vaccinations(self):
        """Identify COVID vaccines by their specific brand."""
        covid_vax_dict = {'Pfizer':'COVID-19, mRNA, LNP-S, PF, 30 mcg/0.3 mL dose','Moderna':'COVID-19, mRNA, LNP-S, PF, 100 mcg/0.5 mL dose', 'JJ':'COVID-19 vaccine, vector-nr, rS-Ad26, PF, 0.5 mL'}
        for key in covid_vax_dict.keys():
            self.vax_table[key] = self.vax_table['Vaccine Administered'].apply(lambda x: covid_vax_dict[key] in x)
        self.covid_vaccinations = self.vax_table.loc[self.vax_table.Pfizer | self.vax_table.Moderna | self.vax_table.JJ]

    def import_covid_vaccinations(self):
        """ Select all COVID vaccinations in the list returned by Immpact and import them."""
        covid_vax_indexes = self.covid_vaccinations.index
        num_covid_vaccinations = len(covid_vax_indexes)
        if num_covid_vaccinations > 0:
            if (len(vax_table) == 1) & (len(covid_vax_indexes) == 1):
                select_path = '/html/body/form/div[2]/div/div[4]/div/table[2]/tbody/tr/td/table/tbody/tr/td[1]/input'
                self.find_element(By.XPATH, select_path).click()
            else:
                for idx in covid_vax_indexes:
                    select_path = f'/html/body/form/div[2]/div/div[4]/div/table[2]/tbody/tr/td/table/tbody/tr[{idx}]/td[1]/input'
                    self.find_element(By.XPATH, select_path).click()
            import_path = '/html/body/form/div[2]/div/div[6]/input[1]'
            self.find_element(By.XPATH, import_path).click()

    def determine_vaccination_status(self, collection_date):
        """ Determine vaccination status at time of illness and other required vaccination data points."""
        covid_vaccinations_prior_to_onset = self.covid_vaccinations.loc[self.covid_vaccinations['Date Administered'] < collection_date ]
        self.num_doses_prior_to_onset = len(covid_vaccinations_prior_to_onset)
        self.last_dose_date = covid_vaccinations_prior_to_onset['Date Administered'].max()
        complete_vaccinations = self.covid_vaccinations.loc[vax_table['Date Administered'] <= (collection_date - datetime.timedelta(days=14))]
        if len(complete_vaccinations.loc[complete_vaccinations.Pfizer]) >= 2:
            self.fully_vaccinated = True
        elif len(complete_vaccinations.loc[complete_vaccinations.Moderna]) >= 2:
            self.fully_vaccinated = True
        elif len(complete_vaccinations.loc[complete_vaccinations.JJ]) >= 1:
            self.fully_vaccinated = True
        else:
            self.full_vaccinated = False

    def check_address(self):
        """ Check if city, zip code, county, and country fields are complete."""
        address_paths = {'City':'//*[@id="DEM161"]'
                        ,'Zip':'//*[@id="DEM163"]'
                        ,'County':'//*[@id="NBS_UI_15"]/tbody/tr[6]/td[2]/input'
                        ,'Country':'//*[@id="NBS_UI_15"]/tbody/tr[7]/td[2]/input'}
        self.issues = []
        for addr_part, path in address_paths.items():
            self.CheckForValue(path, f'{addr_part} is blank.')
        if self.issues:
            self.address_complete = False
        else:
            self.address_complete = True

    def check_ethnicity(self):
        """ Check if ethnicity is completed and if not set the values to unknown."""
        ethnicity_path = '//*[@id="NBS_UI_9"]/tbody/tr[1]/td[2]/input'
        ethnicity = self.ReadText(ethnicity_path)
        if not ethnicity:
            self.find_element(By.XPATH, ethnicity_path).send_keys('unknown')

    def clear_ambiguous_race_answers(self):
        """ Ensure all ambiguous race answers (refused to answer, not answered, and unknown) are not selected."""
        ambiguous_answer_paths = ['//*[@id="NBS_UI_9"]/tbody/tr[10]/td[2]/input'
                                 ,'//*[@id="NBS_UI_9"]/tbody/tr[11]/td[2]/input'
                                 ,'//*[@id="NBS_UI_9"]/tbody/tr[12]/td[2]/input']
        for path in ambiguous_answer_paths:
            self.unselect_checkbox(path)

    def check_race(self):
        unambiguous_race_paths = ['//*[@id="NBS_UI_9"]/tbody/tr[2]/td[2]/input'
                                 ,'//*[@id="NBS_UI_9"]/tbody/tr[3]/td[2]/input'
                                 ,'//*[@id="NBS_UI_9"]/tbody/tr[4]/td[2]/input'
                                 ,'//*[@id="NBS_UI_9"]/tbody/tr[5]/td[2]/input'
                                 ,'//*[@id="NBS_UI_9"]/tbody/tr[6]/td[2]/input']
        other_race_path = '//*[@id="NBS_UI_9"]/tbody/tr[7]/td[2]/input'
        unknown_race_path = '//*[@id="NBS_UI_9"]/tbody/tr[12]/td[2]/input'
        for path in unambiguous_race_paths:
            if self.find_element(By.XPATH, path).is_selected():
                unambiguous_race = True
                break
            else:
                unambiguous_race = False
        self.clear_ambiguous_race_answers()
        if unambiguous_race:
            self.unselect_checkbox(other_race_path)
        elif self.find_element(By.XPATH, other_race_path).is_selected():
            self.select_checkbox(other_race_path)
        else:
            self.find_element(By.XPATH, unknown_race_path).click()

    def set_investigation_start_date(self):
        """ Set investigation start date to today."""
        start_date_path = '//*[@id="INV147"]'
        self.find_element(By.XPATH, start_date_path).send_keys(self.now_str)

    def set_investigation_status_closed(self):
        """Set investigation status to closed."""
        investigation_status_path = '//*[@id="NBS_UI_19"]/tbody/tr[4]/td[2]/input'
        self.find_element(By.XPATH, investigation_status_path).send_keys('Closed')

    def set_state_case_id(self):
        """ Set the State Case ID to the NBS patient ID."""
        state_case_id_path = '//*[@id="INV173"]'
        patient_id = self.ReadPatientID()
        self.find_element(By.XPATH, state_case_id_path).send_keys(patient_id)

    def set_county_and_state_report_dates(self, report_to_ph_date):
        """ Set Earliest Date Reported to County and Earliest Date Reported to
        State based on Lab_Rpt_Received_By_PH_Dt. This method should only be used
        when creating new investigations and not when associating additional labs
        with an existing investigation."""
        report_date_paths = ['//*[@id="INV120"]', '//*[@id="INV121"]']
        report_to_ph_date = report_to_ph_date.strftime('%m/%d/%Y')
        for path in report_date_paths:
            self.find_element(By.XPATH, path).send_keys(report_to_ph_date)

    def set_performing_lab(self, performing_lab):
        """ Set performing laboratory name based on lab report."""
        performing_lab_path = '//*[@id="ME6105"]'
        self.find_element(By.XPATH, performing_lab_path).send_keys(performing_lab)

    def set_earliest_positive_collection_date(self, lab_collection_date):
        """ Read the earliest positive speciment collection date field. If there
        is a date present and it is prior to the collection of the current lab do
        nothing. In the event that the field is blank or the collection of the
        current lab is prior to the current value of the field, set the value to
        the collection date of the current lab. This additional check allows this
        method to be used when creating investigations or associating labs with
        existing investigations."""

        colletion_date_path = '//*[@id="NBS550"]'
        self.current_collection_date = self.ReadDate(collection_date_path)
        if not current_collection_date:
            self.current_collection_date = lab_collection_date
            lab_collection_date = lab_collection_date.strftime('%m/%d/%Y')
            self.find_element(By.XPATH, colletion_date_path).send_keys(lab_collection_date)
        elif lab_collection_date <= current_collection_date:
            self.current_collection_date = lab_collection_date
            lab_collection_date = lab_collection_date.strftime('%m/%d/%Y')
            self.find_element(By.XPATH, colletion_date_path).send_keys(lab_collection_date)

    def set_case_status(self, status):
        """ Set all three fields related to case status based on the provided status."""
        current_status_path = '//*[@id="NBS_UI_GA21015"]/tbody/tr[3]/td[2]/input'
        probable_reason_path = '//*[@id="NBS_UI_GA21015"]/tbody/tr[4]/td[2]/input'
        case_status_path = '//*[@id="NBS_UI_2"]/tbody/tr[5]/td[2]/input'

        if status == 'Confirmed':
            current_status = 'Laboratory-confirmed case'
            probable_reason = ''
        elif status == 'Probable':
            current_status = 'Probable Case'
            probable_reason == 'Meets Presump Lab and Clinical or Epi'
        self.find_element(By.XPATH, current_status_path).send_keys(current_status)
        self.find_element(By.XPATH, probable_reason_path).send_keys(probable_reason)
        self.find_element(By.XPATH, case_status_path).send_keys(status)

    def review_case_status(self, lab_type):
        """ Review current case status and current lab type. Then set case status
        accordingly. This method can be used for creating investigations or
        associating additional labs with existing investigations."""
        case_status_path = '//*[@id="NBS_UI_2"]/tbody/tr[5]/td[2]/input'
        currect_case_status = self.ReadText(case_status_path)
        if lab_type == 'PCR':
            self.set_case_status('Confirmed')
        elif not current_case_status:
            self.set_case_status('Probable')

    def update_aoe(self, aoe_path, lab_aoe):
        """ Update a specific AOE associated investigation field by considering
        its current value and the value in the current lab. An affirmative
        response in either the investigation or the lab takes precedence, followed
        by negative, unknown, and null responses respectively."""
          investigation_aoe = self.ReadText(case_status_path)
          if (investigation_aoe == 'Yes') | (lab_aoe[0].upper() == 'Y'):
              self.find_element(By.XPATH, aoe_path).send_keys('Yes')
          elif (investigation_aoe == 'No') | (lab_aoe[0].upper() == 'N'):
              self.find_element(By.XPATH, aoe_path).send_keys('No')
          elif (investigation_aoe == 'Unknown') | (lab_aoe[0].upper() == 'U'):
              self.find_element(By.XPATH, aoe_path).send_keys('Unknown')

    def update_all_aoes(self, hosp_aoe, cong_aoe, responder_aoe, hcw_aoe, pregnant_aoe):
        """ For every AOE except symptom status apply the update_aoe() method."""
        aoe_dictionary = {'//*[@id="NBS_UI_NBS_INV_GENV2_UI_3"]/tbody/tr[1]/td[2]/input' : hosp_aoe
                         ,'//*[@id="ME59136"]/tbody/tr[1]/td[2]/input' : cong_aoe
                         ,'//*[@id="ME59137"]/tbody/tr[1]/td[2]/input' : responder_aoe
                         ,'//*[@id="UI_ME59106"]/tbody/tr[1]/td[2]/input' : hcw_aoe
                         ,'//*[@id="ME58100"]/tbody/tr[1]/td[2]/input' : pregnant_aoe}
        for aoe_path, aoe_valye in aoe_dictionary.items():
            self.update_aoe(aoe_path, aoe_value)

    def update_symptom_aoe(self, lab_symptom_aoe, lab_onset_date):
        """ Update symptom status based on values in an investigation and values
        reported in the current lab."""
        symptom_path = '//*[@id="NBS_UI_GA21003"]/tbody/tr[3]/td[2]/input'
        onset_date_path = '//*[@id="INV137"]'
        if lab_onset_date:
            lab_symptom_aoe = 'Yes'
        investigation_symtom_status = self.ReadText(symptom_path)
        if investigation_symptom_status == 'Yes':
            investigation_onset_date = self.ReadDate(onsed_date_path)
            if (lab_onset_date) & (investigation_onset_date):
                if lab_onset_date < investigation_onset_date:
                    lab_onset_date = lab_onset_date.strftime('%m/%d/%Y')
                    self.find_element(By.XPATH, onset_date_path).send_keys(lab_onset_date)
        elif lab_symptom_aoe[0].upper() == 'Y':
            self.find_element(By.XPATH, symptom_path).send_keys('Yes')
            lab_onset_date = lab_onset_date.strftime('%m/%d/%Y')
            self.find_element(By.XPATH, onset_date_path).send_keys(lab_onset_date)
        elif (investigation_symtom_status == 'No') | (lab_symptom_aoe[0].upper() == 'N')::
            self.find_element(By.XPATH, symptom_path).send_keys('No')
        elif (investigation_symtom_status == 'Unknown') | (lab_symptom_aoe[0].upper() == 'U')::
            self.find_element(By.XPATH, symptom_path).send_keys('Unknown')

    def set_confirmation_date(self):
        """Set confirmation date to today when creating a new investigation."""
        confirmation_date_path = '//*[@id="INV162"]'
        self.find_element(By.XPATH, confirmation_date_path).send_keys(self.now_str)

    def set_closed_date(self):
        """Set investigation closed date to today when creating a new investigation."""
        closed_date_path = '//*[@id="ME11163"]'
        self.find_element(By.XPATH, closed_date_path).send_keys(self.now_str)

    def set_vaccination_fields(self):
        """Fill in all vaccination specific fields on the COVID tab after querying
        Immpact when creating a new investigation."""
        vaccinated_path = '//*[@id="ME10064101"]/tbody/tr[1]/td[2]/input'
        num_dose_path = '//*[@id="VAC140"]'
        last_dose_path = '//*[@id="VAC142"]'
        fully_vax_path = '//*[@id="ME10064101"]/tbody/tr[4]/td[2]/input'
        immpact_query_path = '//*[@id="ME10064101"]/tbody/tr[9]/td[2]/input'
        if len(self.covid_vaccinations) > 0:
            self.find_element(By.XPATH, vaccinated_path).send_keys('Yes')
            num_doses = str(self.num_doses_prior_to_onset)
            self.find_element(By.XPATH, num_dose_path).send_keys(num_doses)
            last_dose_date = self.last_dose_date..strftime('%m/%d/%Y')
            self.find_element(By.XPATH, last_dose_path).send_keys(last_dose_date)
            if self.fully_vaccinated:
                self.find_element(By.XPATH, fully_vax_path).send_keys('Yes')
        self.find_element(By.XPATH, immpact_query_path).send_keys('Yes')

    def set_lab_testing_performed(self):
        """Set the laboratory testing performed question to 'Yes' when creating a new investigation."""
        lab_testing_path = '//*[@id="ME58101"]/tbody/tr/td[2]/input'
        self.find_element(By.XPATH, lab_testing_path).send_keys('Yes')

    def set_mmwr(self):
        """Set the values of the MMWR week and year correctly based on first positive speciment collection date."""
        week_path = '//*[@id="INV165"]'
        year_path = '//*[@id="INV166"]'
        mmwr_date = Week.fromdate(self.current_collection_date)
        week = str(mmwr_date.week)
        year = str(mmwr_date.year)
        self.find_element(By.XPATH, week_path).send_keys(week)
        self.find_element(By.XPATH, year_path).send_keys(year)


if __name__ == "__main__":
    NBS = COVIDlabreview(production=True)
    NBS.get_unassigned_covid_labs()
    NBS.get_patient_table()
