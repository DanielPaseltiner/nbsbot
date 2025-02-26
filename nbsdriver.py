'''
NOTE: deprecated
The code block below has been commented out, because I kept getting permission issues with the chrome driver
but this solves it, since there's a chrome driver being used within the directory

from selenium import webdriver
import os
driver=webdriver.Chrome()

'''
'''from selenium import webdriver
from selenium.webdriver.chrome.service import Service'''

# initialize chromedriver
'''chrome_driver_path = "./chromedriver.exe"  # Replace with your custom path
service = Service(chrome_driver_path)
driver = webdriver.Chrome(service=service)'''

from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
chromedriverpath=ChromeDriverManager().install()
print(f"chromedriverpath: {chromedriverpath}")




from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from datetime import datetime
from bs4 import BeautifulSoup
import pandas as pd
import sys
import win32com.client as win32
import getpass
from pathlib import Path
from shutil import rmtree
import time
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import ElementClickInterceptedException
from selenium.common.exceptions import NoAlertPresentException
import configparser
import smtplib
from email.message import EmailMessage
from selenium.webdriver.common.by import By
from geopy.geocoders import Nominatim
from usps import USPSApi, Address
import json
from io import StringIO



class NBSdriver(webdriver.Chrome):
    """] A class to provide basic functionality in NBS via Selenium. """
    def __init__(self, production=False):
        self.production = production
        self.read_config()
        self.get_email_info()
        self.get_usps_user_id()
        if self.production:
            self.site = 'https://nbs.iphis.maine.gov/'
        else:
            self.site = 'https://nbstest.state.me.us/'

        self.options = webdriver.ChromeOptions()
        self.options.add_argument('log-level=3')
        self.options.add_argument('--ignore-ssl-errors=yes')
        self.options.add_argument('--ignore-certificate-errors')
        super(NBSdriver, self).__init__(options = self.options)
        self.issues = []
        self.num_attempts = 3
        self.queue_loaded = None
        self.wait_before_timeout = 30
        self.sleep_duration = 3300 #Value in seconds




