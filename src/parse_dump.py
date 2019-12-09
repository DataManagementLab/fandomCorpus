import html
import json
import re
import sys
import nltk
import logging

import shutil
import wikitextparser as wtp
import xml.etree.ElementTree as ET
from os import path, listdir, makedirs


DATA_PATH = "../data"

XML_NAMESPACE = "{http://www.mediawiki.org/xml/export-0.10/}"
XML_IGNORE = ['File:', 'Help:', 'User:', 'User talk:', 'Category:', 'Thread:', 'Talk:', 'Message Wall:', 'Board Thread:', 'Sandbox:', 'MediaWiki:', 'Template:', 'Board:', 'File talk:', 'Category talk:', 'Template talk:', 'Forum:', 'Property:', 'User blog:', 'User blog comment:', 'Image:']
XML_IGNORE += ['Datei:', 'Hilfe:', 'Benutzer', 'Benutzer Diskussion:', 'Kategorie:', 'Thread:', 'Diskussion:', 'Message Wall:', 'Board Thread:', 'Sandbox:', 'MediaWiki:', 'Vorlage:', 'Board:', 'Datei Diskussion:', 'Kategorie Diskussion:', 'Vorlage Diskussion:', 'Forum', 'Property:']
XML_ARTICLE_NAMESPACE = 0
XML_RESTRICT_TO_ARTICLE_NAMESPACE = True

TEXT_CLEAN_SECTIONS_IGNORE = ["Sources", "__NOWYSIWYG__", "See also"]

# Ignore sentences/lines with markup (e.g., bullet point lists, tables, ...)
BAD_SENTENCE_PREFIXES = ['*', '|','Category:', '#', '!', '{', 'align', 'width', ']]']

# Prepare filename cleaning
filename_cleaner = re.compile(r'[^a-zA-Z0-9 ()_-]')

# Prepare text cleaning
comment_cleaner = re.compile(r'<!--.*?-->')


def get_base_path(wiki_name):
    """
    Get base path for a given wiki

    :param wiki_name: name of the wikia dump to parse
    :type wiki_name: str
    :return: base path for this wiki data
    :rtype: str
    """
    return path.join(DATA_PATH, wiki_name)


def get_article_path(wiki_name):
    """
    Get path for raw files for a given wiki

    :param wiki_name: name of the wikia dump to parse
    :type wiki_name: str
    """
    return path.join(DATA_PATH, wiki_name, "raw")


def get_clean_filename(title):
    """
    Remove unwanted chars from title to generate usable filename
    :param title: title to clean
    :type title: str
    :return: cleaned filename
    :rtype: str
    """
    return filename_cleaner.sub("_", title.replace(": ", "__"))


def get_article_json(article_name, wiki_name):
    """
    Get text (from all sections) for a given article

    :param article_name: name of the article
    :type article_name: str
    :param wiki_name: name of the wiki (for path determination)
    :type wiki_name: str
    :return: json object representing the article
    :rtype: Dict[str]
    """
    filename = path.join(get_article_path(wiki_name), article_name + ".json")
    try:
        with open(filename, "r") as file:
            article_info = json.load(file)
            return article_info
    except FileNotFoundError:
        logging.warning(f"File {filename} not found")
        return None


def get_article_text(article_name, wiki_name, article_info = None):
    """
    Get text (from all sections) for a given article

    :param article_name: name of the article
    :type article_name: str
    :param wiki_name: name of the wiki (for path determination)
    :type wiki_name: str
    :param article_info: article information dict (if already present)
    :type article_info: dict[str]
    :return: text of the article
    :rtype: str
    """
    if article_info is None:
        article_info = get_article_json(article_name, wiki_name)

    if article_info is None:
        return ""

    if "sections" not in article_info:
        return ""

    return "\n".join(section["text"] for section in article_info["sections"])


