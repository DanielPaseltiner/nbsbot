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

is_in_production = os.getenv('ENVIRONMENT', 'production') != 'development'


@error_handle
def start_anaplasma(username, passcode):
    
    from .anaplasma import Anaplasma
    

    load_dotenv()
    
    reviewed_ids = []
    what_do = []
    reason = []
    epi = []

    NBS = Anaplasma(production=True)
    NBS.set_credentials(username, passcode)
    NBS.log_in()
    NBS.GoToApprovalQueue()
    # retries = 0
    # for j in range(3):
    # print("start", j)
    patients_to_skip = set()
    error_list = []
    error = False
    n = 1
    gone_home = -1
    attempt_counter = 0
    with open("patients_to_skip.txt", "r") as patient_reader:
        patients_to_skip |= set(patient_reader.readlines())

    limit = 2
    printAt = 100
    printNo = 1
    page = 1
    loop = tqdm(generator())
    for _ in loop:
        print(f"current limit: {limit}", "starting_iteration:", loop.n)
        #check if the bot haa gone through the set limit of reviews
        if loop.n !=0 and loop.n % printAt == 0: 
            print(f"printing set {printNo}", reviewed_ids, reason)
            bot_act = pd.DataFrame(
                {
                'Inv ID': reviewed_ids,
                'Action': what_do,
                'Reason': reason,
                'Epi': epi
                })
            bot_act.to_excel(f"saved/anaplasma/Anaplasma_bot_activity_{printNo}r_{datetime.now().date().strftime('%m_%d_%Y')}.xlsx")
            printNo += 1
            reviewed_ids = []
            what_do = []
            reason = []
            epi = []
            print(f"sleeping for 2s after run {printNo - 1}")
            time.sleep(2)

        if limit and loop.n == limit:
            #for test
            # if page > 1:
            #     page -= 1
            #     gone_home = 0
            #     n = 1
            #     limit += 10
            #     continue
            #end test
            
            if len(reason) > 0:
                bot_act = pd.DataFrame(
                    {'Inv ID': reviewed_ids,
                    'Action': what_do,
                    'Reason': reason,
                    'Epi': epi
                    })
                bot_act.to_excel(f"saved/anaplasma/Anaplasma_bot_activity_Endr_{datetime.now().date().strftime('%m_%d_%Y')}.xlsx")
            break
        try:
            #Sort review queue so that only Anaplasma investigations are listed
            paths = {
                "clear_filter_path":'//*[@id="removeFilters"]/a/font',
                "description_path":'/html/body/div[2]/form/div/table[2]/tbody/tr/td/table/thead/tr/th[8]/img',
                "clear_checkbox_path":'/html/body/div[2]/form/div/table[2]/tbody/tr/td/table/thead/tr/th[8]/div/label[2]/input',
                "click_ok_path":'/html/body/div[2]/form/div/table[2]/tbody/tr/td/table/thead/tr/th[8]/div/label[1]/input[1]',
                "click_cancel_path":'/html/body/div[2]/form/div/table[2]/tbody/tr/td/table/thead/tr/th[8]/div/label[1]/input[2]',
                "tests":["Anapla"],
                "submit_date_path":'/html/body/div[2]/form/div/table[2]/tbody/tr/td/table/thead/tr/th[3]/a'
            }
            NBS.SortQueue(paths)
            print(f"sorting queue...: {NBS.queue_loaded}", "current_iteration:", loop.n)

            #for test
            # NBS.GoToNPage(page)
            #test end

            if NBS.queue_loaded:
                NBS.queue_loaded = None

                #for test
                # if gone_home > NBS.num_attempts and loop.n >= limit:
                #     print("No case in approval queue, ending...", "current_iteration:", loop.n)
                #     break
                # print("failed to go to home, skipping to approval queue...", "current_iteration:", loop.n)
                # gone_home += 1
                #test end 

                continue
            elif NBS.queue_loaded == False:
                NBS.queue_loaded = None
                print("failed to go to home, approval queue didn't load, breaking....", "current_iteration:", loop.n)
                # NBS.SendManualReviewEmail()
                # NBS.Sleep()
                # continue
                break
            
            NBS.CheckFirstCase(n)
            print("checked first case", "current_iteration:", loop.n)
            if NBS.condition == 'Anaplasma phagocytophilum':
                NBS.GoToNCaseInApprovalQueue(n)
                print(f"navigated to {n or "first"} case in queue", "current_iteration:", loop.n)
                if NBS.queue_loaded:
                    NBS.queue_loaded = None

                    #for test
                    # if gone_home > NBS.num_attempts and loop.n >= limit:
                    #     print("No case in approval queue, ending...", "current_iteration:", loop.n)
                    #     break
                    # print("failed to go to home, skipping to approval queue...", "current_iteration:", loop.n)
                    # gone_home += 1
                    #test end
                    continue
                inv_id = NBS.find_element(By.XPATH,'//*[@id="bd"]/table[3]/tbody/tr[2]/td[1]/span[2]').text 
                print(f"present, {inv_id}", "current_iteration:", loop.n)
                if inv_id in patients_to_skip: #this caused order error in nbs comment ?
                    print(f"skipping, {inv_id}", "current_iteration:", loop.n)
                    NBS.ReturnApprovalQueue()
                    print("going to approval queue", "current_iteration:", loop.n)
                    n += 1
                    print("Making up for skipped case with increased limit...", "current_iteration:", loop.n)
                    #for test
                    # limit += 1
                    # print(f"increased limit: {limit}", "current_iteration:", loop.n)
                    #test end
                    continue
                
                NBS.StandardChecks()
                print("running standard checks", "current_iteration:", loop.n)
                if not NBS.issues:
                    reviewed_ids.append(inv_id)
                    what_do.append("Approve Notification")
                    reason.append("Approved")
                    epi.append(NBS.investigator_name)

                    #for test
                    # patients_to_skip.add(inv_id)
                    # print("approved", "current_iteration:", loop.n)
                    #test end

                    #remove on test
                    NBS.ApproveNotification()
                    NBS.SendAnaplasmaEmail("Hey, please don't change anything at all and just click CN", inv_id)
                    print("current run approved", "current_iteration:", loop.n)
                NBS.ReturnApprovalQueue() #return to approval queue if no approval
                print("returning to approval queue..", "ending_iteration:", loop.n)
                if NBS.queue_loaded:
                    NBS.queue_loaded = None

                    #for test
                    # if gone_home > NBS.num_attempts and loop.n >= limit:
                    #     print("No case in approval queue, ending...", "current_iteration:", loop.n)
                    #     break
                    # print("failed to go to home, skipping to approval queue...", "current_iteration:", loop.n)
                    # gone_home += 1
                    #test end

                    continue
                if len(NBS.issues) > 0:
                    NBS.SortQueue(paths)
                    print("sorting queue to check case at the top...", "current_iteration:", loop.n)
                    #for test
                    # NBS.GoToNPage(page)
                    #test end
                    if NBS.queue_loaded:
                        NBS.queue_loaded = None
                        print("failed to go to home, skipping to approval queue....", "current_iteration:", loop.n)
                        continue
                    NBS.CheckFirstCase(n)
                    print("check for matching first case", "current_iteration:", loop.n)

                    NBS.final_name = NBS.patient_name
                    # if NBS.country and NBS.country != 'UNITED STATES' or NBS.state and  NBS.state != 'Maine':
                    #     print("Skipping patient. No action carried out", "current_iteration:", loop.n)
                    #     patients_to_skip.add(inv_id)
                    #     reviewed_ids.append(inv_id)
                    #     what_do.append("Skipped Notification")
                    #     epi.append(NBS.investigator_name)
                    #     reason.append(' '.join(NBS.issues))
                    #     print("issues seen on append:", NBS.issues, "current_iteration:", loop.n)

                    if NBS.final_name == NBS.initial_name:
                        reviewed_ids.append(inv_id)
                        what_do.append("Reject Notification")
                        epi.append(NBS.investigator_name)
                        reason.append(' '.join(NBS.issues))
                        print("issues seen on append:", NBS.issues, "current_iteration:", loop.n)

                        #for test
                        # patients_to_skip.add(inv_id)
                        # print("rejected", "current_iteration:", loop.n)
                        #test end

                        #remove on test
                        NBS.RejectNotification(n)
                        body = ''
                        if  all(case in NBS.issues  for case in ['City is blank.', 'County is blank.', 'Zip code is blank.']):
                            body = 'Hey, please only update City, Zip Code and County, then Click CN'
                        elif NBS.CorrectCaseStatus:
                            body = f'Hey, please only update the case status to {NBS.CorrectCaseStatus}, then click CN for this case.'
                        if body:
                            print('mail', body, "current_iteration:", loop.n)
                            NBS.SendAnaplasmaEmail(body, inv_id)
                        print("current iteration was rejected", "current_iteration:", loop.n)
                        NBS.GoToApprovalQueue()
                        print(f"returning approval queue....: {NBS.queue_loaded}", "ending_iteration:", loop.n)
                    elif NBS.final_name != NBS.initial_name:
                        print(f"here : {NBS.final_name} {NBS.initial_name}", "current_iteration:", loop.n)
                        print('Case at top of queue changed. No action was taken on the reviewed case.', "current_iteration:", loop.n)
                        NBS.num_fail += 1
            else:
                if attempt_counter < NBS.num_attempts:
                    attempt_counter += 1
                else:
                    attempt_counter = 0
                    print("No Anaplasma cases in notification queue.", "current_iteration:", loop.n)
                    # NBS.SendManualReviewEmail()
                    break
                    # NBS.Sleep()
        except Exception as e:
            #for test
            # raise Exception(e)
            #test end

            error_list.append(str(e))
            error = True
        #     # print(tb, "current_iteration:", loop.n)
        #     with open("error_log.txt", "a") as log:
        #         log.write(f"{datetime.now().date().strftime('%m_%d_%Y')} | anaplasma - {str(tb)}")
        #     #NBS.send_smtp_email(NBS.covid_informatics_list, 'ERROR REPORT: NBSbot(Anaplasma Notification Review) AKA Athena', tb, 'error email')
            
    print("ending, printing, saving", "current_iteration:", loop.n)
    
    if len(reason) > 0:
        print(reviewed_ids, what_do, reason, epi, "current_iteration:", loop.n)
        bot_act = pd.DataFrame(
            {'Inv ID': reviewed_ids,
            'Action': what_do,
            'Reason': reason,
            'Epi': epi
            })
        bot_act.to_excel(f"saved/anaplasma/Anaplasma_bot_activity_105r_final_{datetime.now().date().strftime('%m_%d_%Y')}.xlsx")

    # body = "The list of Anaplasma Phagocytophilum notifications that need to be manually reviewed are in the attached spreadsheet."

    # message = EmailMessage()
    # message.set_content(body)
    # message['Subject'] = 'Notification Review Report: NBSbot(Anaplasma Notification Review) AKA Anaplasma de Armas'
    # message['From'] = NBS.nbsbot_email
    # message['To'] = ', '.join(["disease.reporting@maine.gov"])
    # with open(f"Anaplasma_bot_activity_1{datetime.now().date().strftime('%m_%d_%Y')}.xlsx", "rb") as f:
    #     message.add_attachment(
    #         f.read(),
    #         filename=f"Anaplasma_bot_activity_{datetime.now().date().strftime('%m_%d_%Y')}.xlsx",
    #         maintype="application",
    #         subtype="vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    #     )
    # smtpObj = smtplib.SMTP(NBS.smtp_server)
    # smtpObj.send_message(message)
    with open("patients_to_skip.txt", "w") as patient_writer:
        patient_writer.write("\n".join(patients_to_skip) + "\n")
    if error is not None: 
        raise Exception(error_list)
        #NBS.send_smtp_email("disease.reporting@maine.gov", 'Notification Review Report: NBSbot(Anaplasma Notification Review) AKA Anaplasma de Armas', body, 'Anaplasma Notification Review email')

if __name__ == '__main__':
    start_anaplasma()


# CAS11020803ME01