########################### NBS Navigation Methods ############################
    def get_credentials(self):
        """ A method to prompt user to provide a valid username and RSA token
        to log in to NBS. Must """
        self.username = input('Enter your SOM username ("first_name.last_name"):')
        self.passcode = input('Enter your RSA passcode:')

    def set_credentials(self, username, passcode):
        """ A method to prompt user to provide a valid username and RSA token
        to log in to NBS. Must """
        self.username = username
        self.passcode = passcode

    def log_in(self):
        """ Log in to NBS. """
        self.get(self.site)
        print('passed')
        self.switch_to.frame("contentFrame")
        self.find_element(By.ID, "username").send_keys(self.username) #find_element_by_id() has been deprecated
        self.find_element(By.ID, 'passcode').send_keys(self.passcode)
        WebDriverWait(self,self.wait_before_timeout).until(EC.element_to_be_clickable((By.XPATH, '/html/body/div[2]/p[2]/input[1]')))
        self.find_element(By.XPATH,'/html/body/div[2]/p[2]/input[1]').click()
        time.sleep(3) #wait for the page to load, I'm not sure why the following wait to be clickable does not handle this, but this fixed the error
        #print(str(self.current_url))
        print(self.page_source) #for some reason removing this makes nbsbot unable to log in to nbs
        WebDriverWait(self,self.wait_before_timeout).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="bea-portal-window-content-4"]/tr/td/h2[4]/font/a'))) #switch to element_to_be_clickable
        self.find_element(By.XPATH,'//*[@id="bea-portal-window-content-4"]/tr/td/h2[4]/font/a').click()
    def go_to_id(self, id):
        """ Navigate to specific patient by NBS ID from Home. """
        self.find_element(By.XPATH,'//*[@id="DEM229"]').send_keys(id)
        self.find_element(By.XPATH,'//*[@id="patientSearchByDetails"]/table[2]/tbody/tr[8]/td[2]/input[1]').click()
        search_result_path = '//*[@id="searchResultsTable"]/tbody/tr/td[1]/a'
        WebDriverWait(self,self.wait_before_timeout).until(EC.presence_of_element_located((By.XPATH, search_result_path)))
        self.find_element(By.XPATH, search_result_path).click()

    def clean_patient_id(self, patient_id):
        """Remove the leading and trailing characters from local patient
        ids to leave an id that is searchable in through the front end of NBS."""
        if patient_id[0:4] == 'PSN1':
            patient_id = patient_id[4:len(patient_id)-4]
        elif patient_id[0:4] == 'PSN2':
            patient_id = '1' + patient_id[4:len(patient_id)-4]
        return patient_id

    def go_to_summary(self):
        """ Within a patient profile navigate to the Summary tab."""
        self.find_element(By.XPATH,'//*[@id="tabs0head0"]').click()

    def go_to_events(self):
        """ Within patient profile navigate to the Events tab. """
        events_path = '//*[@id="tabs0head1"]'
        try:
            WebDriverWait(self,self.wait_before_timeout).until(EC.presence_of_element_located((By.XPATH, events_path)))
            self.find_element(By.XPATH, events_path).click()
            error_encountered = False
        except TimeoutException:
            error_encountered = True
        return error_encountered

    def go_to_demographics(self):
        """ Within a patient profile navigate to the Demographics tab."""
        demographics_path = '//*[@id="tabs0head2"]'
        WebDriverWait(self,self.wait_before_timeout).until(EC.presence_of_element_located((By.XPATH, demographics_path)))
        self.find_element(By.XPATH,'//*[@id="tabs0head2"]').click()

    def go_to_home(self):
        """ Go to NBS Home page. """
        #xpath = '//*[@id="bd"]/table[1]/tbody/tr/td[1]/table/tbody/tr/td[1]/a'
        partial_link = 'Home'
        for attempt in range(self.num_attempts):
            try:
                #WebDriverWait(self,self.wait_before_timeout).until(EC.presence_of_element_located((By.XPATH, xpath)))
                #self.find_element(By.XPATH, xpath).click()
                WebDriverWait(self,self.wait_before_timeout).until(EC.presence_of_element_located((By.PARTIAL_LINK_TEXT, partial_link)))
                self.find_element(By.PARTIAL_LINK_TEXT, partial_link).click()
                self.home_loaded = True
                break
            except TimeoutException:
                self.home_loaded = False
        if not self.home_loaded:
            sys.exit(print(f"Made {self.num_attempts} unsuccessful attempts to load Home page. A persistent issue with NBS was encountered."))

    def GoToApprovalQueue(self):
        """ Navigate to approval queue from Home page. """
        partial_link = 'Approval Queue for Initial Notifications'
        try:
            WebDriverWait(self,self.wait_before_timeout).until(EC.presence_of_element_located((By.PARTIAL_LINK_TEXT, partial_link)))
            self.find_element(By.PARTIAL_LINK_TEXT, partial_link).click()
        except TimeoutException:
            self.HandleBadQueueReturn()

    def ReturnApprovalQueue(self):
        """ Return to Approval Queue from an investigation initally accessed from the queue. """
        xpath = '//*[@id="bd"]/div[1]/a'
        try:
            WebDriverWait(self,self.wait_before_timeout).until(EC.presence_of_element_located((By.XPATH, xpath)))
            self.find_element(By.XPATH, xpath).click()
        except TimeoutException:
            self.HandleBadQueueReturn()

    def SortApprovalQueue(self):
        """ Sort approval queue so that case are listed chronologically by
        notification creation date and in reverse alpha order so that
        "2019 Novel..." is at the top. """
        clear_filter_path = '//*[@id="removeFilters"]/a/font'
        submit_date_path = '//*[@id="parent"]/thead/tr/th[3]/a'
        condition_path = '//*[@id="parent"]/thead/tr/th[8]/a'
        description_path = '//html/body/div[2]/form/div/table[2]/tbody/tr/td/table/thead/tr/th[8]/img'
        clear_checkbox_path = '/html/body/div[2]/form/div/table[2]/tbody/tr/td/table/thead/tr/th[8]/div/label[2]/input'
        try:
            # Clear all filters
            WebDriverWait(self,self.wait_before_timeout).until(EC.element_to_be_clickable((By.XPATH, clear_filter_path)))
            self.find_element(By.XPATH, clear_filter_path).click()
            # The logic for this is somewhat weird but here is my understanding of what happens.
            # If we have anything in the queue that isn't covid-19 the bot will run until it hits that case and then stall out.
            # To prevent this we can select covid-19 cases from the condition menu, but if there are no covid-19 cases we still
            # have to pick something from the dropdown menu or cancel out. We will cancel out of the dropdown menu if there are
            # no covid-19 cases which will give us only non-covid-19 cases. The check for covid-19 later on will prevent us
            # from reviewing the next case in the queue and it will hit the wait until we have more covid-19 cases. I think this
            # will allow for conditions besides covid-19 in the queue and allow us to process all covid-19 cases without
            # stalling the bot permanently once it runs into a non-covid-19 case.
            # Open Condition dropdown menu
            time.sleep(3)
            WebDriverWait(self,self.wait_before_timeout).until(EC.element_to_be_clickable((By.XPATH, description_path)))
            self.find_element(By.XPATH, description_path).click()
            # Clear checkboxes
            WebDriverWait(self,self.wait_before_timeout).until(EC.element_to_be_clickable((By.XPATH, clear_checkbox_path)))
            self.find_element(By.XPATH, clear_checkbox_path).click()
            try:
                # Click on the 2019 Novel Coronavirus checkbox
                self.find_element(By.XPATH, "//label[contains(text(),'2019 Novel Coronavirus')]/input").click()
                # Click on the okay button
                self.find_element(By.XPATH,'/html/body/div[2]/form/div/table[2]/tbody/tr/td/table/thead/tr/th[8]/div/label[1]/input[1]').click()
            except NoSuchElementException:
                self.find_element(By.XPATH,'/html/body/div[2]/form/div/table[2]/tbody/tr/td/table/thead/tr/th[8]/div/label[1]/input[2]').click()             
            # Double click submit date for chronological order.
            WebDriverWait(self,self.wait_before_timeout).until(EC.element_to_be_clickable((By.XPATH, submit_date_path)))
            self.find_element(By.XPATH, submit_date_path).click()
            WebDriverWait(self,self.wait_before_timeout).until(EC.element_to_be_clickable((By.XPATH, submit_date_path)))
            self.find_element(By.XPATH, submit_date_path).click()
            # Double click condition for reverse alpha order.
            WebDriverWait(self,self.wait_before_timeout).until(EC.element_to_be_clickable((By.XPATH, condition_path)))
            self.find_element(By.XPATH,condition_path).click()
            WebDriverWait(self,self.wait_before_timeout).until(EC.element_to_be_clickable((By.XPATH, condition_path)))
            self.find_element(By.XPATH,condition_path).click()
            WebDriverWait(self,self.wait_before_timeout).until(EC.element_to_be_clickable((By.XPATH, condition_path)))
        except (TimeoutException, ElementClickInterceptedException):
            self.HandleBadQueueReturn()

    def HandleBadQueueReturn(self):
        """ When a request is sent to NBS to load or filter the approval queue
        and "Nothing found to display", or anything other than the populated
        queue is returned, navigate back to the home page and request the queue
        again."""
        # Recursion seems like a good idea here, but if the queue is truly empty there will be nothing to display and recursion will result in a stack overflow.
        for _ in range(self.num_attempts):
            try:
                self.go_to_home()
                self.GoToApprovalQueue()
                self.queue_loaded = True
                break
            except TimeoutException:
                self.queue_loaded = False
        if not self.queue_loaded:
            print(f"Made {self.num_attempts} unsuccessful attempts to load approval queue. Either to queue is truly empty, or a persistent issue with NBS was encountered.")

    def CheckFirstCase(self):
        """ Ensure that first case is COVID and save case's name for later use."""
        try:
            self.condition = self.find_element(By.XPATH, '//*[@id="parent"]/tbody/tr[1]/td[8]/a').get_attribute('innerText')
            self.patient_name = self.find_element(By.XPATH, '//*[@id="parent"]/tbody/tr[1]/td[7]/a').get_attribute('innerText')
        except NoSuchElementException:
            self.condition = None
            self.patient_name = None

    def GoToFirstCaseInApprovalQueue(self):
        """ Navigate to first case in the approval queue. """
        xpath_to_case = '//*[@id="parent"]/tbody/tr[1]/td[8]/a'
        xpath_to_first_name = '//*[@id="DEM104"]'
        try:
            # Make sure queue loads properly before navigating to first case.
            WebDriverWait(self,self.wait_before_timeout).until(EC.presence_of_element_located((By.XPATH, xpath_to_case)))
            self.find_element(By.XPATH, xpath_to_case).click()
            # Make sure first case loads properly before moving on.
            WebDriverWait(self,self.wait_before_timeout).until(EC.presence_of_element_located((By.XPATH, xpath_to_first_name)))
        except TimeoutException:
            self.HandleBadQueueReturn()

    def GoToNCaseInApprovalQueue(self, n=1):
        """ Navigate to first case in the approval queue. """
        xpath_to_case = f'//*[@id="parent"]/tbody/tr[{n}]/td[8]/a'
        xpath_to_first_name = '//*[@id="DEM104"]'
        try:
            # Make sure queue loads properly before navigating to first case.
            WebDriverWait(self,self.wait_before_timeout).until(EC.presence_of_element_located((By.XPATH, xpath_to_case)))
            self.find_element(By.XPATH, xpath_to_case).click()
            # Make sure first case loads properly before moving on.
            WebDriverWait(self,self.wait_before_timeout).until(EC.presence_of_element_located((By.XPATH, xpath_to_first_name)))
        except TimeoutException:
            self.HandleBadQueueReturn()

    def GoToCaseInfo(self):
        """ Within a COVID investigation navigate to the Case Info tab. """
        case_info_tab_path = '//*[@id="tabs0head1"]'
        WebDriverWait(self,self.wait_before_timeout).until(EC.presence_of_element_located((By.XPATH, case_info_tab_path)))
        self.find_element(By.XPATH, case_info_tab_path ).click()

    def GoToCOVID(self):
        """ Within a COVID investigation navigate to the COVID tab. """
        covid_tab_path = '//*[@id="tabs0head2"]'
        WebDriverWait(self,self.wait_before_timeout).until(EC.presence_of_element_located((By.XPATH, covid_tab_path)))
        self.find_element(By.XPATH, covid_tab_path).click()

    def go_to_lab(self, lab_id):
        """ Navigate to a lab from a patient profile navigate to a lab. """
        lab_report_table_path = '//*[@id="lab1"]'
        lab_report_table = self.ReadTableToDF(lab_report_table_path)
        if len(lab_report_table) > 1:
            lab_row_index = lab_report_table[lab_report_table['Event ID'] == lab_id].index.tolist()[0]
            lab_row_index = str(int(lab_row_index) + 1)
            lab_path = f'/html/body/div[2]/form/div/table[4]/tbody/tr[2]/td/div[2]/table/tbody/tr/td/div[1]/div[5]/div/table/tbody/tr/td/table/tbody/tr[{lab_row_index}]/td[1]/a'
        else:
            lab_path = '/html/body/div[2]/form/div/table[4]/tbody/tr[2]/td/div[2]/table/tbody/tr/td/div[1]/div[5]/div/table/tbody/tr/td/table/tbody/tr/td[1]/a'
        self.find_element(By.XPATH,lab_path).click()

    def read_investigation_table(self):
        """ Read the investigations table in the Events tab of a patient profile
        of all investigations on record, both open and closed."""
        investigation_table_path = '//*[@id="inv1"]'
        investigation_table = self.ReadTableToDF(investigation_table_path)
        if type(investigation_table) == pd.core.frame.DataFrame:
            investigation_table['Start Date'] = pd.to_datetime(investigation_table['Start Date'])
        return investigation_table

    def go_to_investigation_by_index(self, index):
        """Navigate to an existing investigation based on its position in the
        Investigations table in the Events tab of a patient profile."""
        if index > 1:
            existing_investigation_path = f'/html/body/div[2]/form/div/table[4]/tbody/tr[2]/td/div[2]/table/tbody/tr/td/div[1]/div[3]/div/table/tbody/tr[2]/td/table/tbody/tr[{str(index)}]/td[1]/a'
        elif index == 1:
            existing_investigation_path = f'/html/body/div[2]/form/div/table[4]/tbody/tr[2]/td/div[2]/table/tbody/tr/td/div[1]/div[3]/div/table/tbody/tr[2]/td/table/tbody/tr/td[1]/a'
        self.find_element(By.XPATH, existing_investigation_path).click()

    def go_to_investigation_by_id(self, inv_id):
        """Navigate to an investigation with a given id from a patient profile."""
        inv_table = self.read_investigation_table()
        inv_row = inv_table[inv_table['Investigation ID'] == inv_id]
        inv_index = int(inv_row.index.to_list()[0]) + 1
        self.go_to_investigation_by_index(inv_index)

    def return_to_patient_profile_from_inv(self):
        """ Go back to the patient profile from within an investigation."""
        return_to_file_path = '//*[@id="bd"]/div[1]/a'
        self.find_element(By.XPATH, return_to_file_path).click()

    def return_to_patient_profile_from_lab(self):
        """ Go back to the patient profile from within a lab report."""
        return_to_file_path = '//*[@id="doc3"]/div[1]/a'
        self.find_element(By.XPATH, return_to_file_path).click()

    def click_submit(self):
        """ Click submit button to save changes."""
        submit_button_path = '/html/body/div/div/form/div[2]/div[1]/table[2]/tbody/tr/td[2]/table/tbody/tr/td[1]/input'
        self.find_element(By.XPATH, submit_button_path).click()

    def click_manage_associations_submit(self):
        """ Click submit button in the Manage Associations window."""
        submit_button_path = '/html/body/div[2]/div/table[2]/tbody/tr/td/table/tbody/tr/td[2]/input'
        self.find_element(By.XPATH, submit_button_path).click()

    def enter_edit_mode(self):
        """From within an investigation click the edit button to enter edit mode."""
        edit_button_path = '/html/body/div/div/form/div[2]/div[1]/table[2]/tbody/tr/td[2]/table/tbody/tr/td[1]/input'
        self.find_element(By.XPATH, edit_button_path).click()
        try:
            self.switch_to.alert.accept()
        except NoAlertPresentException:
            pass

    def click_cancel(self):
        """ Click cancel."""
        cancel_path = '//*[@id="Cancel"]'
        self.find_element(By.XPATH, cancel_path).click()
        self.switch_to.alert.accept()

    def go_to_manage_associations(self):
        """ Click button to navigate to the Manage Associations page from an investigation."""
        manage_associations_path = '//*[@id="manageAssociations"]'
        self.find_element(By.XPATH, manage_associations_path).click()
        try:
            self.switch_to.alert.accept()
        except NoAlertPresentException:
            pass