def adapt_ignores(wiki_prefix):
    """
    Adapt list of ignores based on given wiki prefix

    :param wiki_prefix: prefix for special pages of this wiki (will be ingored)
    :type wiki_prefix: str
    :return: set of categories to ignore
    :rtype: set(str)
    """
    xml_ignore_adapted = set(XML_IGNORE)
    xml_ignore_adapted.add(wiki_prefix + ":")
    xml_ignore_adapted.add(wiki_prefix + " Talk:")
    xml_ignore_adapted.add(wiki_prefix + " Diskussion:")
    return xml_ignore_adapted


def extract_articles(wiki_name, wiki_prefix):
    """
    Parse wikia dump into json files

    :param wiki_name: name of the wikia dump to parse
    :type wiki_name: str
    :param wiki_prefix: prefix for special pages of this wiki (will be ingored)
    :type wiki_prefix: str
    """
    # Adapt ingore list
    xml_ignore_adapted = adapt_ignores(wiki_prefix)

    # Prepare output
    output_path = get_article_path(wiki_name)
    makedirs(output_path, exist_ok=True)

    # Parse wikia database dump
    print("Reading dump...")
    tree = ET.parse(DATA_PATH + "/wikiadumps/" + wiki_name + ".xml")
    wikia_dump = tree.getroot()

    article_count = 0
    # Extract articles from dump
    print("Extracting articles...")
    for page in wikia_dump.findall(XML_NAMESPACE + 'page'):
        # Ignore redirect pages
        redirect_node = page.find(XML_NAMESPACE + 'redirect')
        if redirect_node is not None:
            continue

        if XML_RESTRICT_TO_ARTICLE_NAMESPACE:
            # Only extract from a certain namespace
            namespace = page.find(XML_NAMESPACE + 'ns')
            if int(namespace.text) != XML_ARTICLE_NAMESPACE:
                continue

        # Ignore special pages
        title_node = page.find(XML_NAMESPACE + 'title')
        title = title_node.text
        if any(title.startswith(ignore_string) for ignore_string in xml_ignore_adapted):
            continue

        # Extract raw text
        text = page.find(XML_NAMESPACE + 'revision').find(XML_NAMESPACE + 'text').text

        # Ignore articles without text
        if text is not None:
            print(title)
            # Create filename from title
            cleaned_title = get_clean_filename(title)
            id = page.find(XML_NAMESPACE + 'id').text

            # Make sure the __NOWYSIWYG__ area is treated as a section
            text = text.replace("__NOWYSIWYG__", "==__NOWYSIWYG__==")

            info = {
                "id": id,
                "title": title,
                "cleaned_title": cleaned_title,
                "raw_text": text}

            with open(path.join(output_path, cleaned_title + ".json"), "w") as output_file:
                json.dump(info, output_file, indent=2)
            article_count += 1

    print(f"Extracted {article_count} articles\n")


