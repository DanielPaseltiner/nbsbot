from nbsdriver import NBSdriver
import configparser
import pyodbc
import pandas as pd

class COVIDlabreview(NBSdriver):
    """ A class inherits all basic NBS functionality from NBSdriver and adds
    methods for reviewing unassigned COVID labs."""

    def __init__(self, production=False):
        super(COVIDlabreview, self).__init__(production)

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
                        ,'Reporting_Facility_Name'
                        ,'EMPLOYED_IN_HEALTHCARE'
                        ,'ILLNESS_ONSET_DATE'
                        ,'PATIENT_AGE'
                        ,'PREGNANT'
                        ,'RESIDENT_CONGREGATE_SETTING'
                        ,'SYMPTOMATIC_FOR_DISEASE'
                        ,'TestType'
                        ,'DATEDIFF(DAY, Specimen_Coll_DT, GETDATE()) AS review_delay'
                        )
        variables = ', '.join(variables)
        # If a lab is not positive an investigation should not be created for it.
        # All cases with AOEs indicating hospitalization, or death should be assigned out for investigation. These cases should not be opened and closed.
        where = "WHERE (Result_Category = 'Positive') AND (TestType IN ('PCR', 'Antigen')) AND (HOSPITALIZED IS NULL OR UPPER(HOSPITALIZED) NOT LIKE 'Y%') AND (ICU IS NULL OR UPPER(ICU) NOT LIKE 'Y%') AND (Patient_Death_Ind IS NULL OR UPPER(Patient_Death_Ind) NOT LIKE 'Y%')"
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
        """ Given a patient's first name, last name, and dob search for possible matches amoung all patients in NBS."""

        self.matches = self.patient_list.loc[(self.patient_list.FIRST_NM.str[:2] == fname[:2]) & (self.patient_list.LAST_NM.str[:2] == lname[:2]) & (self.patient_list.BIRTH_DT == dob)]
        self.unique_profiles = self.matches.PERSON_PARENT_UID.unique()
        if len(self.unique_profiles) >= 2:
            self.possible_merges = True
        else:
            self.possible_merges = False

if __name__ == "__main__":
    NBS = COVIDlabreview(production=True)
    NBS.get_unassigned_covid_labs()
    NBS.get_patient_table()
