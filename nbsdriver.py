from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
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

class NBSdriver(webdriver.Chrome):
    """ A class to provide basic functionality in NBS via Selenium. """
    def __init__(self, production=False):
        self.production = production
        if self.production:
            self.site = 'https://nbs.iphis.maine.gov/'
        else:
            self.site = 'https://nbstest.state.me.us/'
        self.executable_path = r'chromedriver.exe'
        self.options = webdriver.ChromeOptions()
        self.options.add_argument('log-level=3')
        self.options.add_argument('--ignore-ssl-errors=yes')
        self.options.add_argument('--ignore-certificate-errors')
        super(NBSdriver, self).__init__(executable_path= self.executable_path, options = self.options)
        self.issues = []
        self.num_attempts = 3
        self.queue_loaded = None
        self.wait_before_timeout = 30
        self.sleep_duration = 3300 #Value in seconds

########################### NBS Navigation Methods ############################
    def GetCredentials(self):
        """ A method to prompt user to provide a valid username and RSA token
        to log in to NBS. Must """
        self.username = input('Enter your SOM username ("first_name.last_name"):')
        self.passcode = input('Enter your RSA passcode:')

    def LogIn(self):
        """ Log in to NBS. """
        self.get(self.site)
        self.switch_to.frame("contentFrame")
        self.find_element_by_id('username').send_keys(self.username)
        self.find_element_by_id('passcode').send_keys(self.passcode)
        self.find_element(By.XPATH,'/html/body/div[2]/p[2]/input[1]').click()
        WebDriverWait(self,self.wait_before_timeout).until(EC.presence_of_element_located((By.XPATH, '//*[@id="bea-portal-window-content-4"]/tr/td/h2[4]/font/a')))
        self.find_element(By.XPATH,'//*[@id="bea-portal-window-content-4"]/tr/td/h2[4]/font/a').click()

    def GoToID(self, id):
        """ Navigate to specifc patient by NBS ID from Home. """
        self.find_element(By.XPATH,'//*[@id="DEM229"]').send_keys(id)
        self.find_element(By.XPATH,'//*[@id="patientSearchByDetails"]/table[2]/tbody/tr[8]/td[2]/input[1]').click()
        self.find_element(By.XPATH,'//*[@id="searchResultsTable"]/tbody/tr/td[1]/a').click()

    def GoToEvents(self):
        """ Within patient profile navigate to the Events tab. """
        self.find_element(By.XPATH,'//*[@id="tabs0head1"]').click()

    def GoToHome(self):
        """ Go to NBS Home page. """
        xpath = '//*[@id="bd"]/table[1]/tbody/tr/td[1]/table/tbody/tr/td[1]/a'
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
        try:
            # Clear all filters
            WebDriverWait(self,self.wait_before_timeout).until(EC.element_to_be_clickable((By.XPATH, clear_filter_path)))
            self.find_element(By.XPATH, clear_filter_path).click()
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
        except TimeoutException:
            self.HandleBadQueueReturn()


    def HandleBadQueueReturn(self):
        """ When a request is sent to NBS to load or filter the approval queue
        and "Nothing found to display", or anything other than the populated
        queue is returned, navigate back to the home page and request the queue
        again."""
        # Recursion seems like a good idea here, but if the queue is truly empty there will be nothing to display and recursion will result in a stack overflow.

        for attempt in range(self.num_attempts):
            try:
                self.GoToHome()
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


    def GoToCaseInfo(self):
        """ Within a COVID investigation navigate to the Case Info tab. """
        self.find_element(By.XPATH,'//*[@id="tabs0head1"]').click()

    def GoToCOVID(self):
        """ Within a COVID investigation navigate to the COVID tab. """
        self.find_element(By.XPATH,'//*[@id="tabs0head2"]').click()

############################# Data Reading/Validation Methods ##################################

    def CheckForValue(self, xpath, blank_message):
        """ If value is blank add appropriate message to list of issues. """
        value = self.find_element(By.XPATH, xpath).get_attribute('innerText')
        value = value.replace('\n','')
        if not value:
            self.issues.append(blank_message)
        return value

    def ReadDate(self, xpath):
        """ Read date from NBS and return a datetime.date object. """
        date = self.find_element(By.XPATH, xpath).get_attribute('innerText')
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
        html = self.find_element(By.XPATH, xpath).get_attribute('innerHTML')
        soup = BeautifulSoup(html, 'html.parser')
        table = pd.read_html(str(soup))[0]
        table.fillna('', inplace = True)
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

    def SendEmail (self, recipient, cc, subject, message, attachment = None):
        self.ClearGenPy()
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

    def ClearGenPy(self):
        # Construct to path gen_py directory if it exists.
        current_user = getpass.getuser().lower()
        gen_py_path = r'C:\Users' +'\\' + current_user + '\AppData\Local\Temp\gen_py'
        gen_py_path = Path(gen_py_path)

        # If gen_py exists delete it and all contents.
        if gen_py_path.exists() and gen_py_path.is_dir():
            rmtree(gen_py_path)
