import json
import os
import sys
from os import path

from parse_dump import get_base_path


def prepare_manual_evaluation(wiki_name, experiment):
    """
    Prepare files for manual evaluation

    :param wiki_name: name of the wikia dump to parse
    :type wiki_name: str
    :param experiment: name of the experiment to load the data for
    :type experiment: str
    """

    path_experiment = path.join(get_base_path(wiki_name), experiment)
    path_human_abstracts = path.join(path_experiment, "human-abstracts")

    path_labels = path.join(path_experiment, "labels-concept-based")
    path_labels_non_distinct = path.join(path_experiment, "labels-sentence-based")
    summary_creation_modes = [('concept-based', path_labels), ('sentence-based', path_labels_non_distinct)]

    path_human_evaluation = path.join(path_experiment, 'human-evaluation')
    os.makedirs(path_human_evaluation, exist_ok=True)

    topics = [file[:-6] for file in os.listdir(path_human_abstracts) if file.endswith(".txt")]

    for topic_id in topics:
        output = {
            "done": False,
        }

        with open(path.join(path_human_abstracts, topic_id + ".1.txt"), 'r') as human_abstract_file:
            human_lines = human_abstract_file.readlines()

        for summary_creation_method, path_creation_mode in summary_creation_modes:
            with open(path.join(path_creation_mode, topic_id + ".json"), 'r') as summary_file:
                summary_info = json.load(summary_file)

            output[summary_creation_method] = {
                "summary": summary_info["text"].replace("\n", " "),
                "covered": [{"sentence": line.replace("\n", ""), "is_covered": 0} for line in human_lines],
                "ilp-score": summary_info["score"]
            }

        with open(path.join(path_human_evaluation, topic_id + ".json"), "w") as output_file:
            json.dump(output, output_file, indent=2)


if __name__ == "__main__":
    wiki_name = sys.argv[1]
    experiment = sys.argv[2]

    prepare_manual_evaluation(wiki_name, experiment)
