from covidnotificationreview import COVIDnotificationreview
from tqdm import tqdm
NBS = COVIDnotificationreview(production=True)
#NBS = COVIDnotificationreview()
NBS.GetCredentials()
NBS.LogIn()
# NBS.GoToApprovalQueue()
#
# num_cases = 300
# for i in tqdm(range(num_cases)):
#     NBS.ReviewCase()
# print(f'notifications approved: {NBS.num_approved}\nnotifications rejected: {NBS.num_rejected}')
