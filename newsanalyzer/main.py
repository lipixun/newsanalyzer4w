# encoding=utf8

""" The main
    Author: lipixun
    Created Time : 日  2/12 14:16:10 2017

    File Name: main.py
    Description:

"""

import math
import logging

from os.path import expanduser, isfile
from argparse import ArgumentParser
from collections import Counter

from .spec import IDFDictFilename
from .utils import nltk, json
from .model import News, NamedKeyword
from .excelio import ExcelInput
from .analyzer import NewsAnalyzer

logger = logging.getLogger("newsanalyzer")

def getArguments(args):
    """Get arguments from args
    """
    parser = ArgumentParser(prog = "newsanalyzer", description = "News Analyzer For WanXuanAo")
    parser.add_argument("--debug", dest = "debug", default = False, action = "store_true", help = "Enable debug mode")
    subParsers = parser.add_subparsers(dest = "action")
    # Prepare
    _ = subParsers.add_parser("prepare-nltk", help = "Prepare nltk")
    prepareIDFParser = subParsers.add_parser("prepare-idf", help = "Prepare idf directory")
    prepareIDFParser.add_argument("-n", "--ngram", dest = "nGram", type = int, default = 6, help = "The nGram")
    # keyword
    keywordParser = subParsers.add_parser("keyword", help = "Run keyword analyzer")
    keywordParser.add_argument("-i", "--input", dest = "input", required = True, help = "Input excel file")
    keywordParser.add_argument("--text-title-input", dest = "textTitleInput", help = "The text title input")
    keywordParser.add_argument("--text-content-input", dest = "textContentInput", help = "The text content input")
    keywordParser.add_argument("-n", "--ngram", dest = "nGram", type = int, default = 6, help = "The nGram")
    keywordParser.add_argument("--output-title", dest = "outputTitle", default = "~/Desktop/keywords-title", help = "Mined from title output file")
    keywordParser.add_argument("--output-content", dest = "outputContent", default = "~/Desktop/keywords-content", help = "Mined from content output file")
    # Cooccurrence
    cooccurrenceParser = subParsers.add_parser("cooccurrence", help = "Run co-occurrence analyzer")
    cooccurrenceParser.add_argument("-i", "--input", dest = "input", required = True, help = "Input excel file")
    cooccurrenceParser.add_argument("--text-content-input", dest = "textContentInput", help = "The text content input")
    cooccurrenceParser.add_argument("-n", "--ngram", dest = "nGram", type = int, default = 6, help = "The nGram")
    cooccurrenceParser.add_argument("-o", "--output", dest = "output", default = "~/Desktop/cooccurrence", help = "Output file")
    cooccurrenceParser.add_argument("words", nargs = "*", help = "The words")
    # Cooccurrence entity
    cooccurrenceEntityParser = subParsers.add_parser("cooccurrence-entity", help = "Run co-occurrence entity analyzer")
    cooccurrenceEntityParser.add_argument("-i", "--input", dest = "input", required = True, help = "Input excel file")
    cooccurrenceEntityParser.add_argument("--text-content-input", dest = "textContentInput", help = "The text content input")
    cooccurrenceEntityParser.add_argument("-o", "--output", dest = "output", default = "~/Desktop/cooccurrence-entity", help = "Output file")
    cooccurrenceEntityParser.add_argument("words", nargs = "*", help = "The words")
    # Done
    return parser.parse_args(args)

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
        prepareNLTK(args)
    elif args.action == "prepare-idf":
        prepareIDF(args)
    elif args.action == "keyword":
        return getKeyWords(args)
    elif args.action == "cooccurrence":
        return cooccurrence(args)
    elif args.action == "cooccurrence-entity":
        return cooccurrenceEntity(args)
    else:
        raise ValueError("Unknown action [%s]" % args.action)

def prepareNLTK(_):
    """Prepare for nltk
    """
    logger.info("Start prepare nltk data")
    nltk.download()

def prepareIDF(args):
    """Prepare for idf
    """
    logger.info("Start prepare idf directory (by calculating on nltk reuters corpus)")
    # Count word per paragraph
    counter = Counter()
    paragraphCount = 0
    for paras in nltk.corpus.reuters.paras():
        words = set()
        for sentence in paras:
            for i in range(len(sentence)):
                for j in range(1, args.nGram + 1):
                    terms = [ x.lower() for x in sentence[i: i+j] ]
                    if len(terms) != j:
                        break
                    if len(terms) == 1:
                        words.add(terms[0])
                    else:
                        words.add(tuple(terms))
        for word in words:
            counter[word] += 1
        paragraphCount += 1
    # Calculate IDF score
    idf = {}
    for word, count in counter.iteritems():
        if count > 3:
            idf[word] = math.log(float(paragraphCount) / float(count))
    with open(IDFDictFilename, "wb") as fd:
        json.dump([ {"w": k, "v": v } for k, v in idf.iteritems() ], fd, ensure_ascii = False)

