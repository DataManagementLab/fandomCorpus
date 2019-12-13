---
title: Fandom Corpus Framework - Usage
---

## Usage

[Back to overview](. "Back to overview")

### Input data

The framework currently works on mediawiki database dumps. However, it could be used on other data as well when replacing the `extract_articles` method in `parse_dump.py` with a suitable reader. The database dump is expected to be in the `wikiadumps` subfolder of the `data` folder.

### Using the construction script

A corpus can be built be simply running the construction script with some suitable parameters:

	python3 construct.py CORPUS_NAME WIKI_PREFIX LANGUAGE EXPERIMENT_NAME QUALITY_TRESHOLD

In the following, we will explain these parameters:

-  **CORPUS_NAME:** Name of the folder of the resulting corpus. Has to be the same as the name of the database dump (without file ending)
-  **WIKI_PREFIX:** Name of the wiki this corpus is based on (e.g., *Wookieepedia*, *Harry_Potter_Wiki*). Will be used to exclude special pages
-  **LANGUAGE:** Language of the corpus (e.g., *english*, *german*). Needed for correct language operations like tokenization
-  **EXPERIMENT_NAME:** Name of the subfolder the resulting corpus should be in. Useful for multiple variants of a corpus or other usages of the data. As default, *mds* can be used.
-  **QUALITY_TRHESHOLD:** Higher values result in better quality of the data but less returned articles. As default value, one fifth of the target length (e.g., 50 for a target length of 250) can be used.

Sample call:

	python3 construct.py starwars-en Wookieepedia english mds 50

Other parameters like the target length can be varied in the files of the individual construction steps directly and are explained there. It is possible to run all stages of the pipeline independently, the usage is explained in every file.

[Back to overview](. "Back to overview")