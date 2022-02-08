from covidlabreview import COVIDlabreview
from tqdm import tqdm
#Initialize NBSbot
NBS = COVIDlabreview(production=True)
#Log in to NBS
NBS.get_credentials()
NBS.log_in()
#Specify the types of labs that the bot should run on and query the database accordingly.
NBS.get_db_connection_info()
NBS.get_unassigned_covid_labs()
NBS.get_patient_table()

#For testing purposes we will select the first lab only. After testing this is where a loop will start.
#for _, lab  in NBS.unassociated_labs.iloc[0].iterrows():

NBS.reset()
lab = NBS.unassociated_labs.iloc[0]
if NBS.check_for_possible_merges(lab.First_Name, lab.Last_Name, lab.Birth_Dt):
#matches = NBS.patient_list.loc[(NBS.patient_list.FIRST_NM.str[:2] == lab.First_Name[:2]) & (NBS.patient_list.LAST_NM.str[:2] == lab.Last_Name[:2]) & (NBS.patient_list.BIRTH_DT == lab.Birth_Dt)]
    print('Possible merge(s) found. Lab skipped.')
    #continue
NBS.go_to_id(lab.Patient_Local_ID)
NBS.go_to_events()
NBS.go_to_lab(lab.Lab_Local_ID)
if NBS.check_patient_hospitalization_status():
    print('Possible hospitalization. Lab skipped.')
    #continue
NBS.return_to_patient_profile_from_lab()
inv_found, existing_not_a_case = NBS.check_for_existing_investigation(lab.Specimen_Coll_DT)
if existing_not_a_case:
    print('Existing COVID investigation in the last 90 days with Not a Case status. Lab skipped.')
    #continue
elif inv_found:
    #If an existing investigation is found associate the lab with that investigation.
    NBS.go_to_investigation_by_index(self.existing_investigation_index)
    NBS.go_to_manage_associations()
    NBS.associate_lab_with_investigation(lab.Lab_Local_ID)
    NBS.click_submit()
    NBS.enter_edit_mode()
    NBS.set_earliest_positive_collection_date()
    NBS.review_case_status(lab.TestType)
    NBS.update_all_aoes(lab.HOSPITALIZED
                        ,lab.RESIDENT_CONGREGATE_SETTING
                        ,lab.FIRST_RESPONDER
                        ,lab.EMPLOYED_IN_HEALTHCARE
                        ,lab.PREGNANT)
    NBS.update_symptom_aoe(lab.SYMPTOMATIC_FOR_DISEASE, lab.ILLNESS_ONSET_DATE)
    NBS.click_submit()
else:
    #If an existing investigation was not found create an new investigation.
    NBS.go_to_lab(lab.Lab_Local_ID)
    NBS.create_investigation()
    NBS.read_address()
    NBS.set_state('Maine')
    NBS.set_country('UNITED STATES')
    if not NBS.county and NBS.city:
        NBS.county = NBS.county_lookup(NBS.city, 'Maine')
        NBS.write_county()
    if not NBS.zip_code and NBS.street:
        NBS.zip_code = NBS.zip_code_lookup(NBS.street, NBS.city, 'ME')
        NBS.write_zip()
    NBS.check_ethnicity()
    NBS.check_race()
    NBS.GoToCaseInfo()
    NBS.set_investigation_status_closed()
    NBS.set_state_case_id()
    NBS.set_county_and_state_report_dates(NBS.now)
    NBS.set_performing_lab(lab.Perform_Facility_Name)
    NBS.set_earliest_positive_collection_date(lab.Specimen_Coll_DT)
    NBS.review_case_status(lab.TestType)
    NBS.update_all_aoes(lab.HOSPITALIZED
                        ,lab.RESIDENT_CONGREGATE_SETTING
                        ,lab.FIRST_RESPONDER
                        ,lab.EMPLOYED_IN_HEALTHCARE
                        ,lab.PREGNANT)

    NBS.set_confirmation_date()
    NBS.set_mmwr()
    NBS.current_collection_date
    NBS.update_symptom_aoe(lab.SYMPTOMATIC_FOR_DISEASE, lab.ILLNESS_ONSET_DATE)
    NBS.set_closed_date()
    NBS.GoToCOVID()
    NBS.set_vaccination_fields()
    NBS.set_lab_testing_performed()
    NBS.click_submit()
    NBS.go_to_manage_associations()
    #Atempt collection vaccine records from Immpact
    if NBS.query_immpact():
        NBS.id_covid_vaccinations()
        NBS.import_covid_vaccinations()
        NBS.determine_vaccination_status()
        NBS.click_submit()
    else:
        NBS.click_cancel()
    if not all(NBS.street, NBS.city, NBS.zip_code, NBS.county, NBS.race, NBS.ethnicty):
        NBS.read_investigation_id()
        NBS.return_to_patient_profile_from_inv()
        if not all(NBS.street, NBS.city, NBS.zip_code, NBS.county):
                NBS.read_demographic_address()
        if not NBS.race:
            NBS.read_demographic_race()
        if not NBS.ethnicty:
            NBS.read_demographic_ethnicity()
        if any(NBS.demo_address, NBS.demo_race, NBS.demo_ethnicity):
            NBS.go_to_investigation_by_id(NBS.investigation_id)
            NBS.enter_edit_mode()
            if NBS.demo_address:
                NBS.write_demographic_address()
            if NBS.demo_race:
                NBS.write_demographic_race()
            if NBS.demo_ethnicity:
                NBS.write_demographic_ethnicity()
            NBS.read_address()
            if not all(NBS.street, NBS.city, NBS.zip_code, NBS.county):
                NBS.incomplete_address_log.append(NBS.ReadPatientID())
            NBS.click_submit()
NBS.go_to_home()
