# Ananplasma Bot Documentation

## Table of Contents
1. [Non-Technical Overview](#non-technical-overview)
2. [Technical Documentation](#technical-documentation)
3. [Developer Reference](#developer-reference)
4. [System Diagrams](#system-diagrams)

# Non-Technical Overview

## Purpose
Ananplasma Bot reviews anaplasma cases and reports using emails to NBS personnel. It processes cases, validates data, and flags issues for manual review.

## Key Features
- Automated case processing
- Data validationf
- Email notifications
- Manual review flagging
- Patient data verification
- Lab data verification
- Investigator verification

## Business Benefits
- Reduced manual processing time
- Consistent data validation
- Automated quality checks
- Streamlined case management
- Improved data accuracy

# Technical Documentation

## System Overview
Ananplasma Bot extends Ananplasma which inherits from Base Bot allowing access to all its functionality. It includes:
- Automated login and navigation
- Comprehensive data validation
- Error handling and recovery
- Reporting functionality
- Integration with external services (USPS, SMTP)

## Core Workflows

### 1. Case Processing
- Queue management
- Case sorting
- Data validation
- Issue flagging

### 2. Reporting
- Email notifications
- Manual review logging
- Status updates

# Developer Reference

## Code Structure

### Base Class
```python
class Anaplasmacasereview_revised(NBSdriver):
    """ A class inherits all basic NBS functionality from NBSdriver and adds
    methods for reviewing COVID case investigations for data accuracy and completeness. """
```

### Key Components
1. Configuration Management
   - Environment selection
   - API credentials

2. Navigation Methods
   - Queue management
   - Case navigation
   - Form handling

3. Data Validation
   - Demographics
   - Investigator checks
   - Lab data
   - Patient status
   - Dates
   - Addresses.

## Validation Checks

### Demographic Validation
1. Personal Information
   - Name verification
   - DOB validation
   - Age verification
   - Race validation
   - Address verification

2. Location Data
   - ZIP code validation
   - County verification
   - State/country checks

### Investigator Checks
1. Investigator 
   - Inestigation duration
   - Investigator assignment
   - Jurisdiction validation

### Lab Data Management
1. Lab Reading
   - Associated labs
   - Assign lab types
   - Case status check
   - Collection Date
   - Report Date 

### Medical Information
1. Patient status
   - Hospitalization
   - Illness duration
   - Physician checks
   - Case status

### Required Fields
- Personal identifiers
- Location data
- Medical information
- Reporting details
- MMWR data

## Error Handling

### Retry Logic
- Configurable attempts
- Timeout management
- Session recovery

### Issue Tracking
- Validation issues log
- Manual review queue
- Lab data issues

## Integration Points

### External Services
- USPS API
- SMTP email
- Chrome WebDriver
- RSA authentication

### Data Exchange
- Lab data processing
- Address verification
- Email notifications

# System Diagrams

## Class Structure
```mermaid
classDiagram
    class Anaplasmacasereview_revised {
        +production: bool
        +num_approved: int
        +num_rejected: int
        +num_fail: int
        
        +__init__(production)
        +CheckAge()
        +CheckAgeType()
        +CheckRaceAna()
        +CheckPhone()
        +read_city()
        +CheckCityCountyMatch()
        +CheckCurrentSex()
        +GoToTickBorne()
        +CheckJurisdiction()
        +CheckInvestigationStartDate()
        +CheckInvestigatorAna()
        +CheckInvestigatorAssignDateAna()
        +CheckDeath()
        +CheckHospitalization()
        +CheckIllnessDurationUnits()
        +CheckTickBite()
        +CheckOutbreak()
        +CheckImmunosupressed()
        +CheckLifeThreatening()
        +CheckPhysicianVisit()
        +CheckSerology()
        +CheckClinicallyCompatible()
        +CheckIllnessLength()
        +CheckSymptoms()
        +CheckCase()
        +RejectNotification()
        +ApproveNotification()
    }
    
    class AnaplasmaBot {

        +patients_to_skip: list
        +tb: string
        +error: bool
        +n: int
        +attempt_counter: int

        +set_credentials(username, passcode)
        +log_in()
        +GoToApprovalQueue()
        +SortApprovalQueue()
        +SendManualReviewEmail()
        +Sleep()
        +CheckFirstCase()
        +GoToFirstCaseInApprovalQueue()
        +StandardChecks()
        +ApproveNotification()
        +ReturnApprovalQueue()
        +RejectNotification()
    }
    AnaplasmaBot --|> Anaplasma
    
    note for AnaplasmaBot "Extends Anaplasma which extends Base Bot\nHandles NBS initialization, authentication and miscellaneous methods"
```

## Process Flow
```mermaid
flowchart TD
    A[Initialize Anaplasma] --> B[Set Credentials]
    B --> C[Login to NBS]
    C --> D[Navigate to Approval Queue]
    D --> E[Sort Queue]
    E --> F{Queue Load?}
    F -->|Yes| G[Check First Case]
    F -->|No| H[Send Review Email]
    G --> I{Patient condition is Covid-19}
    H --> J[Sleep Bot]
    J --> E
    I -->|Yes| K[Navigate to first case in queue]
    I -->|No| L{Check Number of Attempts}
    K --> N[Standard Checks]
    L -->|Less than| M[Increase counter]
    L -->|Greater or Equal to| H
    M --> E
    N --> O{Check for Issues}
    O -->|No issues| P[Approve Notification]
    O --> Q[Return to queue]
    P --> Q
    Q --> R[Sort Queue]
    R --> S[Check First case]
    S --> T{Final name same as Initial Name?}
    T -->|Yes| U[Reject Notification]
    T -->|No| V[Increase fail counter]
    U --> E
    V --> E
```

### Extended
```mermaid
flowchart TD
    A[Initialize Anaplasma] --> B[Set Credentials]
    B --> C[Login to NBS]
    C --> D[Navigate to Approval Queue]
    D --> E[Sort Queue]
    E --> F{Queue Load?}
    F -->|Yes| G[Check First Case]
    F -->|No| H[Send Review Email]
    G --> I{Patient condition is Covid-19}
    H --> J[Sleep Bot]
    J --> E
    I -->|Yes| K[Navigate to first case in queue]
    I -->|No| L{Check Number of Attempts}
    K --> N[Standard Checks]
    L -->|Less than| M[Increase counter]
    L -->|Greater or Equal to| H
    M --> E

    %% Standard Checks Expansion
    N --> N1[Reset Variables]
    N1 --> N2[Store Initial Name]
    N2 --> N3{Is First Name Valid?}
    N3 -->|Yes| N4[Check Last Name]
    N3 -->|No| N48[Log Issue: Invalid First Name]
    N4 --> N5{Is Last Name Valid?}
    N5 -->|Yes| N6[Check DOB]
    N5 -->|No| N49[Log Issue: Invalid Last Name]
    N6 --> N7{Is DOB Valid?}
    N7 -->|Yes| N8[Check Age and Age Type]
    N7 -->|No| N50[Log Issue: Invalid DOB]
    N8 --> N9[Check Current Sex]
    N9 --> N10{Is Sex Valid?}
    N10 -->|Yes| N11[Check Street Address]
    N10 -->|No| N51[Log Issue: Invalid Sex]
    N11 --> N12{Homeless/No Address?}
    N12 -->|Yes| N13[Skip City, Zip, County Checks]
    N12 -->|No| N14[Check City]
    N14 --> N15[Check Zip]
    N15 --> N16[Check County]
    N16 --> N17[Check State]
    N17 --> N18[Check Country]
    N18 --> N19[Check Phone]
    N19 --> N20[Check Ethnicity and Race]
    N20 --> N21[Go To Supplemental Information]
    N21 --> N22[Check Lab Reports]
    N22 --> N23[Go To Tick Borne Section]
    N23 --> N24[Check Investigation Start Date]
    N24 --> N25[Check Report Date]
    N25 --> N26[Check County and State Report Date]
    N26 --> N27{County Available?}
    N27 -->|Yes| N28[Check County]
    N27 -->|No| N29[Skip County Check]
    N28 --> N30[Check Jurisdiction]
    N30 --> N31[Check Investigation Status]
    N31 --> N32[Check Investigator]
    N32 --> N33[Check Investigator Assign Date]
    N33 --> N34[Check MMWR Week and Year]
    N34 --> N35[Check Reporting Source Type]
    N35 --> N36[Check Reporting Organization]
    N36 --> N37[Check Confirmation Date]
    N37 --> N38[Check Admission Date]
    N38 --> N39[Check Discharge Date]
    N39 --> N40[Check Illness Duration Units]
    N40 --> N41[Check Hospitalization]
    N41 --> N42[Check Pregnancy Status]
    N42 --> N43[Check Death]
    N43 --> N44[Check Immunosuppression]
    N44 --> N45[Check Life-Threatening Conditions]
    N45 --> N46[Check Performing Laboratory]
    N46 --> N47[Check Tick Bite]
    N47 --> N48[Check Physician Visit]
    N47 --> N48[Check Serology]
   N48 --> N49[Check AcuteOrConvalscent]
   N49 --> N50[Check OtherDiagnosticTest]
   N50 --> N51[Check FourFoldChange]
   N51 --> N52[Check Outbreak]
   N52 --> N53[Check Symptoms#removed Ana]
   N53 --> N54[Check IllnessLength]
    N54 --> N55{Check Serology Test Type}
    N55 -->|IgM Detected| N50[Log Issue: IgM Not Allowed in Serology]
    N55 -->|IgM Not Detected| N51[Check Case IGG]
    N56 --> N57[Check Detection Method]
    N57 --> N58[Check Confirmation Method]
    N58 --> O{Check for Issues}
    O -->|No issues| P[Approve Notification]
    O --> Q[Return to Queue]
    P --> R[Sort Queue]
    Q --> R
    R --> S[Check First Case]
    S --> T{Final Name Same as Initial Name?}
    T -->|Yes| U[Reject Notification]
    T -->|No| V[Increase Fail Counter]
    U --> E
    V --> E

    %% Additional Decision Points
    N8 --> N100{Is Age within Valid Range?}
    N100 -->|Yes| N9
    N100 -->|No| N101[Log Issue: Invalid Age]
    N19 --> N102{Is Phone Number Valid?}
    N102 -->|Yes| N20
    N102 -->|No| N103[Log Issue: Invalid Phone Number]
    N40 --> N104{Duration Units Valid?}
    N104 -->|Yes| N41
    N104 -->|No| N105[Log Issue: Invalid Duration Units]

   %% CheckCaseAna
   C1 --> C1[Check titer value]
   C1 --> C2{If titer value is less than 128?}
   C2 --> |Yes| C3{if case statuse is not Not a Case?}
   C3 --> |Yes| C3a[Add issue Does not meet the case definition, but does not have Not a Case status.]
   C2 --> |No| C4{Is clinically compatible Yes?}
   C4 --> |Yes| C4a{Is fourfold change Yes, or other diagnostic test Yes, and has any symptom, and confirmation method is laboratory confirmed, and case status is not confirmed }
   C4a --> |Yes| C4b[Add issue Meets case definition for a confirmed case but is not a confirmed case.]
   C4a --> |Yes| C4c{Is fever Yes and any other symptom asides sweats/chills yes? or Is fever no and sweats/chills Yes and any symptom Yes or at least two symptoms are Yes from Headache, Fatigue Malaise, Myalgia?, and serology test type is IgG and titer value is greater than 128 and serology positive is Yes?, and morulae visualization done is Yes?, and confirmation method is not laboratory confirmed?, and case status is not probable?}
   C4c --> |Yes| C4d[Add issue Meets case definition for a probable case but is not a probable case.]
   C4c --> |No| C4e[Add issue Does not meet the case definition, but does not have Not a Case status.]
   C4 --> |No| C5{Is clinically compatible indicator unknown?}
   C5 --> |Yes| C5a{Is serology test type IgG and titer value is greater than 128 and serology positive is Yes? or fourfold change is Yes? or other diagnostic test is Yes,? and confirmation method is not confirmed? and case status is not suspect?}
   C5a --> |Yes| C5b[Add issue Does not meet the case definition, but does not have Suspect status.]
   C5a --> |No| C5c[Add issue Does not meet the case definition, but does not have Not a Case status.]
   C5 --> |No| C6[Add issue Does not meet the case definition, but does not have Not a Case status.]
   End[End]
    
    Start --> ReadCaseStatus
    ReadCaseStatus --> ReadDNATest
    ReadDNATest --> ReadDNAResult
    ReadDNAResult --> ReadAntibodyTest
    ReadAntibodyTest --> CheckSymptoms
    CheckSymptoms -->|Yes| CheckTiterValue
    CheckSymptoms -->|No| CheckNoSymptoms
    CheckTiterValue -->|True| NotACaseStatus
    CheckTiterValue -->|False| ConfirmedStatus
    CheckNoSymptoms -->|True| NotACaseStatus
    CheckNoSymptoms -->|False| ProbableStatus
    ConfirmedStatus --> LogIssues
    ProbableStatus --> LogIssues
    NotACaseStatus --> LogIssues
    SuspectStatus --> LogIssues
    LogIssues --> End

```
# Maintenance Guidelines

## Configuration Updates
- Regular review of timeouts
- Email list maintenance
- API credential updates
- Retry attempt optimization

## Monitoring
- Manual review frequency
- Timeout occurrences
- Email notification success
- SSL certificate status

## Performance Optimization
- Wait time review
- Queue processing efficiency
- Batch size adjustments
- Resource utilization

# Support and Troubleshooting

## Common Issues
1. Login Failures
   - Check RSA token
   - Verify SSL certificates
   - Confirm credentials

2. Timeout Issues
   - Review wait settings
   - Check network connectivity
   - Verify NBS availability

3. Validation Errors
   - Check data completeness
   - Verify field formats
   - Review business rules