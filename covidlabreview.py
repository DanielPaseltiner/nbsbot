from nbsdriver import NBSdriver
import configparser
import pyodbc
import pandas as pd

class COVIDlabreview(NBSdriver):
    """ A class inherits all basic NBS functionality from NBSdriver and adds
    methods for reviewing unassigned COVID labs."""

    def __init__(self, production=False):
        super(COVIDlabreview, self).__init__(production)
        self.read_config()

    def get_db_connection_info(self):
        """ Read information required to connect to the NBS database."""
        self.nbs_db_driver = self.config.get('NBSdb', 'driver')
        self.nbs_db_server = self.config.get('NBSdb', 'server')
        self.nbs_db_name = self.config.get('NBSdb', 'database')
        self.nbs_unassigned_covid_lab_table = self.config.get('NBSdb', 'unassigned_covid_lab_table')

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
                        ,'Perform_Facility_Name'
                        ,'First_Name'
                        ,'Middle_Name'
                        ,'Last_Name'
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
                        ,'CASE WHEN (County_Desc IS NOT NULL) THEN County_Desc '
                        'WHEN (Ordering_Provider_County_Desc IS NOT NULL) THEN Ordering_Provider_County_Desc '
                        'WHEN (Ordering_Facility_County_Desc IS NOT NULL) THEN Ordering_Facility_County_Desc '
                        'WHEN (Reporting_Facility_County_Desc IS NOT NULL) THEN Reporting_Facility_County_Desc '
                        'END AS county'
                        ,'Reporting_Facility_Name'
                        ,'EMPLOYED_IN_HEALTHCARE'
                        ,'ILLNESS_ONSET_DATE'
                        ,'PATIENT_AGE'
                        ,'PREGNANT'
                        ,'RESIDENT_CONGREGATE_SETTING'
                        ,'SYMPTOMATIC_FOR_DISEASE'
                        ,'TestType'
                        ,'DATEDIFF(DAY, Lab_Rpt_Received_By_PH_Dt, GETDATE()) AS review_delay'
                        )
        variables = ', '.join(variables)
        # If a lab is not positive an investigation should not be created for it.
        # All cases with AOEs indicating hospitalization, or death should be assigned out for investigation. These cases should not be opened and closed.
        where = "WHERE (Result_Category = 'Positive') AND (HOSPITALIZED IS NULL OR UPPER(HOSPITALIZED) NOT LIKE 'Y%') AND (ICU IS NULL OR UPPER(ICU) NOT LIKE 'Y%') AND (Patient_Death_Ind IS NULL OR UPPER(Patient_Death_Ind) NOT LIKE 'Y%')"
        if self.min_delay:
            where = where + f'AND (DATEDIFF(DAY, Lab_Rpt_Received_By_PH_Dt ,GETDATE())) >= {self.min_delay}'
        order_by = 'ORDER BY Lab_Rpt_Received_By_PH_Dt'
        # Construct Query
        query = " ".join(['SELECT', variables, 'FROM', self.nbs_unassigned_covid_lab_table, where, order_by] )
        # Connect to database
        print(f'Connecting to {self.nbs_db_name} database...')
        Connection = pyodbc.connect("Driver={SQL Server Native Client 11.0};"
                              r"Server=sql-dhhs-nbs-prod.som.w2k.state.me.us\NBS;"
                              "Database=rdb;"
                              "Trusted_Connection=yes;")
        # Execute query and close connection
        print (f'Connected to {self.nbs_db_name}. Executing query...')
        self.unassociated_labs = pd.read_sql_query(query, Connection)
        self.unassociated_labs.county = self.unassociated_labs.county.str.replace(' County', '')
        Connection.close()
        if self.counties:
            self.unassociated_labs = self.unassociated_labs[self.unassociated_labs.county.isin(self.counties)].reset_index(drop=True)
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

if __name__ == "__main__":
    NBS = COVIDlabreview(production=True)
    NBS.get_unassigned_covid_labs()
    NBS.unassociated_labs
