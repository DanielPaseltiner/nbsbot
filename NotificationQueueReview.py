from NBSdriver import NotificationQueueReview
from NBSdriver import NBSdriver
import time

test = NBSdriver(production=True)
test.LogIn()

NBS = NotificationQueueReview(production=False)
NBS.LogIn()
def RunTest(NBS):
    NBS.Reset()

    # # Check Patient Tab
    NBS.CheckFirstName()
    NBS.CheckLastName()
    NBS.CheckDOB()
    NBS.CheckCurrentSex()
    NBS.CheckStAddr()
    NBS.CheckCity()
    NBS.CheckState()
    NBS.CheckZip()
    NBS.CheckCounty()
    NBS.CheckCountry()
    NBS.CheckEthnicity()
    NBS.CheckRace()

    # # Read Associated labs
    NBS.ReadAssociatedLabs()
    NBS.AssignLabTypes()
    NBS.DetermineCaseStatus()
    NBS.GetCollectionDate()
    NBS.GetReportDate()

    # # Check Case Info Tab
    NBS.GoToCaseInfo()
    NBS.CheckJurisdiction()
    NBS.CheckProgramArea()
    NBS.CheckInvestigationStartDate()
    NBS.CheckInvestigationStatus()
    NBS.CheckSharedIndicator()
    NBS.CheckStateCaseID()
    NBS.CheckInvestigator()
    NBS.CheckReportDate()
    NBS.CheckInvestigatorAssignDate()
    NBS.CheckCountyStateReportDate()
    NBS.CheckReportingSourceType()
    NBS.CheckReportingOrganization()
    NBS.CheckPreformingLaboratory()
    NBS.CheckCollectionDate()
    NBS.CheckCurrentStatus()
    NBS.CheckProbableReason()
    NBS.CheckFirstAttemptDate()
    NBS.CheckLostToFollowUp()

    NBS.CheckHospitalizationIndicator()
    if (NBS.hospitalization_indicator == 'Yes') & (NBS.ltf != 'Yes'):
        NBS.CheckHospitalName()
        NBS.CheckAdmissionDate()
        NBS.CheckDischargeDate()

    NBS.CheckIcuIndicator()
    if (NBS.icu_indicator == 'Yes') & (NBS.ltf != 'Yes'):
        NBS.CheckIcuAdmissionDate()
        NBS.CheckIcuDischargeDate()

    NBS.CheckDieFromIllness()
    if NBS.death_inidicator == 'Yes':
        NBS.CheckDeathDate()

    NBS.CheckCongregateSetting()
    if NBS.cong_setting_indicator == 'Yes':
        NBS.CheckCongregateFacilityName()

    NBS.CheckFirstResponder()
    if NBS.first_responder == 'Yes':
        NBS.CheckFirstResponderOrg()

    NBS.CheckHealthcareWorker()
    if NBS.healthcare_worker == 'Yes':
        NBS.CheckHealtcareWorkerFacility()
        NBS.CheckHealthcareWorkerJob()
        if NBS.healthcare_worker_job == 'Other':
            NBS.CheckHealthcareWorkerJobOther()
        NBS.CheckHealthcareWorkerSetting()
        if NBS.healthcare_worker_setting == 'other':
            NBS.CheckHealthcareWorkerSettingOther()

    if NBS.ltf != 'Yes':
        NBS.CheckNumCloseContacts()
        NBS.CheckExposureSection()
        NBS.CheckDomesticTravel()
        NBS.CheckShipTravel()
        #NBS.CheckSchoolExposure()
        NBS.CheckOutbreakExposure()
        NBS.CheckTransmissionMode()
        NBS.CheckDetectionMethod()
        NBS.CheckConfirmationMethod()

    NBS.CheckConfirmationDate()
    NBS.CheckCaseStatus()
    NBS.CheckMmwrWeek()
    NBS.CheckMmwrYear()
    NBS.CheckClosedDate()

    # Check COVID Tab.
    NBS.GoToCOVID()

    NBS.CheckSymptoms()
    if (NBS.symptoms == 'Yes') & (NBS.ltf != 'Yes'):
        NBS.CheckSymptomDatesAndStatus()

    NBS.CheckIsolation()
    if NBS.ltf != 'Yes':
        NBS.CheckPreExistingConditions()

    NBS.CheckImmPactQuery()
    NBS.CheckRecievedVax()
    NBS.CheckFullyVaccinated()
    NBS.CheckTestingPreformed()

    if NBS.testing_preformed == 'Yes':
        NBS.CheckLabTable()

    # Check AOEs
    if (NBS.ltf == 'Yes') | (not NBS.investigator):
        NBS.ReadAoes()
        NBS.CheckHospAOE()
        NBS.CheckIcuAOE()
        NBS.CheckHcwAOE()
        NBS.CheckSympAOE()
        NBS.CheckCongAOE()

start = time.time()
RunTest(NBS)
stop = time.time()
print(f"{stop-start}")
print('\n'.join(NBS.issues))
