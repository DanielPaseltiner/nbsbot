from covidnotificationreview import COVIDnotificationreview
NBS = COVIDnotificationreview(production=True)
NBS.GetCredentials()
NBS.LogIn()
#NBS.GoToApprovalQueue()
#NBS.ReviewCase()
