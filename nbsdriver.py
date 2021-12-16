from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime


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
        """ Navigate to approval queue from Home page. """
        self.find_element(By.PARTIAL_LINK_TEXT,'Approval Queue for Initial Notifications').click()
        self.SortApprovalQueue()

    def ReturnApprovalQueue(self):
        """ Return to Approval Queue from an investigation initally accessed from the queue. """
        self.find_element(By.XPATH,'//*[@id="bd"]/div[1]/a').click()
        self.SortApprovalQueue()

    def SortApprovalQueue(self):
        """ Sort approval queue so that case are listed chronologically by
        notification creation date and in alpha order so that
        "2019 Novel..." is at the top. """
        clear_filter_path = '//*[@id="removeFilters"]/a/font'
        submit_date_path = '//*[@id="parent"]/thead/tr/th[3]/a'
        condition_path = '//*[@id="parent"]/thead/tr/th[8]/a'
        # Clear all filters
        self.find_element(By.XPATH, clear_filter_path).click()
        # Double click submit date for chronological order.
        self.find_element(By.XPATH, submit_date_path).click()
        self.find_element(By.XPATH, submit_date_path).click()
        # Double clikc condition for alpha order.
        self.find_element(By.XPATH,condition_path).click()
        self.find_element(By.XPATH,condition_path).click()

    def CheckFirstCase(self):
        """ Ensure that first case is COVID and save case's name for later use."""
        self.condition = self.find_element(By.XPATH, '//*[@id="parent"]/tbody/tr[1]/td[8]/a').get_attribute('innerText')
        self.patient_name = self.find_element(By.XPATH, '//*[@id="parent"]/tbody/tr[1]/td[7]/a').get_attribute('innerText')

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
        value = self.find_element(By.XPATH, xpath).get_attribute('innerText')
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
        if parent == value:
            child = self.find_element(By.XPATH, child_xpath).get_attribute('innerText')
            if not child:
                self.issues.append(message)
