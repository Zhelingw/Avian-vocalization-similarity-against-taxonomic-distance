
import csv
from classes import TaxonomyTree, Species, RecordingData

# loading in a dictionary of species to the paths of all its recordings
species_path = {}

with open('bird_data/bird_metadata.csv', 'r') as file:
    species = csv.reader(file, delimiter=',')
    next(species)
    for row in species:
        latin_name = row[3]
        path = row[6]
        if latin_name not in species_path:
            species_path[latin_name] = []
        species_path[latin_name].append('bird_data/' + path)

# creating the RecordingData for each species
d = RecordingData(species_path['Baeolophus_inornatus'])
print(d.features)

# for species in species_path:
#     d = RecordingData(species_path[path])
#     print(d.features)