def _parse_sections(parsed_text, ignores, language='english'):
    """
    Parse sections of a given parsed raw text

    :param parsed_text: raw text parsed with wikitextparser
    :type parsed_text: wikitextparser.WikiText
    :param language: language of this wiki
    :type language: str
    :return: list of section info objects
    :rtype: list[dict]
    """
    parsed_sections = []

    # Extract text and other information for all sections
    # (and ignore certain sections (that do not hold textual information)
    for section in parsed_text.sections:
        if section.title not in TEXT_CLEAN_SECTIONS_IGNORE and section.contents != "":
            # Extract all links (potential source documents from the section text)
            # but ignore links to ignored page categories
            section_links = list(set(wl.target for wl in section.wikilinks if all(not(wl.target.startswith(s)) for s in ignores)))

            # Clean text for further usage
            # Remove all templates and html tags (mainly ref links)
            for template in section.templates:
                try:
                    del template[:]
                except IndexError:
                    pass
            for html_tag in section.tags():
                try:
                    del html_tag[:]
                except IndexError:
                    pass
            section_text = section.contents

            # Ignore subsections
            subsection_equal_string = "=" * (section.level + 1)
            begin_subsection_index = section_text.find(subsection_equal_string)
            if begin_subsection_index > -1:
                section_text = section_text[:begin_subsection_index]

            # Remove all file and image links:
            section_text = re.sub(r"\[\[(File:|Image:)([^\]]+)\]\]", r"", section_text)
            # Replace all links with their link texts:
            section_text = re.sub(r"\[\[([^|\]]*\|)?([^\]]+)\]\]", r"\2", section_text)

            # Remove special chars and unneeded whitespace
            section_text = section_text.replace("'''", "")
            section_text = section_text.strip()

            # Unescape html chars
            section_text = html.unescape(section_text)

            # Remove empty lines, lists of bullet points, tables and other unwanted markup
            # (although they might be interesting for some applications we are mainly interested in running text)
            section_sentences = [sent.strip() for sent in nltk.sent_tokenize(section_text, language=language) if sent.strip() != "" and not any(sent.startswith(prefix) for prefix in BAD_SENTENCE_PREFIXES)]

            # Make sure there is still content left after cleaning...
            if len(section_sentences) > 0:
                cleaned_text = "\n".join(section_sentences)
                # section_tokens = nltk.word_tokenize(cleaned_text)
                # ... compile all necessary information...
                section_info = {
                    "title": section.title,
                    "length": len(nltk.word_tokenize(cleaned_text, language=language)),
                    "links": section_links,
                    # Store each sentence in a new line (required by many summarization systems)
                    "text": cleaned_text,
                    # "tokens": section_tokens
                }
                # ... and store it
                parsed_sections.append(section_info)

    return parsed_sections


def get_article_jsons(wiki_name):
    """
    Get all article json files for a given wiki
    :param wiki_name: name of the wiki
    :type wiki_name: str
    :return: list of all matching file paths
    :rtype: list[str]
    """
    raw_path = get_article_path(wiki_name)
    return [path.join(raw_path, file) for file in listdir(raw_path) if file.endswith(".json")]


def parse_texts(wiki_name, wiki_prefix, language='english'):
    """
    Parse raw texts for a given wiki (json files from extraction need to be present)
    :param wiki_name: name of the wikia dump to parse
    :type wiki_name: str
    :param wiki_prefix: prefix for special pages of this wiki (will be ingored)
    :type wiki_prefix: str
    :param language: language of this wiki
    :type language: str
    """
    # Process raw files
    print("Parsing raw text...")

    ignores_list = list(adapt_ignores(wiki_prefix))

    article_json_files = get_article_jsons(wiki_name)

    files_with_empty_sections_path = path.join(get_article_path(wiki_name), "empty")

    makedirs(files_with_empty_sections_path, exist_ok=True)

    for article_json_filename in article_json_files:
        with open(article_json_filename, "r") as article_json_file:
            info = json.load(article_json_file)
            print(info['title'])

            # Do basic pre-processing of raw text
            raw_text = comment_cleaner.sub("", info['raw_text'])
            # Parse raw text using wikitextparser
            parsed_text = wtp.parse(raw_text)

            # Determine and store categories
            info["categories"] = [wl.target[9:] for wl in parsed_text.wikilinks if wl.target.startswith("Category")]

            # Extract text and other information for all sections
            # (and ignore certain sections (that do not hold text)
            parsed_sections = _parse_sections(parsed_text, ignores_list, language)

            # Store information about parsed sections (and clear it if already present)
            info['sections'] = parsed_sections

        if len(info['sections']) > 0:
            with open(article_json_filename, "w") as article_json_file:
                json.dump(info, article_json_file, indent=2)
        else:
            # Move empty files to subfolder
            shutil.move(article_json_filename, files_with_empty_sections_path)


if __name__ == "__main__":
    wiki_name = sys.argv[1]
    wiki_prefix = sys.argv[2]
    if len(sys.argv) > 3:
        language = sys.argv[3]
    else:
        language = "english"

    extract_articles(wiki_name, wiki_prefix)
    parse_texts(wiki_name, wiki_prefix, language)

