import nltk
from pulp import *


def convert_raw_text(text, stopword_set):
    """
    Convert given raw text into list of dictionaries representing each sentence

    :param text: text to convert
    :type text: str
    :param stopword_set: set of stopwords in a corresponding language
    :type stopword_set: set[str]
    :return: list of sentence representations
    :rtype: list[dict[str, any]]
    """
    text_sentences = [(s, s.lower().split(" ")) for s in text.split(".")]
    return [
        {"concepts": [f"{b0} {b1}" for b0, b1 in nltk.bigrams(s_tokens) if not (b0 in stopword_set and b1 in stopword_set)],
         "length": len(s_tokens),
         "tokens": s_tokens,
         "untokenized_form": s,
         "position": i}
        for i, (s, s_tokens) in enumerate(text_sentences)]


def convert_preprocessed_text(sentences, stopword_set):
    """
    Convert a given list of already preprocessed sentences into the format needed here

    Each input sentence representation is expected to have at least the following attributes
    text, tokens, sentence_id, word_count

    :param sentences: list of sentence-info-object
    :type sentences: list[dict[str, any]]
    :param stopword_set: set of stopwords in a corresponding language
    :type stopword_set: set[str]
    :return: list of sentence representations
    :rtype: list[dict[str, any]]
    """
    return [
        {"concepts": [f"{b0} {b1}" for b0, b1 in nltk.bigrams(sent["tokens"]) if not (b0 in stopword_set and b1 in stopword_set)],
         "length": sent["word_count"],
         "tokens": sent["tokens"],
         "untokenized_form": sent["text"],
         "position": sent["sentence_id"]}
        for sent in sentences]


def generate_concept_weights(text, stopword_set):
    """
    Generate a dictionary of concept weights for a given raw text

    :param text: raw target text
    :type text: str
    :param stopword_set: set of stopwords in a corresponding language
    :type stopword_set: set[str]
    :return: dictionary of concept weights
    :rtype: dict[str, int]
    """
    concept_weights = dict()
    for sentence in nltk.sent_tokenize(text):
        for b in [f"{b0} {b1}" for b0, b1 in nltk.bigrams(sentence.lower().split(" ")) if not (b0 in stopword_set and b1 in stopword_set)]:
            concept_weights[b] = concept_weights.get(b, 0) + 1
    return concept_weights


def recreate_text_concept_based(source_text_processed, concept_weights, TARGET_LENGTH):
    """
    Try to represent a given target text (represented by its concept weights) with sentences from a given source text

    :param source_text_processed: text to pool from (preprocessed)
    :type source_text_processed: list[dict[str, any]]
    :param concept_weights: dictionary of weights representing the value of concepts in the target text
    :type concept_weights: dict[str, int]
    :param TARGET_LENGTH: desired length (maximum) of the recreated summary
    :type TARGET_LENGTH: int
    :return: list of binary values (0, 1) representing whether a sentence is part of the extractive summary or not
    :rtype: list[int]
    """
    # Sort concepts by their weight (descending)
    concepts = sorted(concept_weights, key=concept_weights.get, reverse=True)
    COUNT_CONCEPTS = len(concepts)  # count of distinct concepts
    COUNT_SENTENCES = len(source_text_processed)  # count of sentences

    # formulation of the ILP problem

    prob = LpProblem("Recreate Text with Extracted Sentences Problem", LpMaximize)

    # initialize the concepts binary variables
    c = pulp.LpVariable.dicts(name='c',
                              indexs=range(COUNT_CONCEPTS),
                              lowBound=0,
                              upBound=1,
                              cat='Integer')

    # initialize the sentences binary variables
    s = pulp.LpVariable.dicts(name='s',
                              indexs=range(COUNT_SENTENCES),
                              lowBound=0,
                              upBound=1,
                              cat='Integer')

    # OBJECTIVE FUNCTION
    prob += pulp.lpSum(concept_weights[concepts[i]] * c[i] for i in range(COUNT_CONCEPTS))

    # CONSTRAINT FOR SUMMARY SIZE
    prob += pulp.lpSum(s[j] * source_text_processed[j]["length"] for j in range(COUNT_SENTENCES)) <= TARGET_LENGTH

    # INTEGRITY CONSTRAINTS
    for i in range(COUNT_CONCEPTS):
        for j in range(COUNT_SENTENCES):
            if concepts[i] in source_text_processed[j]["concepts"]:
                prob += s[j] <= c[i]

    for i in range(COUNT_CONCEPTS):
        prob += pulp.lpSum(s[j] for j in range(COUNT_SENTENCES)
                           if concepts[i] in source_text_processed[j]["concepts"]) >= c[i]

    # solving the ilp problem
    prob.solve()

    # retrieve the optimal subset of sentences
    labels = [int(s[i].varValue) for i in range(COUNT_SENTENCES)]
    score = pulp.value(prob.objective)
    solution = [source_text_processed[j] for j in range(COUNT_SENTENCES) if s[j].varValue == 1]
    solution_text = "\n".join(s["untokenized_form"] for s in solution)
    solution_length = sum(s["length"] for s in solution)

    print("Status:", LpStatus[prob.status])
    print("Score:", score)
    print("Labels:", labels)
    print("Solution length:", solution_length)
    print("Solution:", solution_text)

    return labels, score, solution_length, solution_text


