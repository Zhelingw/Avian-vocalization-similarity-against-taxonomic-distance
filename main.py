
import csv
from classes import TaxonomyTree, Species, RecordingData

API_DATA_FILE = 'bird_data/bird_metadata.csv'
TAXONOMY_INFORMATION = 'bird_data/bird_taxonomy.csv'

species_information = []
existing_species = set()
taxonomy_tree = TaxonomyTree(
    rank='Class',
    root='Aves',
    subtrees=[TaxonomyTree(rank='Order', root='Passeriformes', subtrees=[])]
)

# Creating a csv file with only the species information from the downloaded records
with open(API_DATA_FILE, 'r') as file:
    species = csv.reader(file, delimiter=',')
    next(species)
    for row in species:
        if row[3] not in existing_species:
            existing_species.add(row[3])
            single_species_information = {
                'family': row[0],
                'genus': row[1],
                'species': row[2],
                'latin_name': row[3],
                'common_name': row[4]
            }
            species_information.append(single_species_information)

fieldnames = ['family', 'genus', 'species', 'latin_name', 'common_name']

with open(TAXONOMY_INFORMATION, 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(species_information)


# Using the created species_information file to create the taxonomy tree
for row in species_information:
    family, genus, species, latin_name, common_name \
        = row['family'], row['genus'], row['species'], row['latin_name'], row['common_name']
    taxonomy_tree.add_species(family, genus, species, latin_name, common_name, [RecordingData()])

