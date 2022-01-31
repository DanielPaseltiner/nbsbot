from covidnotificationreview import COVIDnotificationreview
from tqdm import tqdm
import time

def generator():
    while True:
        yield

NBS = COVIDnotificationreview(production=True)
NBS.get_credentials()
NBS.log_in()
NBS.GoToApprovalQueue()

attempt_counter = 0
for _ in tqdm(generator()):
    NBS.SortApprovalQueue()

    if NBS.queue_loaded:
        NBS.queue_loaded = None
        continue
    elif NBS.queue_loaded == False:
        NBS.queue_loaded = None
        NBS.SendManualReviewEmail()
        NBS.Sleep()
        continue

    NBS.CheckFirstCase()
    NBS.initial_name = NBS.patient_name
    if NBS.condition == '2019 Novel Coronavirus (2019-nCoV)':
        NBS.GoToFirstCaseInApprovalQueue()
        if NBS.queue_loaded:
            NBS.queue_loaded = None
            continue
        NBS.StandardChecks()
        if not NBS.investigator:
            NBS.TriageReview()
        elif NBS.investigator_name in NBS.outbreak_investigators:
            NBS.OutbreakInvestigatorReview()
        else:
            NBS.CaseInvestigatorReview()

        if not NBS.issues:
            NBS.ApproveNotification()
        NBS.ReturnApprovalQueue()
        if NBS.queue_loaded:
            NBS.queue_loaded = None
            continue
        if len(NBS.issues) > 0:
            NBS.SortApprovalQueue()
            if NBS.queue_loaded:
                NBS.queue_loaded = None
                continue
            NBS.CheckFirstCase()
            NBS.final_name = NBS.patient_name
            if NBS.final_name == NBS.initial_name:
                NBS.RejectNotification()
            elif NBS.final_name != NBS.initial_name:
                print('Case at top of queue changed. No action was taken on the reviewed case.')
                NBS.num_fail += 1
    else:
        if attempt_counter < NBS.num_attempts:
            attempt_counter += 1
        else:
            attempt_counter = 0
            print("No COVID-19 cases in notification queue.")
            NBS.SendManualReviewEmail()
            NBS.Sleep()
