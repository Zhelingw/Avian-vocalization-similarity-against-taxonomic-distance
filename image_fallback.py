import csv
PATH = "bird_data/image_urls.csv"

# If web request fails to retrieve image url, then a preset will be chosen from here
FALLBACK = {}

# Automatically loads preset urls
with open(PATH) as csvfile:
    reader = csv.reader(csvfile)

    for row in reader:
        FALLBACK[row[0]] = row[1]

