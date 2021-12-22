from covidcasereview import COVIDcasereview
from selenium.webdriver.common.by import By
from datetime import datetime

class COVIDnotificationreview(COVIDcasereview):
    """ A class to review COVID-19 cases in the notification queue.
    It inherits from COVIDcasereview and NBSdriver."""

    def __init__(self, production=False):
        super(COVIDnotificationreview, self).__init__(production)
        self.num_approved = 0
        self.num_rejected = 0
        self.num_fail = 0

    def StandardChecks(self):
        """ A method to conduct checks that must be done on all cases regardless of investigator. """
        self.Reset()
        # Check Patient Tab
        self.CheckFirstName()
        self.CheckLastName()
        self.CheckDOB()
        self.CheckCurrentSex()
        self.CheckStAddr()
        self.CheckCity()
        self.CheckState()
        self.CheckZip()
        self.CheckCounty()
        self.CheckCountry()
        self.CheckEthnicity()
        self.CheckRace()
        # Read Associated labs
        self.ReadAssociatedLabs()
        self.AssignLabTypes()
        self.DetermineCaseStatus()
        self.GetCollectionDate()
        self.GetReportDate()

        # # Check Case Info Tab
        self.GoToCaseInfo()
        self.CheckJurisdiction()
        self.CheckProgramArea()
        self.CheckInvestigationStartDate()
        self.CheckInvestigationStatus()
        self.CheckSharedIndicator()
        self.CheckStateCaseID()
        self.CheckInvestigator()
        self.CheckLostToFollowUp()
        self.CheckReportDate()
        self.CheckInvestigatorAssignDate()
        self.CheckCountyStateReportDate()
        self.CheckReportingSourceType()
        self.CheckReportingOrganization()
        self.CheckPreformingLaboratory()
        self.CheckCollectionDate()
        self.CheckCurrentStatus()
        self.CheckProbableReason()

        self.CheckHospitalizationIndicator()
        if self.hospitalization_indicator == 'Yes':
            self.CheckHospitalName()
            self.CheckAdmissionDate()
            self.CheckDischargeDate()

        self.CheckIcuIndicator()
        if self.icu_indicator == 'Yes':
            self.CheckIcuAdmissionDate()
            self.CheckIcuDischargeDate()

        self.CheckDieFromIllness()
        if self.death_indicator == 'Yes':
            self.CheckDeathDate()

        self.CheckCongregateSetting()
        if self.cong_setting_indicator == 'Yes':
            self.CheckCongregateFacilityName()

        self.CheckFirstResponder()
        if self.first_responder == 'Yes':
            self.CheckFirstResponderOrg()

        self.CheckHealthcareWorker()
        if self.healthcare_worker == 'Yes':
            self.CheckHealtcareWorkerFacility()
            self.CheckHealthcareWorkerJob()
            if self.healthcare_worker_job == 'Other':
                self.CheckHealthcareWorkerJobOther()
            self.CheckHealthcareWorkerSetting()
            if self.healthcare_worker_setting == 'Other':
                self.CheckHealthcareWorkerSettingOther()

        self.CheckConfirmationDate()
        self.CheckCaseStatus()
        self.CheckMmwrWeek()
        self.CheckMmwrYear()
        self.CheckClosedDate()

    def ExposureChecks(self):
        """ A method to conduct all checks required to review the exposure section. """
        self.CheckExposureSection()
        self.CheckDomesticTravel()
        self.CheckShipTravel()
        self.CheckSchoolExposure()
        self.CheckOutbreakExposure()
        self.CheckTransmissionMode()
        self.CheckDetectionMethod()

    def AOEChecks(self):
        """ A method to read and check all AOEs."""
        self.ReadAoes()
        self.CheckHospAOE()
        self.CheckIcuAOE()
        self.CheckHcwAOE()
        self.CheckSympAOE()
        self.CheckCongAOE()
        self.CheckFirstResponderAOE()
        self.CheckPregnancyAOE()

    def CaseInvestigatorReview(self):
        """ Conduct the case review required when an investigation is assigned to a case investigator. """
        self.CheckFirstAttemptDate()

        if self.ltf != 'Yes':
            self.CheckNumCloseContacts()
            self.ExposureChecks()
        # Check COVID Tab.
        self.GoToCOVID()
        self.CheckSymptoms()
        if (self.symptoms == 'Yes') & (self.ltf != 'Yes'):
            self.CheckSymptomDatesAndStatus()
        self.CheckIsolation()
        if self.ltf != 'Yes':
            self.CheckPreExistingConditions()
        self.CheckImmPactQuery()
        self.CheckRecievedVax()
        if self.vax_recieved == 'Yes':
            self.CheckFullyVaccinated()
        self.CheckTestingPreformed()
        if self.testing_preformed == 'Yes':
            self.CheckLabTable()
        # Check AOEs
        if self.ltf == 'Yes':
            self.AOEChecks()

    def OutbreakInvestigatorReview(self):
        """A method to perfrom check specific to investigations assigned to outbreak investigators. """
        self.ExposureChecks()
        # Check COVID Tab.
        self.GoToCOVID()
        self.CheckSymptoms()
        if self.symptoms == 'Yes':
            self.CheckSymptomDatesAndStatus()
        self.CheckIsolation()
        self.CheckImmPactQuery()
        self.CheckRecievedVax()
        if self.vax_recieved == 'Yes':
            self.CheckFullyVaccinated()
        self.CheckTestingPreformed()
        if self.testing_preformed == 'Yes':
            self.CheckLabTable()
        self.AOEChecks()

    def TriageReview(self):
        """A method to perfrom check specific to investigations open and closed without an investigator. """
        # Check COVID Tab.
        self.GoToCOVID()
        self.CheckSymptoms()
        self.CheckImmPactQuery()
        self.CheckRecievedVax()
        if self.vax_recieved == 'Yes':
            self.CheckFullyVaccinated()
        self.CheckTestingPreformed()
        # Check AOEs
        self.AOEChecks()

    def ReviewCase(self):
        """ Conduct review of a case in the notification queue. """
        self.SortApprovalQueue()
        self.CheckFirstCase()
        self.initial_name = self.patient_name
        if self.condition == '2019 Novel Coronavirus (2019-nCoV)':
            self.GoToFirstCaseInApprovalQueue()
            self.StandardChecks()
            if not self.investigator:
                self.TriageReview()
            elif self.investigator_name in self.outbreak_investigators:
                self.OutbreakInvestigatorReview()
            else:
                self.CaseInvestigatorReview()

            if not self.issues:
                self.ApproveNotification()
            self.ReturnApprovalQueue()
            self.SortApprovalQueue()
            self.CheckFirstCase()
            self.final_name = self.patient_name
            if (self.final_name == self.initial_name) & (len(self.issues) > 0):
                self.RejectNotification()
            elif (self.final_name != self.initial_name) & (len(self.issues) > 0):
                print('Case at top of queue changed. No action was taken on the reviewed case.')
                self.num_fail += 1
        else:
            print("No COVID-19 cases in notification queue.")

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

    def RejectNotification(self):
        """ Reject notification on first case in notification queue.
        To be used when issues were encountered during review of the case."""
        main_window_handle = self.current_window_handle
        self.find_element(By.XPATH,'//*[@id="parent"]/tbody/tr[1]/td[2]/img').click()
        for handle in self.window_handles:
            if handle != main_window_handle:
                rejection_comment_window = handle
                break
        self.switch_to.window(rejection_comment_window)
        timestamp = datetime.now().strftime("%m/%d/%Y, %H:%M:%S")
        self.issues.append('-nbsbot ' + timestamp)
        self.find_element(By.XPATH,'//*[@id="rejectComments"]').send_keys(' '.join(self.issues))
        self.find_element(By.XPATH,'/html/body/form/table/tbody/tr[3]/td/input[1]').click()
        self.switch_to.window(main_window_handle)
        self.num_rejected += 1

    def SendManualReviewEmail(self):
        """ Send email containing NBS IDs that required manual review."""
        if (len(self.not_a_case_log) > 0) | (len(self.lab_data_issues_log) > 0):
            recipient = 'MeCDC.COVIDCommander@maine.gov'
            cc = 'daniel.paseltiner@maine.gov'
            subject = 'Cases Requiring Manual Review'
            message = "COVID Commander,\nThe case(s) listed below have been moved to the rejected notification queue and require manual review\n\nNot a case:"
            for id in self.not_a_case_log:
                message = message + f'\n{id}'
            message = message + '\n\nAssociated lab issues:'
            for id in self.lab_data_issues_log:
                message = message + f'\n{id}'
            message = message + '\n\n-Nbsbot'
            self.SendEmail(recipient, cc, subject, message)
            self.not_a_case_log = []
            self.lab_data_issues_log = []
