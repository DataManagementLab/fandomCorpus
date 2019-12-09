import json
import math
import sys
import logging
from os import path, makedirs

import nltk
from nltk import sent_tokenize, word_tokenize, pos_tag

from overlap import recreate_text_concept_based, convert_preprocessed_text, generate_concept_weights, \
    recreate_text_sentence_based
from parse_dump import get_article_jsons, DATA_PATH, get_clean_filename, get_article_text, \
    get_base_path


MIN_TARGET_LENGTH = 150
MAX_TARGET_LENGTH = 400
TARGET_LENGTH_EXTRACTIVE = 250
TARGET_SOURCE_RATIO = 2
MIN_SOURCE_DOC_COUNT = 5
MIN_OVERLAP = 50


def _compute_overlap(target_text, source_text_unified_tokens, language):
    """
    Compute bigram overlap between two given texts

    :param target_text: first text
    :type target_text: str
    :param source_text_unified_tokens: second text (list of tokens
    :type source_text_unified_tokens: list[str]
    :param language: language of the two texts
    :type language: str
    :return: percentage of bigram overlap between the given texts
    :rtype: float
    """
    # Compute bigram overlap
    target_text_tokens = nltk.word_tokenize(target_text, language)
    bigrams_target = nltk.bigrams(target_text_tokens)
    bigrams_source = set(nltk.bigrams(source_text_unified_tokens))
    bigrams_found_not_found = [1 if bigram in bigrams_source else 0 for bigram in bigrams_target]
    return sum(bigrams_found_not_found) / float(len(bigrams_found_not_found)) * 100


