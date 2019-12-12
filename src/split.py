import json
import os
import sys
from os import path, listdir

import random

from math import ceil

from parse_dump import get_base_path

SPLIT_TEST = 0.1
SPLIT_VAL = 0.1


def split(wiki_name, experiment, threshold=0):
    """
    Split available files into train, validation and test set

    :param wiki_name: name of the wikia dump to parse
    :type wiki_name: str
    :param experiment: name of the experiment to load the data for
    :type experiment: str
    :param threshold: if higher than 0, only files with sentence-based threshold over given threshold are considered
    :type threshold: int
    """
    # Base paths
    path_experiment = path.abspath(path.join(get_base_path(wiki_name), experiment))
    path_inputs = path.join(path_experiment, "inputs")
    path_labels_concept_based = path.join(path_experiment, "labels-concept-based")
    path_labels_sentence_based = path.join(path_experiment, "labels-sentence-based")
    path_human_abstracts = path.join(path_experiment, "human-abstracts")
    path_extractive_concept_based = path.join(path_experiment, "extractive-concept-based")
    path_extractive_sentence_based = path.join(path_experiment, "extractive-sentence-based")

    # List of all topics of this corpus
    files = []
    for f in listdir(path_labels_concept_based):
        if f.endswith(".json"):
            with open(path.join(path_labels_sentence_based, f), 'r') as label_file:
                label_info = json.load(label_file)
            if label_info["score"] is not None and label_info["score"] >= threshold and label_info["length"] > 0:
                files.append(f)

    split_info = {"name": wiki_name, "size": len(files), "files": files, "splits": []}

    # Shuffle files to get a balanced split
    random.seed(42)
    random.shuffle(files)

    # Generate splits based upon configuration
    split_test_val = ceil(len(files) * SPLIT_TEST)
    split_val_train = ceil(len(files) * (SPLIT_TEST + SPLIT_VAL))
    splits = [(f'test-{str(threshold)}', files[:split_test_val]),
              (f'valid-{str(threshold)}', files[split_test_val:split_val_train]),
              (f'train-{str(threshold)}', files[split_val_train:])]

    # For every split...
    for split_name, split_files in splits:
        # ... determine paths and create folders...
        split_path_inputs = path.join(path_inputs, split_name)
        os.makedirs(split_path_inputs, exist_ok=True)
        split_path_labels_concept_based = path.join(path_labels_concept_based, split_name)
        os.makedirs(split_path_labels_concept_based, exist_ok=True)
        split_path_labels_sentence_based = path.join(path_labels_sentence_based, split_name)
        os.makedirs(split_path_labels_sentence_based, exist_ok=True)
        split_path_human_abstracts = path.join(path_human_abstracts, split_name)
        os.makedirs(split_path_human_abstracts, exist_ok=True)
        split_path_extractive_concept_based = path.join(path_extractive_concept_based, split_name)
        os.makedirs(split_path_extractive_concept_based, exist_ok=True)
        split_path_extractive_sentence_based = path.join(path_extractive_sentence_based, split_name)
        os.makedirs(split_path_extractive_sentence_based, exist_ok=True)

        # Add info to json
        split_info["splits"].append({"name": split_name, "size": len(split_files), "files": split_files})

        # ... and create symlinks for all affected files
        for file in split_files:
            os.symlink(path.relpath(path.join(path_inputs, file), split_path_inputs),
                       path.join(split_path_inputs, file))
            os.symlink(path.relpath(path.join(path_labels_concept_based, file), split_path_labels_concept_based),
                       path.join(split_path_labels_concept_based, file))
            os.symlink(path.relpath(path.join(path_labels_sentence_based, file), split_path_labels_sentence_based),
                       path.join(split_path_labels_sentence_based, file))
            fileid_ref = file[:-5] + ".1.txt"
            os.symlink(path.relpath(path.join(path_human_abstracts, fileid_ref), split_path_human_abstracts),
                       path.join(split_path_human_abstracts, fileid_ref))
            os.symlink(path.relpath(path.join(path_extractive_concept_based, fileid_ref), split_path_extractive_concept_based),
                       path.join(split_path_extractive_concept_based, fileid_ref))
            os.symlink(path.relpath(path.join(path_extractive_sentence_based, fileid_ref), split_path_extractive_sentence_based),
                       path.join(split_path_extractive_sentence_based, fileid_ref))

    with open(path.join(path_experiment, f"{wiki_name}.split.{str(threshold)}.json"), 'w') as split_info_file:
        json.dump(split_info, split_info_file, indent=2)


if __name__ == "__main__":
    wiki_name = sys.argv[1]
    experiment = sys.argv[2]
    if len(sys.argv) > 3:
        threshold = int(sys.argv[3])
    else:
        threshold = 0

    split(wiki_name, experiment, threshold)