############################# Data Reading/Validation Methods ##################################

    def CheckForValue(self, xpath, blank_message):
        """ If value is blank add appropriate message to list of issues. """
        value = self.find_element(By.XPATH, xpath).get_attribute('innerText')
        value = value.replace('\n','')
        if not value:
            self.issues.append(blank_message)
        return value

    def check_for_value_bool(self, path):
        """ Return boolean value based on whether a value is present."""
        value = self.ReadText(path)
        if value:
            check = True
        else:
            check = False
        return check

    def ReadDate(self, xpath, attribute='innerText'):
        """ Read date from NBS and return a datetime.date object. """
        date = self.find_element(By.XPATH, xpath).get_attribute(attribute)
        try:
            date = datetime.strptime(date, '%m/%d/%Y').date()
        except ValueError:
            date = ''
        return date

    def CheckIfField(self, parent_xpath, child_xpath, value, message):
        """ If parent field is value ensure that child field is not blank. """
        parent = self.find_element(By.XPATH, parent_xpath).get_attribute('innerText')
        parent = parent.replace('\n','')
        if parent == value:
            child = self.find_element(By.XPATH, child_xpath).get_attribute('innerText')
            child = child.replace('\n','')
            if not child:
                self.issues.append(message)

    def ReadText(self, xpath):
        """ A method to read the text of any web element identified by an Xpath
        and remove leading an trailing carriage returns sometimes included by
        Selenium's get_attribute('innerText')."""
        value = self.find_element(By.XPATH, xpath).get_attribute('innerText')
        value = value.replace('\n','')
        return value

    def ReadTableToDF(self, xpath):
        """ A method to read tables into pandas Data Frames for easy manipulation. """
        try:
            html = self.find_element(By.XPATH, xpath).get_attribute('innerHTML')
            soup = BeautifulSoup(html, 'html.parser')
            table = pd.read_html(StringIO(str(soup)))[0]
            table.fillna('', inplace = True)
        except ValueError:
            table = None
        return table

    def ReadPatientID(self):
        """ Read patient ID from within patient profile. """
        patient_id = self.ReadText('//*[@id="bd"]/table[3]/tbody/tr[1]/td[2]/span[2]')
        return patient_id

    def Sleep(self):
        """ Pause all action for the specified number of seconds. """
        for i in range(self.sleep_duration):
            time_remaining = self.sleep_duration - i
            print(f'Sleeping for: {time_remaining//60:02d}:{time_remaining%60:02d}', end='\r', flush=True)
            time.sleep(1)
        print('Sleeping for: 00:00', end='\r', flush=True)

    def send_email_local_outlook_client (self, recipient, cc, subject, message, attachment = None):
        """ Send an email using local Outlook client."""
        self.clear_gen_py()
        outlook = win32.Dispatch('outlook.application')
        mail = outlook.CreateItem(0)
        mail.GetInspector
        mail.To = recipient
        mail.CC = cc
        mail.Subject = subject
        mail.Body = message
        if attachment != None:
            mail.Attachments.Add(attachment)
        mail.Send()

    def clear_gen_py(self):
        """ Clear the contents of the the gen_py directory to ensure emails can
        always be sent."""
        # Construct to path gen_py directory if it exists.
        current_user = getpass.getuser().lower()
        gen_py_path = r'C:\Users' +'\\' + current_user + r'\AppData\Local\Temp\gen_py'
        
        gen_py_path = Path(gen_py_path)

        # If gen_py exists delete it and all contents.
        if gen_py_path.exists() and gen_py_path.is_dir():
            rmtree(gen_py_path)

    def read_config(self):
        """ Read in data from config.cfg"""
        self.config = configparser.ConfigParser()
        self.config.read('config.cfg')

    def get_email_info(self):
        """ Read information required for NBSbot to send emails via an smtp
        server to various email lists."""
        self.smtp_server = self.config.get('email', 'smtp_server')
        self.nbsbot_email = self.config.get('email', 'nbsbot_email')
        self.covid_informatics_list = self.config.get('email', 'covid_informatics_list')
        self.covid_admin_list = self.config.get('email', 'covid_admin_list')
        self.covid_commander = self.config.get('email', 'covid_commander')

    def get_usps_user_id(self):
        """ Extract the USPS User ID from the config file for later use in the
        zip_code_lookup() method."""
        self.usps_user_id = self.config.get('usps', 'user_id')

    def send_smtp_email(self, receiver, subject, body, email_name):
        """ Send emails using an SMTP server """
        message = EmailMessage()
        message.set_content(body)
        message['Subject'] = subject
        message['From'] = self.nbsbot_email
        message['To'] = ', '.join([receiver])
        try:
           smtpObj = smtplib.SMTP(self.smtp_server)
           smtpObj.send_message(message)
           print(f"Successfully sent {email_name}.")
        except smtplib.SMTPException:
           print(f"Error: unable to send {email_name}.")

    def get_main_window_handle(self):
        """ Run after login to identify and store the main window handle that the handles for pop-up windows can be differentiated."""
        self.main_window_handle = self.current_window_handle

    def switch_to_secondary_window(self):
        """ Set a secondary window as the current window in order to interact with the pop up."""
        new_window_handle = None
        for handle in self.window_handles:
            if handle != self.main_window_handle:
                new_window_handle = handle
                break
        if new_window_handle:
            self.switch_to.window(new_window_handle)

    def select_checkbox(self, xpath):
        """ Ensure the a given checkbox or radio button is selected. If not selected then click it to select."""
        checkbox = self.find_element(By.XPATH, xpath)
        if not checkbox.is_selected():
            checkbox.click()

    def unselect_checkbox(self, xpath):
        """ Ensure the a given checkbox or radio button is not selected. If selected then click it to un-select."""
        checkbox = self.find_element(By.XPATH, xpath)
        if checkbox.is_selected():
            checkbox.click()

    def county_lookup(self, city, state):
        """ Use the Nominatim geocode service via the geopy API to look up the county of a given town/city and state."""
        geolocator = Nominatim(user_agent = 'nbsbot')
        location = geolocator.geocode(city + ', ' + state)
        if location:
            location = location[0].split(', ')
            county = [x for x in location if 'County' in x]
            if len(county) == 1:
                county = county[0].split(' ')[0]
            else:
                county = ''
        else:
            county = ''
        return county

    def zip_code_lookup(self, street, city, state):
        """ Given a street address, city, and state use the USPS API via the usps
        Python package to lookup the associated zip code."""
        address = Address(
            name='',
            address_1=street,
            city=city,
            state=state,
            zipcode=''
        )
        usps = USPSApi(self.usps_user_id, test=True)
        try:
            validation = usps.validate_address(address)
            if not 'Address Not Found' in json.dumps(validation.result):
                zip_code = validation.result['AddressValidateResponse']['Address']['Zip5']
            else:
                zip_code = ''
        except:
            zip_code = ''
        return zip_code

    def check_for_error_page(self):
        """ See if NBS encountered an error."""
        error_page_path = '/html/body/table/tbody/tr/td/table/tbody/tr[2]/td/table/tbody/tr/td/table/tbody/tr[2]/td[1]'
        try:
            if self.ReadText(error_page_path) == '\xa0Error Page':
                nbs_error = True
            else:
                nbs_error = False
        except:
            nbs_error = False
        return nbs_error

    def go_to_home_from_error_page(self):
        """ Go to NBS Home page from an NBS error page. """
        xpath = '/html/body/table/tbody/tr/td/table/tbody/tr[1]/td/table/tbody/tr/td/table/tbody/tr/td[1]/a'
        for attempt in range(self.num_attempts):
            try:
                WebDriverWait(self,self.wait_before_timeout).until(EC.presence_of_element_located((By.XPATH, xpath)))
                self.find_element(By.XPATH, xpath).click()
                self.home_loaded = True
                break
            except TimeoutException:
                self.home_loaded = False
        if not self.home_loaded:
            sys.exit(print(f"Made {self.num_attempts} unsuccessful attempts to load Home page. A persistent issue with NBS was encountered."))

    def write_general_comment(self, note):
        """Write a note in the general comments box of an investigation."""
        xpath = '//*[@id="INV167"]'
        self.find_element(By.XPATH, xpath).send_keys(note)

    #new code added from covidnotificationbot, it also inherits from here
    def SendManualReviewEmail(self):
        """ Send email containing NBS IDs that required manual review."""
        if (len(self.not_a_case_log) > 0) | (len(self.lab_data_issues_log) > 0):
            subject = 'Cases Requiring Manual Review'
            email_name = 'manual review email'
            body = "COVID Commander,\nThe case(s) listed below have been moved to the rejected notification queue and require manual review.\n\nNot a case:"
            for id in self.not_a_case_log:
                body = body + f'\n{id}'
            body = body + '\n\nAssociated lab issues:'
            for id in self.lab_data_issues_log:
                body = body + f'\n{id}'
            body = body + '\n\n-Nbsbot'
            #self.send_smtp_email(recipient, cc, subject, body)
            self.send_smtp_email(self.covid_commander, subject, body, email_name)
            self.not_a_case_log = []
            self.lab_data_issues_log = []