def recreate_text_sentence_based(source_text_processed, concept_weights, TARGET_LENGTH):
    """
    Try to represent a given target text with sentences from a given source text
    without forcing the system to prefer sentences with concepts not used yet

    :param source_text_processed: text to pool from (preprocessed)
    :type source_text_processed: list[dict[str, any]]
    :param concept_weights: dictionary of weights representing the value of concepts in the target text
    :type concept_weights: dict[str, int]
    :param TARGET_LENGTH: desired length (maximum) of the recreated summary
    :type TARGET_LENGTH: int
    :return: list of binary values (0, 1) representing whether a sentence is part of the extractive summary or not
    :rtype: list[int]
    """
    COUNT_SENTENCES = len(source_text_processed)  # count of sentences

    # formulation of the ILP problem

    prob = LpProblem("Recreate Text with Extracted Sentences Non-Distinct Problem", LpMaximize)

    # initialize the sentences binary variables
    s = pulp.LpVariable.dicts(name='s',
                              indexs=range(COUNT_SENTENCES),
                              lowBound=0,
                              upBound=1,
                              cat='Integer')

    # OBJECTIVE FUNCTION
    prob += pulp.lpSum(s[j] * sum(concept_weights.get(concept, 0) for concept in source_text_processed[j]["concepts"]) for j in range(COUNT_SENTENCES))

    # CONSTRAINT FOR SUMMARY SIZE
    prob += pulp.lpSum(s[j] * source_text_processed[j]["length"] for j in range(COUNT_SENTENCES)) <= TARGET_LENGTH

    # solving the ilp problem
    prob.solve()

    # retrieve the optimal subset of sentences
    labels = [int(s[i].varValue) for i in range(COUNT_SENTENCES)]
    score = pulp.value(prob.objective)
    solution = [source_text_processed[j] for j in range(COUNT_SENTENCES) if s[j].varValue == 1]
    solution_text = "\n".join(s["untokenized_form"] for s in solution)
    solution_length = sum(s["length"] for s in solution)

    print("Status:", LpStatus[prob.status])
    print("Score:", score)
    print("Labels:", labels)
    print("Solution length:", solution_length)
    print("Solution:", solution_text)

    return labels, score, solution_length, solution_text


if __name__ == "__main__":
    stopword_set = set(sw.lower() for sw in nltk.corpus.stopwords.words('english'))
    source_text_processed = convert_raw_text("A B C. F G H.", stopword_set)
    concept_weights = generate_concept_weights("D E F G. A B.", stopword_set)

    TARGET_LENGTH = 3

    recreate_text_concept_based(source_text_processed, concept_weights, TARGET_LENGTH)
    recreate_text_sentence_based(source_text_processed, concept_weights, TARGET_LENGTH)
