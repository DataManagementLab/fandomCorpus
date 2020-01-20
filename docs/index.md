---
title: Fandom Corpus Framework - Index
---

Fandom Corpus is a framework to create topic-specific multi-document summariazation (mds) corpora. An overview over the pipeline can be found in the following figure:

![](pipeline.png)

The essential steps of our approach are: (1) parsing and cleaning of input documents, (2) selecting potential candidates for abstractive summaries from those input documents and assigning summary candidates to them, and (3) choosing the
final set of abstractive summaries based upon a new quality threshold and splitting the selected summaries into training,
validation, and test set if needed.


### Licence & Citatation

The code is published under a MIT License. If you are using the system for research, please cite our work as follows.

> tba


### Data

[Dowload the data and read about its structure](data.md).


### Usage

Read about [how to use the framework](usage.md).