def assign(wiki_name, experiment='qf-mds', language="english"):
    """
    Determine which articles are suitable for single document summarization
    and apply train-dev-test-split

    :param wiki_name: name of the wikia dump to parse
    :type wiki_name: str
    :param experiment: construct abstractive or extractive summaries (extractive will only use documents with a certain portion of sentences from source documents reused)
    :type experiment: str
    :param language: language of this wiki
    :type language: str
    """
    language_short = language[:3]
    stopword_set = set(sw.lower() for sw in nltk.corpus.stopwords.words(language))

    # Process raw files
    print("Creating Query-Focused Multi Document Summarization corpus...")

    article_json_files = get_article_jsons(wiki_name)

    output_path_base = path.join(DATA_PATH, wiki_name, experiment)
    makedirs(output_path_base, exist_ok=True)

    output_path_inputs = path.join(output_path_base, "inputs")
    makedirs(output_path_inputs, exist_ok=True)

    output_path_labels_concept = path.join(output_path_base, "labels-concept-based")
    makedirs(output_path_labels_concept, exist_ok=True)

    output_path_extractive_concept = path.join(output_path_base, "extractive-concept-based")
    makedirs(output_path_extractive_concept, exist_ok=True)

    output_path_labels_non_distinct = path.join(output_path_base, "labels-sentence-based")
    makedirs(output_path_labels_non_distinct, exist_ok=True)

    output_path_extractive_sentence = path.join(output_path_base, "extractive-sentence-based")
    makedirs(output_path_extractive_sentence, exist_ok=True)

    output_path_human_abstracts = path.join(output_path_base, "human-abstracts")
    makedirs(output_path_human_abstracts, exist_ok=True)

    try:
        with open(path.join(get_base_path(wiki_name), wiki_name + ".json"), "r") as wiki_info_file:
            wiki_info = json.load(wiki_info_file)
            unwanted_categories = set(wiki_info["unwanted_categories"])
    except FileNotFoundError:
        unwanted_categories = set()

    candidates_count = 0

    # Padding for file identifiers according to the maximum number of articles
    padding_length = math.ceil(math.log(len(article_json_files), 10))

    output_statistics = []

    # Loop over all articles
    for article_json_filename in article_json_files:
        with open(article_json_filename, "r") as article_json_file:
            article_info = json.load(article_json_file)

            if "sections" not in article_info:
                continue

            # Consider only articles with multiple sections (since the first one is not query-focused)
            if len(article_info["sections"]) > 1:
                # Skip all stub articles and articles from unwanted categories
                if any(True for category in article_info["categories"] if "stub" in category.lower() or category in unwanted_categories):
                    logging.info(f"Ingore {article_info['title']} because of categories: {', '.join(article_info['categories'])}")
                    continue

                for section in article_info["sections"][1:]:
                    # Suitable sections need to have a certain length and enough source docs
                    target_length = section["length"]

                    # Clean links (remove-self references and section restrictions)
                    cleaned_source_doc_names = set(get_clean_filename(link.split('#')[0]) for link in section["links"] if not link.startswith('#'))
                    cleaned_source_doc_names = cleaned_source_doc_names.difference([article_info["cleaned_title"]])
                    source_doc_count = len(cleaned_source_doc_names)

                    # Check if section meets heuristic
                    if MIN_TARGET_LENGTH <= target_length <= MAX_TARGET_LENGTH and source_doc_count >= MIN_SOURCE_DOC_COUNT:
                        # Target
                        query = f"{article_info['title']}: {section['title']}"
                        target_text = section["text"]

                        # Get source text for further analyzing
                        source_texts = [(article, get_article_text(article, wiki_name)) for article in cleaned_source_doc_names]
                        source_texts = [(article, text) for article, text in source_texts if text != '']
                        source_doc_count = len(source_texts)

                        # Make sure that source doc count criterion is still met now that we tried to load the source docs
                        if source_doc_count < MIN_SOURCE_DOC_COUNT:
                            continue

                        source_text_unified = "\n".join(text for _, text in source_texts if text.strip() != '')
                        source_text_unified_tokens = nltk.word_tokenize(source_text_unified, language=language)

                        # Compute bigram overlap
                        target_source_overlap = _compute_overlap(target_text, source_text_unified_tokens, language)

                        # Ignore possible summaries with very little overlap
                        if target_source_overlap >= MIN_OVERLAP:
                            print(f"{candidates_count}: {query} [{target_length}, {source_doc_count}, {target_source_overlap:02.4f}]")

                            # Prepare output
                            output_prefix = f"{wiki_name}_{candidates_count:0{padding_length}d}"

                            # Output target text in new format
                            with open(path.join(output_path_human_abstracts, output_prefix) + ".1.txt", "w") as human_abstract_file:
                                human_abstract_file.write(target_text)

                            # Generate input representation
                            inputs = []
                            sent_id = 0
                            for doc_id, (_, text) in enumerate(source_texts):
                                for sent in sent_tokenize(text):
                                    tokenized_sent = word_tokenize(sent, language)
                                    sent_info = {
                                        "text": sent,
                                        "tokens": tokenized_sent,
                                        "pos": pos_tag(tokenized_sent, language_short),
                                        "doc_id": doc_id,
                                        "sentence_id": sent_id,
                                        "word_count": len(tokenized_sent)
                                    }
                                    inputs.append(sent_info)
                                    sent_id += 1

                            input_info = {
                                "id": output_prefix,
                                "query": query,
                                "target_length": target_length,
                                "overlap": target_source_overlap,
                                "source_doc_count": source_doc_count,
                                "source_overall_length": len(source_text_unified_tokens),
                                "source_doc_names": [article for article, _ in source_texts],
                                "inputs": inputs
                            }
                            with open(path.join(output_path_inputs, output_prefix) + ".json", "w") as input_file:
                                json.dump(input_info, input_file, indent=2)

                            concept_weights = generate_concept_weights(target_text, stopword_set)
                            source_text_processed = convert_preprocessed_text(inputs, stopword_set)

                            # Generate labels concept based...
                            labels, solution_score, solution_length, solution_text = recreate_text_concept_based(source_text_processed, concept_weights, TARGET_LENGTH_EXTRACTIVE)
                            labels_info = {
                                "id": output_prefix,
                                "score": solution_score,
                                "text": solution_text,
                                "length": solution_length,
                                "labels": labels,
                            }
                            with open(path.join(output_path_labels_concept, output_prefix) + ".json", "w") as labels_file:
                                json.dump(labels_info, labels_file, indent=2)

                            # Store raw text of this extractive summary
                            with open(path.join(output_path_extractive_concept, output_prefix) + ".1.txt", "w") as extractive_file:
                                extractive_file.write(solution_text)

                            # ... and sentence based
                            labels, solution_score, solution_length, solution_text = recreate_text_sentence_based(source_text_processed, concept_weights, TARGET_LENGTH_EXTRACTIVE)
                            labels_info = {
                                "id": output_prefix,
                                "score": solution_score,
                                "text": solution_text,
                                "length": solution_length,
                                "labels": labels,
                            }
                            with open(path.join(output_path_labels_non_distinct, output_prefix) + ".json", "w") as labels_file:
                                json.dump(labels_info, labels_file, indent=2)

                            # Store raw text of this extractive summary
                            with open(path.join(output_path_extractive_sentence, output_prefix) + ".1.txt", "w") as extractive_file:
                                extractive_file.write(solution_text)

                            candidates_count += 1

    print(f"Created {candidates_count} query-focused multi document summaries")


if __name__ == "__main__":
    wiki_name = sys.argv[1]
    if len(sys.argv) > 2:
        experiment = sys.argv[2]
    else:
        experiment = 'qf-mds'
    if len(sys.argv) > 3:
        language = sys.argv[3]
    else:
        language = "english"

    assign(wiki_name, experiment, language)
