from covidnotificationreview import COVIDnotificationreview
NBS = COVIDnotificationreview(production=True)
NBS.GetCredentials()
NBS.LogIn()
NBS.GoToApprovalQueue()
for i in range(10):
    NBS.ReviewCase()
