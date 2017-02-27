# encoding=utf8

""" The analyzer
    Author: lipixun
    Created Time : 日  2/12 14:15:36 2017

    File Name: analyzer.py
    Description:

"""

import re
import logging

from sets import Set
from collections import Counter

from trie import TrieTree
from spec import IDFDictFilename, MissingValueIDF, DropWords, KeyCountry
from utils import nltk, json

PunctuationRegex = re.compile(r"""^[\!\"\#\$\%\&\'\(\)\*\+\,\-\.\/\:\;\<\=\>\?\@\[\\\]\^\_\`\{\|\}\~]+$""")

class NewsAnalyzer(object):
    """The new analyzer
    """
    logger = logging.getLogger("newsanalyzer.NewsAnalyzer")

    def __init__(self, countries = None, regions = None, provinces = None, cities = None, peoples = None):
        """Create a new NewsAnalyzer
        """
        self.countries = countries or []
        self.regions = regions or []
        self.provinces = provinces or []
        self.cities = cities or []
        self.peoples = peoples or []

    def prepare(self):
        """Prepare the data (by build the data relationship)
        """
        # Build country names dict
        countries = {}
        for country in self.countries:
            for name in country.alias:
                if name in countries:
                    self.logger.error("Duplicated country (alias) name found: %s of %s", name, country.name)
                else:
                    countries[name] = country
        # Check region to country
        for region in self.regions:
            regionCountries = []
            for country in region.countries:
                if not country in countries:
                    self.logger.error("Country [%s] of region [%s] not found in country list", country, region.name)
                else:
                    regionCountries.append(countries[country])
            # Use the standard country names
            region.countries = regionCountries

    def normalize(self, words):
        """Normalize the words
        """
        newWords = []
        for word in words:
            if word.endswith("'s"):
                word = word[:-2]
            word = word.strip()
            if word:
                newWords.append(word)
        return newWords

    def buildEntityTrieTree(self):
        """Build entity trie tree
        """
        self.logger.info("Build entity trie-tree")
        tree = TrieTree()
        for country in self.countries:
            for name in country.alias:
                tree.add([ x.strip() for x in name.split(" ") if x.strip() ], **{ KeyCountry: country })
        # Done
        return tree

    def loadIDFDict(self):
        """Load idf dict
        """
        self.logger.info("Load IDF Dictionary")
        with open(IDFDictFilename, "rb") as fd:
            return { k: v for (k, v) in json.load(fd) }

    def loadStopwordSet(self):
        """Load stop word set
        """
        self.logger.info("Load English Stopword Dictionary")
        return set(nltk.corpus.stopwords.words("english"))

    def tokenize(self, text, stopwords):
        """Standard tokenize
        """
        # Run tokenize
        for word in nltk.tokenize.word_tokenize(text):
            word = word.lower()
            if word in stopwords or word in DropWords or PunctuationRegex.match(word):
                continue
            # Good
            yield word

    def getKeywords(self, newsList, titleFile, contentFile):
        """Get the keywords list
        """
        # Load idf
        idf = self.loadIDFDict()
        titleTF, contentTF = Counter(), Counter()
        # Get the stop words
        stopwords = self.loadStopwordSet()
        # Get tf
        for news in newsList:
            if news.title:
                # Title
                words = list(self.tokenize(news.title, stopwords))
                # Single
                for word in words:
                    titleTF[word] += 1
                # Double
                for i in xrange(0, len(words) - 1):
                    titleTF[(words[i].lower(), words[i + 1].lower())] += 1
                # Triple
                for i in xrange(0, len(words) - 2):
                    titleTF[(words[i].lower(), words[i + 1].lower(), words[i + 2].lower())] += 1
                # Four
                for i in xrange(0, len(words) - 3):
                    titleTF[(words[i].lower(), words[i + 1].lower(), words[i + 2].lower(), words[i + 3].lower())] += 1
            if news.content:
                # Content
                words = list(self.tokenize(news.content, stopwords))
                # Single
                for word in words:
                    contentTF[word] += 1
                # Double
                for i in xrange(0, len(words) - 1):
                    contentTF[(words[i].lower(), words[i + 1].lower())] += 1
                # Triple
                for i in xrange(0, len(words) - 2):
                    contentTF[(words[i].lower(), words[i + 1].lower(), words[i + 2].lower())] += 1
                # Four
                for i in xrange(0, len(words) - 3):
                    contentTF[(words[i].lower(), words[i + 1].lower(), words[i + 2].lower(), words[i + 3].lower())] += 1
        # Get tf-idf
        titleKeywords, contentKeywords = {}, {}
        for word, tf in titleTF.iteritems():
            titleKeywords[word] = tf * idf.get(word, MissingValueIDF)
        for word, tf in contentTF.iteritems():
            contentKeywords[word] = tf * idf.get(word, MissingValueIDF)
        # Write out
        with open(titleFile, "wb") as fd:
            print >>fd, "\t".join([ u"关键词", u"单词个数", u"TF-IDF" ])
            for word, score in sorted(titleKeywords.iteritems(), key = lambda (k, v): v, reverse = True)[: 2000]:
                if not isinstance(score, float):
                    continue
                if isinstance(word, (list, tuple)):
                    length = len(word)
                    word = " ".join(word)
                else:
                    length = 1
                print >>fd, "%s\t%d\t%.4f" % (word, length, score)
        with open(contentFile, "wb") as fd:
            print >>fd, "\t".join([ u"关键词", u"单词个数", u"TF-IDF" ])
            for word, score in sorted(contentKeywords.iteritems(), key = lambda (k, v): v, reverse = True)[: 2000]:
                if not isinstance(score, float):
                    continue
                if isinstance(word, (list, tuple)):
                    length = len(word)
                    word = " ".join(word)
                else:
                    length = 1
                print >>fd, "%s\t%d\t%.4f" % (word, length, score)

    def cooccurrence(self, newsList, words, outputFile):
        """Analyze the news cooccurrence words
        """
        # Get the stop words
        stopwords = self.loadStopwordSet()
        # Build trie tree dict
        tree = TrieTree()
        for word in words:
            w = list(self.tokenize(word, stopwords))
            if w:
                tree.add(w, word = word, words = w)
        # Load idf
        idf = self.loadIDFDict()
        keywords = {}
        # Get tf
        for news in newsList:
            if news.content:
                paragraphs = [ x.strip() for x in news.content.split("\n") ]
                # Calculate on each paragraph
                for paragraph in paragraphs:
                    # Tokenize the paragraph
                    words = list(self.tokenize(paragraph, stopwords))
                    # Search for each key words
                    keywordsWithIndexes = {}
                    for node, startIndex in tree.search(words):
                        keyword = node.attrs["word"]
                        if not keyword in keywordsWithIndexes:
                            keywordsWithIndexes[keyword] = [ (startIndex, len(node.attrs["words"])) ]
                        else:
                            keywordsWithIndexes[keyword].append((startIndex, len(node.attrs["words"])))
                    # Caculate the related words except the keyword itself
                    for keyword, indices in keywordsWithIndexes.iteritems():
                        # Get counter of the keyword
                        if not keyword in keywords:
                            keywords[keyword] = Counter()
                        continuousWords = []
                        counter = keywords[keyword]
                        for i, word in enumerate(words):
                            for startIndex, length in indices:
                                if i >= startIndex and i < startIndex + length:
                                    # Fall in the keyword
                                    continuousWords = []
                                    break
                            else:
                                # Good
                                counter[word] += 1
                                continuousWords.append(word)
                                if len(continuousWords) > 4:
                                    del continuousWords[0]
                                for i in range(4):
                                    if len(continuousWords) - i <= 1:
                                        break
                                    counter[tuple(continuousWords[i:])] += 1
        # Get for each trunk
        with open(outputFile, "wb") as fd:
            print >>fd, "\t".join([ u"关键词", u"相关词汇", u"单词个数", u"TF-IDF" ])
            for keyword, counter in keywords.iteritems():
                words = {}
                for word, tf in counter.iteritems():
                    words[word] = tf * idf.get(word, MissingValueIDF)
                for word, score in sorted(words.iteritems(), key = lambda (k, v): v, reverse = True)[: 100]:
                    if isinstance(word, (list, tuple)):
                        length = len(word)
                        word = " ".join(word)
                    else:
                        length = 1
                    print >>fd, "%s\t%s\t%d\t%.4f" % (keyword, word, length, score)

    def cooccurrenceEntity(self, newsList, words, outputFile):
        """Analyze the news cooccurrence words
        """
        # Get the stop words
        stopwords = self.loadStopwordSet()
        # Build entity trie tree
        tree = self.buildEntityTrieTree()
        for word in words:
            w = list(self.tokenize(word, stopwords))
            if w:
                tree.add(w, word = word, words = w)
        keyword2Entities = {}
        # Get tf
        for news in newsList:
            if news.content:
                paragraphs = [ x.strip() for x in news.content.split("\n") ]
                # Calculate on each paragraph
                for paragraph in paragraphs:
                    # Tokenize the paragraph
                    words = list(self.tokenize(paragraph, stopwords))
                    # Search for each key words
                    keywords = Set()
                    entities = {}
                    for node, _ in tree.search(words):
                        # Check keyword
                        keyword = node.attrs.get("word")
                        if keyword:
                            keywords.add(keyword)
                        # Check entities
                        country = node.attrs.get(KeyCountry)
                        if country:
                            if not KeyCountry in entities:
                                entities[KeyCountry] = Counter()
                            entities[KeyCountry][country.name] += 1
                    # Add to global
                    for keyword in keywords:
                        if not keyword in keyword2Entities:
                            ents = {}
                            keyword2Entities[keyword] = ents
                        else:
                            ents = keyword2Entities[keyword]
                        for entType, counter in entities.iteritems():
                            if not entType in ents:
                                ents[entType] = Counter()
                            for key, value in counter.iteritems():
                                ents[entType][key] += value
        # Get for each trunk
        with open(outputFile, "wb") as fd:
            print >>fd, "\t".join([ u"关键词", u"相关实体类型", u"相关实体", u"实体出现次数" ])
            for keyword, entities in keyword2Entities.iteritems():
                for entType, counter in entities.iteritems():
                    for key, value in counter.most_common()[: 100]:
                        print >>fd, "%s\t%s\t%s\t%d" % (keyword, entType, key, value)
