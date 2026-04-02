"""
CSC111 Project 2: recordings downloading file

This files is used to download all the recording files used for analysis in the project.

Copyright (c) 2026 Lucy Wang,  Ted Song, Yiming Xu. All rights reserved.
"""

import time
import csv
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import defaultdict
import os
import requests

MAX_SPECIES_PER_FAMILY = 10
MAX_RECORDINGS_PER_SPECIES = 10
MAX_CONCURRENT_DOWNLOADS = 4
SLEEP_BETWEEN_DOWNLOADS = 0.8

ONLY_QUALITY_A = True
MAX_LENGTH_SECONDS = "10-30"


def download_single(rec: dict, species_path: str, family: str) -> dict[str, str] | None:
    """Download single file."""
    species_name = f"{rec['gen']}_{rec['sp']}"
    file_id = rec["id"]

    file_url = rec.get("file")
    if file_url and file_url.startswith("//"):
        file_url = "https:" + file_url
    elif not file_url or not file_url.startswith("http"):
        return None

    target_path = os.path.join(species_path, f"{file_id}.mp3")

    audio_resp = requests.get(file_url, timeout=45)

    if audio_resp.status_code == 200:
        with open(target_path, "wb") as f:
            f.write(audio_resp.content)

        metadata_entry = {
            "family": family,
            "genus": rec["gen"],
            "species": rec["sp"],
            "latin_name": f"{rec['gen']}_{rec['sp']}",
            "common_name": rec.get("en", "Unknown"),
            "xc_id": file_id,
            "local_file_path": f"{family}/{species_name}/{file_id}.mp3",
            "quality": rec.get("q", ""),
            "duration": rec.get("length", ""),
        }

        return metadata_entry
    else:
        return None


def download_recordings_of(families: list[str]) -> None:
    """Download the sample species of the family,
    using the limits defined by the constant at top of file."""

    data_dir = "bird_data"

    # fill in your API key from Xeno-Canto
    api_key = "Your_key"

    if not api_key:
        return

    if not os.path.exists(data_dir):
        os.makedirs(data_dir)

    all_metadata = []

    for fam in families:
        query = f"fam:{fam}+type:song+grp:birds+len:{MAX_LENGTH_SECONDS}"
        if ONLY_QUALITY_A:
            query += "+q:A"

        query_url = f"https://xeno-canto.org/api/3/recordings?query={query}&per_page=200&key={api_key}"

        resp = requests.get(query_url, timeout=20)
        if resp.status_code != 200:
            continue

        data = resp.json()
        recordings = data.get("recordings", [])

        species_recordings = defaultdict(list)
        for rec in recordings:
            species_name = f"{rec['gen']}_{rec['sp']}"
            species_recordings[species_name].append(rec)

        sorted_species = sorted(
            species_recordings.items(),
            key=lambda x: len(x[1]),
            reverse=True,
        )

        selected_species = sorted_species[:MAX_SPECIES_PER_FAMILY]

        download_tasks = []
        for species_name, rec_list in selected_species:
            to_download = rec_list[:MAX_RECORDINGS_PER_SPECIES]

            species_path = os.path.join(data_dir, fam, species_name)
            os.makedirs(species_path, exist_ok=True)

            for rec in to_download:
                download_tasks.append((rec, species_path, fam))

        success_count = 0
        with ThreadPoolExecutor(max_workers=MAX_CONCURRENT_DOWNLOADS) as executor:
            future_to_task = {
                executor.submit(download_single, rec, path, fam): rec
                for rec, path, fam in download_tasks
            }

            for future in as_completed(future_to_task):
                meta = future.result()
                if meta:
                    all_metadata.append(meta)
                    success_count += 1
                time.sleep(SLEEP_BETWEEN_DOWNLOADS / 2)

    if all_metadata:
        csv_path = os.path.join(data_dir, "bird_metadata.csv")
        fieldnames = [
            "family", "genus", "species", "latin_name", "common_name",
            "xc_id", "local_file_path", "quality", "duration"
        ]

        # Filter and add only the species that are not already in the record
        existing_ids = set()
        file_exists = os.path.isfile(csv_path)

        if file_exists:
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                existing_ids = {row['xc_id'] for row in reader if 'xc_id' in row}

        new_metadata = [meta for meta in all_metadata if meta['xc_id'] not in existing_ids]

        if new_metadata:
            with open(csv_path, 'a', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                if not file_exists:
                    writer.writeheader()
                writer.writerows(new_metadata)


if __name__ == "__main__":
    # download_recordings_of(['paridae', 'fringillidae', 'phylloscopidae', 'picidae', 'strigidae'])

    import doctest
    doctest.testmod()

    import python_ta
    python_ta.check_all(config={
        'max-line-length': 120,
        'disable': ['static_type_checker']
    })
