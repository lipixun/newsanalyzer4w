# encoding=utf8

""" The main
    Author: lipixun
    Created Time : 日  2/12 14:16:10 2017

    File Name: main.py
    Description:

"""

import sys
reload(sys)
sys.setdefaultencoding("utf8")

import math
import logging
logger = logging.getLogger("newsanalyzer")

from os.path import expanduser
from argparse import ArgumentParser
from collections import Counter

from spec import IDFDictFilename
from utils import nltk, json
from excelio import ExcelInput
from analyzer import NewsAnalyzer

def main(args):
    """The application main entry
    """
    args = getArguments(args)
    if args.debug:
        logging.basicConfig(format = "%(asctime)s - %(levelname)s - %(name)s - %(message)s", level = logging.DEBUG)
    else:
        logging.basicConfig(format = "%(asctime)s - %(levelname)s - %(name)s - %(message)s", level = logging.INFO)
    # Check actions
    if args.action == "prepare-nltk":
        logger.info("Start prepare nltk data")
        nltk.download()
    elif args.action == "prepare-idf":
        logger.info("Start prepare idf directory (by calculating on nltk reuters corpus)")
        counter = Counter()
        for docWords in nltk.corpus.reuters.sents():
            # Single word
            for word in docWords:
                counter[word.lower()] += 1
            # Double
            for i in xrange(0, len(docWords) - 1):
                counter[(docWords[i].lower(), docWords[i + 1].lower())] += 1
            # Triple
            for i in xrange(0, len(docWords) - 2):
                counter[(docWords[i].lower(), docWords[i + 1].lower(), docWords[i + 2].lower())] += 1
            # Four
            for i in xrange(0, len(docWords) - 3):
                counter[(docWords[i].lower(), docWords[i + 1].lower(), docWords[i + 2].lower(), docWords[i + 3].lower())] += 1
        idf = {}
        for word, count in counter.iteritems():
            if count > 5:
                idf[word] = math.log(float(len(counter)) / float(count))
        with open(IDFDictFilename, "wb") as fd:
            json.dump([ {"w": k, "v": v } for k, v in idf.iteritems() ], fd, ensure_ascii = False)
    elif args.action == "keyword":
        return getKeyWords(args)
    elif args.action == "cooccurrence":
        return cooccurrence(args)
    elif args.action == "cooccurrence-entity":
        return cooccurrenceEntity(args)
    else:
        raise ValueError("Unknown action [%s]" % args.action)

def getArguments(args):
    """Get arguments from args
    """
    parser = ArgumentParser(prog = "newsanalyzer", description = "News Analyzer For WanXuanAo")
    parser.add_argument("--debug", dest = "debug", default = False, action = "store_true", help = "Enable debug mode")
    subParsers = parser.add_subparsers(dest = "action")
    # Prepare
    _ = subParsers.add_parser("prepare-nltk", help = "Prepare nltk")
    _ = subParsers.add_parser("prepare-idf", help = "Prepare idf directory")
    # keyword
    keywordParser = subParsers.add_parser("keyword", help = "Run keyword analyzer")
    keywordParser.add_argument("-i", "--input", dest = "input", required = True, help = "Input excel file")
    keywordParser.add_argument("--output-title", dest = "outputTitle", default = "~/Desktop/keywords-title.txt", help = "Mined from title output file")
    keywordParser.add_argument("--output-content", dest = "outputContent", default = "~/Desktop/keywords-content.txt", help = "Mined from content output file")
    # Cooccurrence
    cooccurrenceParser = subParsers.add_parser("cooccurrence", help = "Run co-occurrence analyzer")
    cooccurrenceParser.add_argument("-i", "--input", dest = "input", required = True, help = "Input excel file")
    cooccurrenceParser.add_argument("-o", "--output", dest = "output", default = "~/Desktop/cooccurrence.txt", help = "Output file")
    cooccurrenceParser.add_argument("words", nargs = "*", help = "The words")
    # Cooccurrence entity
    cooccurrenceEntityParser = subParsers.add_parser("cooccurrence-entity", help = "Run co-occurrence entity analyzer")
    cooccurrenceEntityParser.add_argument("-i", "--input", dest = "input", required = True, help = "Input excel file")
    cooccurrenceEntityParser.add_argument("-o", "--output", dest = "output", default = "~/Desktop/cooccurrence-entity.txt", help = "Output file")
    cooccurrenceEntityParser.add_argument("words", nargs = "*", help = "The words")
    # Done
    return parser.parse_args(args)

def loadNews(excelInput):
    """Load news
    """
    logger.info("Load news")
    return list(excelInput.news)

def normalizeFilename(filename):
    """Normalize filename
    """
    return expanduser(filename)

def readWords():
    """Read words
    """
    words = []
    while True:
        try:
            print u"输入单词（只输入一个比如USA或者China South Sea）：，不输入直接会车表示完成：",
            word = raw_input().strip()
            if not word:
                return words
            words.append(word)
        except EOFError:
            return words

def getKeyWords(args):
    """Get keywords
    """
    # Load excel
    logger.info("Load excel")
    excelInput = ExcelInput(args.input)
    # Load news
    news = loadNews(excelInput)
    # Run analyzer
    analyzer = NewsAnalyzer(excelInput.countries, excelInput.regions, excelInput.provinces, excelInput.cities)
    analyzer.prepare()
    logger.info("Start analyze keywords")
    return analyzer.getKeywords(news, normalizeFilename(args.outputTitle), normalizeFilename(args.outputContent))

def cooccurrence(args):
    """Get cooccurrence
    """
    # Load excel
    logger.info("Load excel")
    excelInput = ExcelInput(args.input)
    # Load news
    news = loadNews(excelInput)
    # Run analyzer
    analyzer = NewsAnalyzer(excelInput.countries, excelInput.regions, excelInput.provinces, excelInput.cities)
    analyzer.prepare()
    # Check words
    if not args.words:
        # Read words
        words = readWords()
    else:
        words = args.words
    # Run
    logger.info("Start analyze co-occurrence on words: %s", ",".join(words))
    return analyzer.cooccurrence(news, words, normalizeFilename(args.output))

def cooccurrenceEntity(args):
    """Get cooccurrence entity
    """
    # Load excel
    logger.info("Load excel")
    excelInput = ExcelInput(args.input)
    # Load news
    news = loadNews(excelInput)
    # Run analyzer
    analyzer = NewsAnalyzer(excelInput.countries, excelInput.regions, excelInput.provinces, excelInput.cities)
    analyzer.prepare()
    # Check words
    if not args.words:
        # Read words
        words = readWords()
    else:
        words = args.words
    # Run
    logger.info("Start analyze co-occurrence on words: %s", ",".join(words))
    return analyzer.cooccurrenceEntity(news, words, normalizeFilename(args.output))
