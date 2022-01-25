from csv import DictReader
import datetime
from matplotlib import pyplot as plt

DATA_PATH = "data_analysis\Results_25-01-2022_23-23-20.txt"

def findTimeOfData(queryID, list: list):
    for i in list:
        if i["queryID"] == queryID:
            time = i["time"]
            list.remove(i)
            return time

# Read the header
with open(DATA_PATH) as f:
    content = f.readlines()
    lookup = "HEADER, End"
    header_line_no = [line_num for line_num, line_content in enumerate(content) if lookup in line_content][0]

# Read the data
waiting_queries = []
data_records = []
with open(DATA_PATH,"r",encoding="utf-8") as dataset:
    # Skip the header
    for i in range(header_line_no + 1):
        next(dataset)
    dataset_reader = DictReader(dataset, delimiter=',')
    # Calculate the latency
    for row in dataset_reader:
        if row["action"] == "SendingQuery":
            waiting_queries.append(row)
        elif row["action"] == "ReceivedResponseBatch":
            sendingString = findTimeOfData(row["queryID"], waiting_queries)
            sendingTime = datetime.datetime.strptime(sendingString, "%H:%M:%S.%f")
            responseString = row["time"]
            responseTime = datetime.datetime.strptime(responseString, "%H:%M:%S.%f")
            latency: datetime.timedelta = responseTime - sendingTime
            data_records.append(latency.microseconds)

# Plot
plt.plot(data_records)
print()