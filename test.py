from covidnotificationreview import COVIDnotificationreview
from tqdm import tqdm
NBS = COVIDnotificationreview(production=True)
NBS.GetCredentials()
NBS.LogIn()
NBS.GoToApprovalQueue()

num_cases = 100
for i in tqdm(range(num_cases)):
    NBS.ReviewCase()
print(f'notfications approved: {NBS.num_approved}\nnotifications rejected: {NBS.num_rejected}')
