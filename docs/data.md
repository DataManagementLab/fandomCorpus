---
title: Fandom Corpus Framework - Data
---

## Data

[Back to overview](. "Back to overview")

As part of the paper, we constructed three sample corpora from three fandom.org wikis: Star Wars (en) from [Wookieepedia](https://starwars.fandom.com/wiki/Main_Page "Wookieepedia"), Star Wars (de) from [Jedipedia](https://jedipedia.fandom.com/wiki/Jedipedia:Hauptseite "Jedipedia") (in German) and Harry Potter from the [Harry Potter Wiki](https://harrypotter.fandom.com/wiki/Main_Page "Harry Potter Wiki").

We downloaded current database dumps of these wikis and performed the steps of the pipeline on them: (1) parsing and cleaning of input documents, (2) selecting potential candidates for abstractive summaries from those input documents and assigning summary candidates to them, and (3) choosing the
final set of abstractive summaries based upon a new quality threshold and splitting the selected summaries into training, validation, and test set. They steps are described in more detail in the paper.

### Download

The resulting files from that process can be dowloaded here:

- [Star Wars (en) Corpus](https://hessenbox.tu-darmstadt.de/getlink/fi4azgjQD5yW7wzvoAPV8qg6/sw-en-mds.zip) (1,5 GB)
- [Star Wars (de) Corpus](https://hessenbox.tu-darmstadt.de/getlink/fiNeP2HKcvj2H9mLcEqsGtYf/sw-de-mds.zip) (185 MB)
- [Harry Potter Corpus](https://hessenbox.tu-darmstadt.de/getlink/fiHaqN6im7ewthjePhNc4zCt/harrypotter-mds.zip) (800 MB)


### Structure

Each corpus consists of a folder structure containing the preprocessed input files, human written as well as automatically generated summaries and meta data with the following structure:

    mds
	+-extractive-concept-based
	+-extractive-sentence-based
	+-human-abstracts
	+-human-evaluation
	+-inputs
	+-labels-concept-based
	+-labels-sentence-based

All folders have subfolders like

	+-extractive-concept-based
	 +-train-50
	 +-test-50
	 +-valid-50

for the different sets, where 50 is the quality threshold applied. Hence the first level folder contain all the data while the subfolders only contain references to the files over the given quality threshold. The affected files from the random-based split can be found in the ``corpus_name.split.$threshold.json`` file in the top folder.

The contents of the folders are

- **inputs**: The preprocessed input files, containing the textual sources and some meta data (json)
- **extractive-concept-based** and **extractive-sentence-based**: The automatically constructed extractive summaries using both building strategies from the paper (txt)
- **human-abstracts**: The human-written texts that are used as summaries (txt)
- **human-evaluation**: Files ready for annotation to manually analyze the quality (json)
- **labels-concept-based** and **labels-sentence-based**: Binary decission for each sentence from the input files whether it is included in the extractive summary or not (json)

the structure of the contained files will now be described in detail.

### Inputs

JSON file containing the source texts and meta data with the following structure:
	
	{
		"id": str,						# id of this file
		"query": str,					# query/headline of this summary
		"target_length": int,			# length of the abstractive summary
		"overlap": float,				# overlap between source texts and target text (in %, based on strategy)
		"source_doc_count": int,		# amount of different source docs
		"source_overall_length": int,	# total length of all source docs concatenated (in words)
		"source_doc_names": [			# list of all source document names
		    list of str
		  ],
		"inputs": [						# list of all input sentences
			{
				"text": str,			# text of this sentence
				"tokens": [				# tokens of this sentence
					list of str
				],
				"pos": [
					[str, str],			# POS tags of this sentence word by word
					...					# list of str-tuples (a tuple is a two-element list in json)
				],
				"doc_id": int,			# to which of the different source docs does this sentence belong
				"sentence_id": int,		# index of this sentence in doc
				"word_count": int		# lenght (words) of this sentence
			},
			...
		]
	}


### Labels

JSON file containing labels for extractive summarization with the following structure:

	{
		"id": str,						# id of this file
		"score": int,					# optimization objective score from automatical summarization construction
		"text": str,					# text of the extractive summary
		"length": int,					# length of the extractive summary (words)
		"labels": [						# binary decision whether the sentence with this index
			list of int					# is part of the summary or not
		 ]
	}

### Human abstracts

Text file containing all sentences of the human-written summary, one sentence per line. The filename is ``summary_id.1.txt``.

### Extractive summaries

Text file containing all sentences of the extractive summary, one sentence per line. The filename is ``summary_id.1.txt``.

### Human evaluation files

JSON file for human annotation/quality review of the extractive summaries with the following structure:

	{
		"done": bool,					# was this file already annotated?
		"strategy-name": {				# one entry per strategy
			"summary": str,				# text of the extractive summary
			"covered": [				# list of all sentences in the human summary
				{
					"sentence": str,	# sentence of the human summary
					"is_covered": int	# score indicating how good it was covered
				},
				...
			]
		}
	}


[Back to overview](. "Back to overview")