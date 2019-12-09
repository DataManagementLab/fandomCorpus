import random
import sys

from assign import assign
from eval_quality import aggregate_label_scores
from parse_dump import extract_articles, parse_texts
from prepare_manual_evaluation import prepare_manual_evaluation
from split import split


def construct_corpus(wiki_name, wiki_prefix, language, experiment, threshold):
    """
    Create a corpus from a given wiki

    :param wiki_name: name of the wikia dump to parse
    :type wiki_name: str
    :param wiki_prefix: prefix for special pages of this wiki (will be ingored)
    :type wiki_prefix: str
    :param language: language of this wiki
    :type language: str
    :param experiment: name of the experiment
    :type experiment: str
    :param threshold: if higher than 0, only files with sentence-based threshold over given threshold are considered
    :type threshold: int
    """
    # Parse dump
    extract_articles(wiki_name, wiki_prefix)
    parse_texts(wiki_name, wiki_prefix, language)

    # Assign candidates
    assign(wiki_name, experiment, language)

    # Prepare evaluation
    aggregate_label_scores(wiki_name, experiment)
    prepare_manual_evaluation(wiki_name, experiment)

    # Apply threshold and split
    random.seed(42)
    split(wiki_name, experiment, threshold)


if __name__ == "__main__":
    wiki_name = sys.argv[1]
    wiki_prefix = sys.argv[2]
    language = sys.argv[3]
    experiment = sys.argv[4]
    threshold = int(sys.argv[5])

    construct_corpus(wiki_name, wiki_prefix, language, experiment, threshold)
