from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
from bs4 import BeautifulSoup
from datetime import datetime


class NBSdriver(webdriver.Chrome):
    """ A class to provide basic functionality in NBS via Selenium. """
    def __init__(self, production=False):
        if production:
            self.site = 'https://nbs.iphis.maine.gov/'
        else:
            self.site = 'https://nbstest.state.me.us/'
        self.executable_path = r'chromedriver.exe'
        self.options = webdriver.ChromeOptions()
        self.options.add_argument('log-level=3')
        self.options.add_argument('--ignore-ssl-errors=yes')
        self.options.add_argument('--ignore-certificate-errors')
        super(NBSdriver, self).__init__(executable_path= self.executable_path, options = self.options)

########################### NBS Navigation Methods ############################
    def LogIn(self):
        """ Log in to NBS. """
        self.get(self.site)
        self.switch_to.frame("contentFrame")
        self.username = input('Enter your SOM username ("first_name.last_name"):')
        self.find_element_by_id('username').send_keys(self.username)
        self.passcode = input('Enter your RSA passcode:')
        self.find_element_by_id('passcode').send_keys(self.passcode)
        self.find_element(By.XPATH,'/html/body/div[2]/p[2]/input[1]').click()
        WebDriverWait(self,60).until(EC.presence_of_element_located((By.XPATH, '//*[@id="bea-portal-window-content-4"]/tr/td/h2[4]/font/a')))
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
        self.find_element(By.XPATH,'//*[@id="bd"]/table[1]/tbody/tr/td[1]/table/tbody/tr/td[1]/a').click()

    def GoToApprovalQueue(self):
        """ NAvigate to approval queue from Home page. """
        self.find_element(By.PARTIAL_LINK_TEXT,'Approval Queue for Initial Notifications').click()

    def GoToFirstCaseInApprovalQueue(self):
        """ Navigate to first case in the approval queue. """
        self.find_element(By.XPATH,'//*[@id="parent"]/tbody/tr[1]/td[8]/a').click()
        self.issues = []

    def GoToCaseInfo(self):
        """ Within a COVID investigation navigate to the Case Info tab. """
        self.find_element(By.XPATH,'//*[@id="tabs0head1"]').click()

    def GoToCOVID(self):
        """ Within a COVID investigation navigate to the COVID tab. """
        self.find_element(By.XPATH,'//*[@id="tabs0head2"]').click()

############################# Data Reading/Validation Methods ##################################

    def CheckForValue(self, xpath, blank_message):
        """ If value is blank add appropriate message to list of issues. """
        value = self.find_element(By.XPATH, xpath).text
        if not value:
            self.issues.append(blank_message)
        return value

    def ReadDate(self, xpath):
        """ Read date from NBS and return a datetime.date object. """
        date = self.find_element(By.XPATH, xpath).text
        try:
            date = datetime.strptime(date, '%m/%d/%Y').date()
        except ValueError:
            date = ''
        return date

    def CheckIfField(self, parent_xpath, child_xpath, value, message):
        """ If parent field is value ensure that child field is not blank. """
        parent = self.find_element(By.XPATH, parent_xpath).text
        if parent == value:
            child = self.find_element(By.XPATH, child_xpath).text
            if not child:
                self.issues.append(message)