def loadNews(excelInput):
    """Load news
    """
    logger.info("Load news")
    return list(excelInput.news)

def normalizeFilename(filename):
    """Normalize filename
    """
    return expanduser(filename)

def loadTitleTexts(titleTextFile):
    """Load title texts from file
    """
    if isfile(titleTextFile):
        texts = []
        with open(titleTextFile, "rb") as fd:
            for content in fd:
                texts.append(unicode(content))
        return texts

def loadContentTexts(contentTextFile):
    """Load content texts from file
    """
    if isfile(contentTextFile):
        texts = []
        with open(contentTextFile, "rb") as fd:
            for content in fd:
                texts.append(unicode(content))
        return texts

def readWords():
    """Read words
    Returns:
        [ NamedKeyword ]: The input words
    """
    print u"输入关键词\n格式说明"
    print u"* 输入一个单词或者短语。比如USA或者China South Sea"
    print u"* 输入多个单词或短语，将这多组单词、短语当作一个词汇统计，使用英文逗号分隔。"
    print u"  比如America, usa。America以及usa两个单词的统计结果会合成为词汇[America,usa]的统计结果"
    keywords = []
    while True:
        try:
            print u"请输入，直接回车表示完成：",
            word = raw_input().strip()
            if not word:
                return keywords
            words = [ x.strip() for x in word.split(",") if x.strip() ]
            if words:
                keywords.append(NamedKeyword(",".join(words), words))
        except EOFError:
            return keywords

def getKeyWords(args):
    """Get keywords
    """
    # Load excel
    logger.info("Load excel")
    excelInput = ExcelInput(args.input)
    # Load news
    news = loadNews(excelInput)
    if args.textTitleInput:
        titles = loadTitleTexts(args.textTitleInput)
        if titles:
            news.extend([ News(title = x) for x in titles ])
        logger.info("Load [%d] lines from text title input", len(titles) if titles else 0)
    if args.textContentInput:
        contents = loadContentTexts(args.textContentInput)
        if contents:
            news.extend([ News(content = x) for x in contents ])
        logger.info("Load [%d] lines from text content input", len(contents) if contents else 0)
    # Run analyzer
    analyzer = NewsAnalyzer(excelInput.countries, excelInput.regions, excelInput.provinces, excelInput.cities)
    analyzer.prepare()
    logger.info("Start analyze keywords")
    return analyzer.getKeywords(args.nGram, news, normalizeFilename(args.outputTitle), normalizeFilename(args.outputContent))

def cooccurrence(args):
    """Get cooccurrence
    """
    # Load excel
    logger.info("Load excel")
    excelInput = ExcelInput(args.input)
    # Load news
    news = loadNews(excelInput)
    if args.textContentInput:
        contents = loadContentTexts(args.textContentInput)
        if contents:
            news.extend([ News(content = x) for x in contents ])
        logger.info("Load [%d] lines from text content input", len(contents) if contents else 0)
    # Run analyzer
    analyzer = NewsAnalyzer(excelInput.countries, excelInput.regions, excelInput.provinces, excelInput.cities)
    analyzer.prepare()
    # Read words
    if not args.words:
        # Read words
        keywords = readWords()
    else:
        keywords = []
        for word in args.words:
            words = [ x.strip() for x in word.split(",") if x.strip() ]
            if words:
                keywords.append(NamedKeyword(",".join(words), words))
    # Run
    logger.info("Start analyze co-occurrence on words: %s", "|".join([ x.name for x in keywords ]))
    return analyzer.cooccurrence(args.nGram, news, keywords, normalizeFilename(args.output))

def cooccurrenceEntity(args):
    """Get cooccurrence entity
    """
    # Load excel
    logger.info("Load excel")
    excelInput = ExcelInput(args.input)
    # Load news
    news = loadNews(excelInput)
    if args.textContentInput:
        contents = loadContentTexts(args.textContentInput)
        if contents:
            news.extend([ News(content = x) for x in contents ])
        logger.info("Load [%d] lines from text content input", len(contents) if contents else 0)
    # Run analyzer
    analyzer = NewsAnalyzer(excelInput.countries, excelInput.regions, excelInput.provinces, excelInput.cities)
    analyzer.prepare()
    # Read words
    if not args.words:
        # Read words
        keywords = readWords()
    else:
        keywords = []
        for word in args.words:
            words = [ x.strip() for x in word.split(",") if x.strip() ]
            if words:
                keywords.append(NamedKeyword(",".join(words), words))
    # Run
    logger.info("Start analyze co-occurrence on words: %s", "|".join([ x.name for x in keywords ]))
    return analyzer.cooccurrenceEntity(news, keywords, normalizeFilename(args.output))
