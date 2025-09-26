# -*- coding: utf-8 -*-
"""
Created on Wed Apr 17 10:35:46 2024

@author: Jared.Strauch
"""
from tqdm import tqdm
import time
import traceback
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import ElementNotInteractableException
from selenium.common.exceptions import StaleElementReferenceException
from selenium.common.exceptions import TimeoutException
import pandas as pd
from datetime import datetime
import smtplib, ssl
from email.message import EmailMessage

from dotenv import load_dotenv
import os
from decorator import error_handle

def generator():
    while True:
        yield

reviewed_ids = []
what_do = []
reason = []

is_in_production = os.getenv('ENVIRONMENT', 'production') != 'development'


@error_handle
def start_giardia(username, passcode):
    
    from .giardia import Giardia
    

    load_dotenv()
    
    
    NBS = Giardia(production=False)
    NBS.set_credentials(username, passcode)
    NBS.log_in()
    NBS.GoToApprovalQueue()

    patients_to_skip = set()
    error_list = []
    error = False
    n = 1
    gone_home = -1
    attempt_counter = 0
    with open("patients_to_skip.txt", "r") as patient_reader:
        patients_to_skip |= set(patient_reader.readlines())

    limit = 4
    page = 2
    loop = tqdm(generator())
    for _ in loop:
        print(f"current limit: {limit}")
        #check if the bot haa gone through the set limit of reviews
        if loop.n == limit:
            if page > 1:
                page -= 1
                gone_home = 0
                n = 1
                limit += 20
                continue
            break
        try:
            #Sort review queue so that only giardia investigations are listed
            paths = {
                "clear_filter_path":'//*[@id="removeFilters"]/a/font',
                "description_path":'/html/body/div[2]/form/div/table[2]/tbody/tr/td/table/thead/tr/th[8]/img',
                "clear_checkbox_path":'/html/body/div[2]/form/div/table[2]/tbody/tr/td/table/thead/tr/th[8]/div/label[2]/input',
                "click_ok_path":'/html/body/div[2]/form/div/table[2]/tbody/tr/td/table/thead/tr/th[8]/div/label[1]/input[1]',
                "click_cancel_path":'/html/body/div[2]/form/div/table[2]/tbody/tr/td/table/thead/tr/th[8]/div/label[1]/input[2]',
                "tests":["Giardiasis"],
                "submit_date_path":'/html/body/div[2]/form/div/table[2]/tbody/tr/td/table/thead/tr/th[3]/a'
            }
            NBS.SortQueue(paths)
            print(f"sorting queue...: {NBS.queue_loaded}")
            NBS.GoToNPage(page)

            if NBS.queue_loaded:
                NBS.queue_loaded = None
                if gone_home > NBS.num_attempts and loop.n >= limit:
                    print("No case in approval queue, ending...")
                    break
                print("failed to go to home, skipping to approval queue...")
                gone_home += 1
                continue
            elif NBS.queue_loaded == False:
                NBS.queue_loaded = None
                print("failed to go to home, approval queue didn't load, breaking....")
                # NBS.SendManualReviewEmail()
                # NBS.Sleep()
                # continue
                break
            
            NBS.CheckFirstCase()
            print("checked first case")
            if NBS.condition == 'Giardiasis':
                NBS.GoToNCaseInApprovalQueue(n)
                print("navigated to first case in queue")
                if NBS.queue_loaded:
                    NBS.queue_loaded = None
                    if gone_home > NBS.num_attempts and loop.n >= limit:
                        print("No case in approval queue, ending...")
                        break
                    print("failed to go to home, skipping to approval queue...")
                    gone_home += 1
                    continue
                inv_id = NBS.find_element(By.XPATH,'//*[@id="bd"]/table[3]/tbody/tr[2]/td[1]/span[2]').text 
                if inv_id in patients_to_skip:
                    print(f"present, {inv_id}")
                    NBS.ReturnApprovalQueue()
                    print("going to approval queue")
                    n += 1
                    limit += 1
                    print(f"increased limit: {limit}")
                    continue
                
                NBS.StandardChecks()
                print("running standard checks")
                if not NBS.issues:
                    reviewed_ids.append(inv_id)
                    what_do.append("Approve Notification")
                    reason.append("Approved")
                    patients_to_skip.add(inv_id)
                    print("approved")
                    # NBS.ApproveNotification()
                    # NBS.SendAnaplasmaEmail("Hey, please don't change anything at all and just click CN", inv_id)
                NBS.ReturnApprovalQueue()
                print("returning to approval queue..")
                if NBS.queue_loaded:
                    NBS.queue_loaded = None
                    if gone_home > NBS.num_attempts and loop.n >= limit:
                        print("No case in approval queue, ending...")
                        break
                    print("failed to go to home, skipping to approval queue...")
                    gone_home += 1
                    continue
                if len(NBS.issues) > 0:
                    NBS.SortQueue(paths)
                    print("sorting queue...")
                    NBS.GoToNPage(page)
                    if NBS.queue_loaded:
                        NBS.queue_loaded = None
                        print("failed to go to home, skipping to approval queue....")
                        continue
                    NBS.CheckFirstCase()
                    print("check for matching first case")

                    NBS.final_name = NBS.patient_name
                    # if NBS.country != 'UNITED STATES':
                    #     print("Skipping patient. No action carried out")
                    #     patients_to_skip.add(inv_id)
                    if NBS.final_name == NBS.initial_name:
                        reviewed_ids.append(inv_id)
                        what_do.append("Reject Notification")
                        reason.append(' '.join(NBS.issues))
                        patients_to_skip.add(inv_id)
                        print("rejected")
                        # NBS.RejectNotification()
                        # body = ''
                        # if  all(case in NBS.issues  for case in ['City is blank.', 'County is blank.', 'Zip code is blank.']):
                        #     body = 'Hey, please only update City, Zip Code and County, then Click CN'
                        # elif NBS.CorrectCaseStatus:
                        #     body = f'Hey, please only update the case status to {NBS.CorrectCaseStatus}, then click CN for this case.'
                        # if body:
                        #     print('mail', body)
                        #     NBS.SendAnaplasmaEmail(body, inv_id)
                        NBS.GoToApprovalQueue()
                        print(f"returning approval queue....: {NBS.queue_loaded}")
                    elif NBS.final_name != NBS.initial_name:
                        print(f"here : {NBS.final_name} {NBS.initial_name}")
                        print('Case at top of queue changed. No action was taken on the reviewed case.')
                        NBS.num_fail += 1
            else:
                if attempt_counter < NBS.num_attempts:
                    attempt_counter += 1
                else:
                    attempt_counter = 0
                    print("No giardia cases in notification queue.")
                    # NBS.SendManualReviewEmail()
                    break
                    # NBS.Sleep()
        except Exception as e:
            raise Exception(e)
            # error_list.append(str(e))
            # error = True
        #     # print(tb)
        #     with open("error_log.txt", "a") as log:
        #         log.write(f"{datetime.now().date().strftime('%m_%d_%Y')} | giardia - {str(tb)}")
        #     #NBS.send_smtp_email(NBS.covid_informatics_list, 'ERROR REPORT: NBSbot(giardia Notification Review) AKA Athena', tb, 'error email')
            
    print("ending, printing, saving")
    print(reviewed_ids, what_do, reason)
    bot_act = pd.DataFrame(
        {'Inv ID': reviewed_ids,
        'Action': what_do,
        'Reason': reason
        })
    bot_act.to_excel(f"saved/giardia/Giardia_bot_activity_{datetime.now().date().strftime('%m_%d_%Y')}.xlsx")

    # body = "The list of giardia Phagocytophilum notifications that need to be manually reviewed are in the attached spreadsheet."
    
    # message = EmailMessage()
    # message.set_content(body)
    # message['Subject'] = 'Notification Review Report: NBSbot(giardia Notification Review) AKA giardia de Armas'
    # message['From'] = NBS.nbsbot_email
    # message['To'] = ', '.join(["disease.reporting@maine.gov"])
    # with open(f"giardia_bot_activity_1{datetime.now().date().strftime('%m_%d_%Y')}.xlsx", "rb") as f:
    #     message.add_attachment(
    #         f.read(),
    #         filename=f"giardia_bot_activity_{datetime.now().date().strftime('%m_%d_%Y')}.xlsx",
    #         maintype="application",
    #         subtype="vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    #     )
    # smtpObj = smtplib.SMTP(NBS.smtp_server)
    # smtpObj.send_message(message)
    with open("patients_to_skip.txt", "w") as patient_writer:
        patient_writer.write("\n".join(patients_to_skip) + "\n")
    if error is not None: 
        raise Exception(error_list)
    #NBS.send_smtp_email("disease.reporting@maine.gov", 'Notification Review Report: NBSbot(giardia Notification Review) AKA giardia de Armas', body, 'giardia Notification Review email')

if __name__ == '__main__':
    start_giardia()