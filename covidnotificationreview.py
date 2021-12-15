from covidcasereview import COVIDcasereview

class COVIDnotificationreview(COVIDcasereview):
    """ A class to review COVID-19 cases in the notification queue.
    It inherits from COVIDcasereview and NBSdriver."""

    def __init__(self, production=False):
        super(COVIDnotificationreview, self).__init__(production)

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
        if self.death_inidicator == 'Yes':
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
        self.CheckConfirmationMethod()

    def CaseInvestigatorReview(self):
        """ Conduct the case review required when an investigation is assigned to a case investigator. """
        self.StandardChecks()
        self.CheckFirstAttemptDate()
        self.CheckLostToFollowUp()
        if self.ltf != 'Yes':
            self.CheckNumCloseContacts()
            self.CheckExposureSection()
            self.CheckDomesticTravel()
            self.CheckShipTravel()
            self.CheckSchoolExposure()
            self.CheckOutbreakExposure()
            self.CheckTransmissionMode()
            self.CheckDetectionMethod()
            self.CheckConfirmationMethod()
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
        self.CheckFullyVaccinated()
        self.CheckTestingPreformed()
        if self.testing_preformed == 'Yes':
            self.CheckLabTable()
        # Check AOEs
        if self.ltf == 'Yes':
            self.ReadAoes()
            self.CheckHospAOE()
            self.CheckIcuAOE()
            self.CheckHcwAOE()
            self.CheckSympAOE()
            self.CheckCongAOE()

    def OutbreakInvestigatorReview(self):
        """A method to perfrom check specific to investigations assigned to outbreak investigators. """
        self.StandardChecks()
        self.ExposureChecks()
        # Check COVID Tab.
        self.GoToCOVID()
        self.CheckSymptoms()
        if self.symptoms == 'Yes':
            self.CheckSymptomDatesAndStatus()
        self.CheckIsolation()
        self.CheckImmPactQuery()
        self.CheckRecievedVax()
        self.CheckFullyVaccinated()
        self.CheckTestingPreformed()
        if self.testing_preformed == 'Yes':
            self.CheckLabTable()

    def TraigeReview(self):
        """A method to perfrom check specific to investigations open and closed without an investigator. """
        self.StandardChecks()
        # Check COVID Tab.
        self.GoToCOVID()
        self.CheckSymptoms()
        self.CheckImmPactQuery()
        self.CheckRecievedVax()
        self.CheckFullyVaccinated()
        self.CheckTestingPreformed()
        # Check AOEs
        self.ReadAoes()
        self.CheckHospAOE()
        self.CheckIcuAOE()
        self.CheckHcwAOE()
        self.CheckSympAOE()
        self.CheckCongAOE()

    def ApproveNotification(self):
        """ Approve notification on first case in notification queue. """
        self.find_element(By.XPATH,'//*[@id="parent"]/tbody/tr[1]/td[1]/img').click()

    #def RejectNotification(self):
