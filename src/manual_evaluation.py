import json
import os
import sys
from os import path
import matplotlib.pyplot as plt
import numpy as np

from parse_dump import get_base_path, DATA_PATH


def manual_evaluation(corpus_names, experiment):
    """
    Prepare files for manual evaluation

    :param corpus_names: name of the different corpora to put into the plot
    :type corpus_names: str
    :param experiment: name of the experiment to load the data for
    :type experiment: str
    """

    path_general_output = path.join(DATA_PATH, 'benchmarks')
    os.makedirs(path_general_output, exist_ok=True)
    summary_creation_modes = ['concept-based', 'sentence-based']
    values_for_modes_and_corpora = {method: [] for method in summary_creation_modes}
    corpus_names_string = "_".join(corpus_names)

    ilp_scores_for_method = {method: [] for method in summary_creation_modes}

    for corpus_name in corpus_names:
        path_experiment = path.join(get_base_path(corpus_name), experiment)
        path_human_evaluation = path.join(path_experiment, 'human-evaluation')
        summary_creation_modes_for_this_corpus = [('concept-based', [], []), ('sentence-based', [], [])]

        for file in os.listdir(path_human_evaluation):
            if file.endswith(".json"):
                with open(path.join(path_human_evaluation, file), "r") as eval_file:
                    evaluation_info = json.load(eval_file)

                for summary_creation_method, method_ilp_scores, method_human_scores in summary_creation_modes_for_this_corpus:
                    ilp_score = evaluation_info[summary_creation_method]['ilp-score']
                    ilp_scores_for_method[summary_creation_method].append(ilp_score)
                    if evaluation_info["done"]:
                        method_ilp_scores.append(ilp_score)
                        coverings = [e["is_covered"] for e in evaluation_info[summary_creation_method]['covered'] if 0 <= e['is_covered'] <= 3]
                        method_human_scores.append(sum(coverings) / len(coverings))

        for summary_creation_method, method_ilp_scores, method_human_scores in summary_creation_modes_for_this_corpus:
            values_for_modes_and_corpora[summary_creation_method].append((
                corpus_name,
                method_ilp_scores,
                method_human_scores
            ))

    for summary_creation_method in summary_creation_modes:
        plt.clf()
        plt.title(f"ILP-Score Human-Annotator Agreement\n{experiment} - {summary_creation_method}")
        plt.ylim(-0.25, 3.25)
        for corpus_name, method_ilp_scores, method_human_scores in values_for_modes_and_corpora[summary_creation_method]:
            plt.scatter(x=np.array(method_ilp_scores), y=np.array(method_human_scores))
        plt.legend(corpus_names, loc='lower right')
        plt.xlabel("ILP Objective Scores")
        plt.ylabel('Human Annotation [0-3]')
        plt.savefig(path.join(path_general_output, f"human.{corpus_names_string}.{experiment}.{summary_creation_method}.png"))
        plt.show()

    # Plot correlation between ilp scores for all socres...
    plt.clf()
    plt.title(f"ILP-Scores Correlation (all)\n{summary_creation_modes[0]} vs. {summary_creation_modes[1]}")
    plt.scatter(x=np.array(ilp_scores_for_method[summary_creation_modes[0]]), y=np.array(ilp_scores_for_method[summary_creation_modes[1]]), alpha=0.2)
    plt.xlabel(f"ILP Objective Scores ({summary_creation_modes[0]})")
    plt.ylabel(f"ILP Objective Scores ({summary_creation_modes[1]})")
    plt.savefig(path.join(path_general_output, f"ilp.{corpus_names_string}.{experiment}.all.png"))
    plt.show()

    # ... and evaluated values only
    plt.clf()
    plt.title(f"ILP-Scores Correlation (evaluated)\n{summary_creation_modes[0]} vs. {summary_creation_modes[1]}")

    ilp_scores_for_method = []
    for method in summary_creation_modes:
        scores = []
        for _, ilp_scores, _ in values_for_modes_and_corpora[method]:
            scores.extend(ilp_scores)
        ilp_scores_for_method.append(np.array(scores))

    plt.scatter(x=np.array(ilp_scores_for_method[0]), y=np.array(ilp_scores_for_method[1]), alpha=0.5)
    plt.xlabel(f"ILP Objective Scores ({summary_creation_modes[0]})")
    plt.ylabel(f"ILP Objective Scores ({summary_creation_modes[1]})")
    plt.savefig(path.join(path_general_output, f"ilp.{corpus_names_string}.{experiment}.evaluated.png"))
    plt.show()

    # plot manual evaluation against each other
    plt.clf()
    plt.title(f"Human Evaluation Correlation\n{summary_creation_modes[0]} vs. {summary_creation_modes[1]}")

    human_scores_for_method = []
    for method in summary_creation_modes:
        scores = []
        for _, _, human_scores in values_for_modes_and_corpora[method]:
            scores.extend(human_scores)
        human_scores_for_method.append(np.array(scores))

    plt.scatter(x=np.array(ilp_scores_for_method[0]), y=np.array(ilp_scores_for_method[1]), alpha=0.5)
    plt.xlabel(f"Human Evaluation ({summary_creation_modes[0]})")
    plt.ylabel(f"Human Evaluation ({summary_creation_modes[1]})")
    plt.savefig(path.join(path_general_output, f"human.{corpus_names_string}.{experiment}.evaluated.png"))
    plt.show()

    print(f"Manual evaluation covered {len(ilp_scores_for_method[0])} entries")


if __name__ == "__main__":
    corpus_names = sys.argv[1].split(',')
    experiment = sys.argv[2]

    manual_evaluation(corpus_names, experiment)
