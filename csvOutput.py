import csv

# Your data
data = [
    ['CAS10978034ME01', 'CAS10978034ME01', 'CAS10978034ME01', 'CAS10978034ME01', 'CAS10978034ME01', 'CAS10978034ME01', 'CAS10978034ME01', 'CAS10978034ME01', 'CAS10978034ME01', 'CAS10978034ME01', 'CAS10978034ME01', 'CAS10978034ME01', 'CAS10978034ME01', 'CAS10978034ME01', 'CAS10978034ME01', 'CAS10978034ME01', 'CAS10978034ME01', 'CAS10978034ME01', 'CAS10978034ME01', 'CAS10978034ME01', 'CAS10978034ME01', 'CAS10978034ME01', 'CAS10978034ME01', 'CAS10978034ME01'],
    ['Reject Notification', 'Reject Notification', 'Reject Notification', 'Reject Notification', 'Reject Notification', 'Reject Notification', 'Reject Notification', 'Reject Notification', 'Reject Notification', 'Reject Notification', 'Reject Notification', 'Reject Notification', 'Reject Notification', 'Reject Notification', 'Reject Notification', 'Reject Notification', 'Reject Notification', 'Reject Notification', 'Reject Notification', 'Reject Notification', 'Reject Notification', 'Reject Notification', 'Reject Notification', 'Reject Notification'],
    ['Missing lab report.', 'Missing lab report.', 'Missing lab report.', 'Missing lab report.', 'Missing lab report.', 'Missing lab report.', 'Missing lab report.', 'Missing lab report.', 'Missing lab report.', 'Missing lab report.', 'Missing lab report.', 'Missing lab report.', 'Missing lab report.', 'Missing lab report.', 'Missing lab report.', 'Missing lab report.', 'Missing lab report.', 'Missing lab report.', 'Missing lab report.', 'Missing lab report.', 'Missing lab report.', 'Missing lab report.', 'Missing lab report.', 'Missing lab report.']
]

# Transpose the data (rows to columns)
transposed = list(zip(*data))

# Write to CSV with headers
with open('output.csv', 'w', newline='', encoding='utf-8') as file:
    writer = csv.writer(file)
    writer.writerow(['ID', 'Notification Type', 'Reason'])  # Headers
    writer.writerows(transposed)

print("CSV file created successfully!")