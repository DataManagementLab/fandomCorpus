import json
import sys
from os import path, listdir

from parse_dump import get_base_path


def aggregate_label_scores(wiki_name, experiment):
    """
    Aggregate scores of summary recreation in one single csv file

    :param wiki_name: name of the wikia dump to parse
    :type wiki_name: str
    :param experiment: name of the experiment to load the data for
    :type experiment: str
    """

    path_experiment = path.join(get_base_path(wiki_name), experiment)
    path_labels = path.join(path_experiment, "labels-concept-based")
    path_labels_non_distinct = path.join(path_experiment, "labels-sentence-based")

    output = []

    for file in listdir(path_labels):
        if file.endswith(".json"):
            with open(path.join(path_labels, file), 'r') as labels_concept_based_file:
                info_concept_based = json.load(labels_concept_based_file)
            with open(path.join(path_labels_non_distinct, file), 'r') as labels_sentence_based_file:
                info_sentence_based = json.load(labels_sentence_based_file)

            output += f"{info_concept_based['id']};{info_concept_based['score']};{info_concept_based['length']};{info_sentence_based['score']};{info_sentence_based['length']}\n"

    with open(path.join(path_experiment, "label_scores.csv"), "w") as output_file:
        output_file.write("id;score_concept_based;length_concept_based;score_sentence_based;length_sentence_based\n")
        output_file.writelines(output)


if __name__ == "__main__":
    wiki_name = sys.argv[1]
    experiment = sys.argv[2]

    aggregate_label_scores(wiki_name, experiment)
