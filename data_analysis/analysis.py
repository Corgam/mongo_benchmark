from csv import DictReader

DATA_PATH = "data_analysis\Results_25-01-2022_20-58-49.txt"

# Read the header
with open(DATA_PATH) as f:
    content = f.readlines()
    lookup = "HEADER, End"
    header_line_no = [line_num for line_num, line_content in enumerate(content) if lookup in line_content][0]

with open(DATA_PATH,"r",encoding="utf-8") as dataset:
    # Skip the header
    for i in range(header_line_no + 1):
        next(dataset)
    dataset_reader = DictReader(dataset, delimiter=',')
    for row in dataset_reader:
        print(row)