from covidlabreview import COVIDlabreview
from tqdm import tqdm
import pandas as pd
import traceback

#Initialize NBSbot
NBS = COVIDlabreview(production=False) #If you are running in NBS Test you need to edit the config file to specify the NBS test server
#Log in to NBS
NBS.get_credentials()
NBS.log_in()
#Specify the types of labs that the bot should run on and query the database accordingly.
NBS.get_db_connection_info()
NBS.get_unassigned_covid_labs()
NBS.get_patient_table()

for idx, lab in tqdm(NBS.unassociated_labs.iterrows(), total=NBS.unassociated_labs.shape[0]):
    emails_sent = False
    try:
        NBS.pause_for_database()
        NBS.reset()
        NBS.get_main_window_handle()
        if NBS.check_for_possible_merges(lab.First_Name, lab.Last_Name, lab.Birth_Dt):
            print('Possible merge(s) found. Lab skipped.')
            continue
        NBS.go_to_id(lab.Patient_Local_ID)
        error_flag = NBS.go_to_events()
        if error_flag:
            NBS.go_to_home()
            print("Issue encountered navigating to patient. Continuing to next unassociated lab.")
            continue
        NBS.go_to_lab(lab.Lab_Local_ID)
        if NBS.check_patient_hospitalization_status():
            NBS.go_to_home()
            print('Possible hospitalization. Lab skipped.')
            continue
        NBS.return_to_patient_profile_from_lab()
        inv_found, existing_not_a_case = NBS.check_for_existing_investigation(lab.Specimen_Coll_DT)
        if existing_not_a_case:
            NBS.go_to_home()
            print('Existing COVID investigation in the last 90 days with Not a Case status. Lab skipped.')
            continue
        elif inv_found:
            #If an existing investigation is found associate the lab with that investigation.
            NBS.go_to_investigation_by_index(NBS.existing_investigation_index)
            NBS.go_to_manage_associations()
            NBS.associate_lab_with_investigation(lab.Lab_Local_ID)
            NBS.click_manage_associations_submit()
            NBS.enter_edit_mode()
            NBS.GoToCaseInfo()
            NBS.set_earliest_positive_collection_date(lab.Specimen_Coll_DT)
            NBS.update_report_date(lab.Lab_Rpt_Received_By_PH_Dt)
            NBS.set_county_and_state_report_dates(lab.Lab_Rpt_Received_By_PH_Dt)
            NBS.review_case_status(lab.TestType)
            NBS.update_case_info_aoes(lab.HOSPITALIZED
                                ,lab.RESIDENT_CONGREGATE_SETTING
                                ,lab.FIRST_RESPONDER
                                ,lab.EMPLOYED_IN_HEALTHCARE)
            NBS.write_general_comment(f' Associated lab {lab.Lab_Local_ID}. -nbsbot {NBS.now_str}')
            NBS.GoToCOVID()
            NBS.GoToCOVID()
            NBS.update_pregnant_aoe(lab.PREGNANT)
            NBS.update_symptom_aoe(lab.SYMPTOMATIC_FOR_DISEASE, lab.ILLNESS_ONSET_DATE)
            NBS.click_submit()
        else:
            #If an existing investigation was not found create a new investigation.
            NBS.go_to_lab(lab.Lab_Local_ID)
            NBS.create_investigation()
            NBS.read_address()
            NBS.set_state('M')
            NBS.set_country('UNITED S')
            if not NBS.county and NBS.city:
                NBS.county = NBS.county_lookup(NBS.city, 'Maine')
                NBS.write_county()
            if not NBS.zip_code and NBS.street and NBS.city:
                NBS.zip_code = NBS.zip_code_lookup(NBS.street, NBS.city, 'ME')
                NBS.write_zip()
            NBS.check_ethnicity()
            NBS.check_race()
            NBS.GoToCaseInfo()
            NBS.set_investigation_status_closed()
            NBS.set_state_case_id()
            NBS.set_county_and_state_report_dates(lab.Lab_Rpt_Received_By_PH_Dt)
            NBS.set_performing_lab(lab.Perform_Facility_Name)
            NBS.set_earliest_positive_collection_date(lab.Specimen_Coll_DT)
            NBS.review_case_status(lab.TestType)
            NBS.update_case_info_aoes(lab.HOSPITALIZED
                                ,lab.RESIDENT_CONGREGATE_SETTING
                                ,lab.FIRST_RESPONDER
                                ,lab.EMPLOYED_IN_HEALTHCARE)
            NBS.set_confirmation_date()
            NBS.set_mmwr()
            NBS.set_closed_date()
            NBS.write_general_comment(f'Created investigation from lab {lab.Lab_Local_ID}. -nbsbot {NBS.now_str}')
            NBS.GoToCOVID()
            NBS.update_symptom_aoe(lab.SYMPTOMATIC_FOR_DISEASE, lab.ILLNESS_ONSET_DATE)
            NBS.update_pregnant_aoe(lab.PREGNANT)
            NBS.set_immpact_query_to_yes()
            NBS.set_lab_testing_performed()
            NBS.click_submit()
            NBS.click_submit()
            NBS.patient_id = NBS.ReadPatientID()
            NBS.go_to_manage_associations()
            #Atempt collection vaccine records from Immpact
            if NBS.query_immpact():
                NBS.id_covid_vaccinations()
                if len(NBS.covid_vaccinations) >= 1:
                    NBS.import_covid_vaccinations()
                    NBS.determine_vaccination_status(NBS.current_collection_date)
                    NBS.switch_to.window(NBS.main_window_handle)
                    NBS.click_manage_associations_submit()
                    NBS.enter_edit_mode()
                    NBS.GoToCOVID()
                    NBS.set_vaccination_fields()
                    NBS.click_submit()
                else:
                    NBS.close()
                    NBS.switch_to.window(NBS.main_window_handle)
                    NBS.click_cancel()
            else:
                NBS.switch_to.window(NBS.main_window_handle)
                NBS.click_cancel()
                if NBS.multiple_possible_patients_in_immpact:
                    NBS.failed_immpact_query_log.append(NBS.ReadPatientID())

            if not all([NBS.street, NBS.city, NBS.zip_code, NBS.county, NBS.unambiguous_race, NBS.ethnicity]):
                NBS.read_investigation_id()
                NBS.return_to_patient_profile_from_inv()
                NBS.go_to_demographics()
                if not all([NBS.street, NBS.city, NBS.zip_code, NBS.county]):
                    NBS.read_demographic_address()
                if not NBS.unambiguous_race:
                    NBS.read_demographic_race()
                if (not NBS.ethnicity) | (NBS.ethnicity == 'unknown'):
                    NBS.read_demographic_ethnicity()
                NBS.go_to_events()
                NBS.go_to_investigation_by_id(NBS.investigation_id)
                if (type(NBS.demo_address) == pd.core.series.Series) | (any([NBS.demo_race, NBS.demo_ethnicity])):
                    NBS.enter_edit_mode()
                    if type(NBS.demo_address) == pd.core.series.Series:
                        NBS.write_demographic_address()
                    if NBS.demo_race:
                        NBS.write_demographic_race()
                    if NBS.demo_ethnicity:
                        NBS.write_demographic_ethnicity()
                    NBS.read_address()
                    if not all([NBS.street, NBS.city, NBS.zip_code, NBS.county]):
                        NBS.incomplete_address_log.append(NBS.ReadPatientID())
                    NBS.click_submit()
            NBS.create_notification()
            NBS.check_jurisdiction()
        NBS.go_to_home()

    except:
        tb = traceback.format_exc()
        print(tb)
        NBS.send_smtp_email(NBS.covid_informatics_list, 'ERROR REPORT: NBSbot(COVID open/close) AKA Hoover', tb, 'error email')
        NBS.send_bad_address_email()
        NBS.send_failed_query_email()
        emails_sent = True
        if NBS.check_for_error_page():
            NBS.go_to_home_from_error_page()
        else:
            break
if not emails_sent:
    NBS.send_bad_address_email()
    NBS.send_failed_query_email()
if idx + 1 == len(NBS.unassociated_labs):
    print('No additional labs to review.')

# message = EmailMessage()
# message.set_content('test')
# message['Subject'] = 'TEST'
# message['From'] = NBS.nbsbot_email
# message['To'] = ', '.join([NBS.covid_informatics_list])
# try:
#    smtpObj = smtplib.SMTP(NBS.smtp_server)
#    smtpObj.send_message(message)
#    print(f"Successfully sent {email_name}.")
# except SMTPException:
#    print(f"Error: unable to send {email_name}.")
