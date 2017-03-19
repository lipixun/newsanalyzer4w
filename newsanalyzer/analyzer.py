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

from .trie import TrieTree
from .spec import IDFDictFilename, MissingValueIDF, DropWords, KeyCountry, KeyRegion, KeyProvince, KeyCity
from .utils import nltk, json
from .excelio import KeywordResultWriter, CooccurrenceResultWriter, CooccurrenceEntityResultWriter

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
        for region in self.regions:
            for name in region.alias:
                tree.add([ x.strip() for x in name.split(" ") if x.strip() ], **{ KeyRegion: region })
        for province in self.provinces:
            for name in province.alias:
                tree.add([ x.strip() for x in name.split(" ") if x.strip() ], **{ KeyProvince: province })
        for city in self.cities:
            for name in city.alias:
                tree.add([ x.strip() for x in name.split(" ") if x.strip() ], **{ KeyCity: city })
        # Done
        return tree

    def loadIDFDict(self):
        """Load idf dict
        """
        self.logger.info("Load IDF Dictionary")
        idf = {}
        with open(IDFDictFilename, "rb") as fd:
            for item in json.load(fd):
                w, v = item["w"], item["v"]
                if isinstance(w, list):
                    w = tuple(w)
                idf[w] = v
        return idf

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

    def groupByTermsCount(self, counter):
        """Group by terms count
        """
        counters = {}
        for term, count in counter.iteritems():
            if isinstance(term, tuple):
                termCount = len(term)
            else:
                termCount = 1
            if termCount not in counters:
                counters[termCount] = Counter()
            counters[termCount][term] = count
        return counters

    def getKeywords(self, nGram, newsList, titleFile, contentFile):
        """Get the keywords list
        """
        # Load idf
        idf = self.loadIDFDict()
        titleTF, contentTF = Counter(), Counter()
        # Get the stop words
        stopwords = self.loadStopwordSet()
        # Get common keywords
        self.logger.info("Start analyze")
        for news in newsList:
            if news.title:
                # Title
                words = list(self.tokenize(news.title, stopwords))
                for i in range(len(words)):
                    for j in range(1, nGram + 1):
                        terms = words[i:i+j]
                        if len(terms) != j:
                            break
                        if j == 1:
                            titleTF[terms[0]] += 1
                        else:
                            titleTF[tuple(terms)] += 1
            if news.content:
                # Content
                words = list(self.tokenize(news.content, stopwords))
                for i in range(len(words)):
                    for j in range(1, nGram + 1):
                        terms = words[i:i+j]
                        if len(terms) != j:
                            break
                        if j == 1:
                            contentTF[terms[0]] += 1
                        else:
                            contentTF[tuple(terms)] += 1
        # Get tf-idf
        titleKeywords, contentKeywords = {}, {}
        for word, tf in titleTF.iteritems():
            titleKeywords[word] = tf * idf.get(word, MissingValueIDF)
        for word, tf in contentTF.iteritems():
            contentKeywords[word] = tf * idf.get(word, MissingValueIDF)
        # Write out
        self.logger.info("Write output")
        with open(titleFile + ".csv", "wb") as fd:
            titleWriter = KeywordResultWriter(fd)
            for termCount, termCounter in sorted(self.groupByTermsCount(titleKeywords).iteritems(), key = lambda (k,v): k):
                for term, count in termCounter.most_common(200):
                    titleWriter.write({
                        titleWriter.FieldKeyword: " ".join(term) if isinstance(term, tuple) else term ,
                        titleWriter.FieldTermsCount: termCount,
                        titleWriter.FieldTFIDF: count,
                        titleWriter.FieldFrequency: titleTF[term],
                        })
        with open(contentFile + ".csv", "wb") as fd:
            contentWriter = KeywordResultWriter(fd)
            for termCount, termCounter in sorted(self.groupByTermsCount(contentKeywords).iteritems(), key = lambda (k,v): k):
                for term, count in termCounter.most_common(200):
                    contentWriter.write({
                        contentWriter.FieldKeyword: " ".join(term) if isinstance(term, tuple) else term ,
                        contentWriter.FieldTermsCount: termCount,
                        contentWriter.FieldTFIDF: count,
                        contentWriter.FieldFrequency: contentTF[term],
                        })

    def cooccurrence(self, nGram, newsList, keywords, outputFile):
        """Analyze the news cooccurrence words
        Args:
            newsList([ News ]): The news
            keywords([ NamedKeyword ]): The keywords
            outputFile(str): The output file
        """
        # Get the stop words
        stopwords = self.loadStopwordSet()
        # Build trie tree of key words
        tree = TrieTree()
        for namedKeyword in keywords:
            for word in namedKeyword.words:
                terms = list(self.tokenize(word, stopwords))
                if terms:
                    tree.add(terms, keyword = namedKeyword, word = word, _terms = terms)
        # Load idf
        idf = self.loadIDFDict()
        keywords = {}
        # Get words
        self.logger.info("Start analyze")
        for terms in self.iterTerms(newsList, stopwords, perParagraph = True):
            # Search for all known keywords
            keywordsInParagraph = {}
            for node, startIndex in tree.search(terms):
                namedKeyword = node.attrs["keyword"]
                if not namedKeyword.name in keywordsInParagraph:
                    keywordsInParagraph[namedKeyword.name] = []
                keywordsInParagraph[namedKeyword.name].append((startIndex, len(node.attrs["_terms"])))
            # Caculate the related words except the keyword itself
            for keywordName, indices in keywordsInParagraph.iteritems():
                # Get counter of the keyword
                if not keywordName in keywords:
                    keywords[keywordName] = Counter()
                counter = keywords[keywordName]
                continuousTerms = []
                # Get the cooccurrence terms
                for i, term in enumerate(terms):
                    for startIndex, length in indices:
                        if i >= startIndex and i < startIndex + length:
                            # Fall in the keyword
                            continuousTerms = []
                            break
                    else:
                        # Good
                        counter[term] += 1
                        continuousTerms.append(term)
                        if len(continuousTerms) > nGram:
                            del continuousTerms[0]
                        for i in range(nGram):
                            if len(continuousTerms) - i <= 1:
                                break

                            counter[tuple(continuousTerms[i:])] += 1
        # Get for each trunk
        self.logger.info("Write output")
        with open(outputFile + ".csv", "wb") as fd:
            writer = CooccurrenceResultWriter(fd)
            for keywordName, counter in keywords.iteritems():
                # Get idf
                termsIDF = {}
                for term, tf in counter.iteritems():
                    termsIDF[term] = tf * idf.get(term, MissingValueIDF)
                # Write
                for termCount, termCounter in sorted(self.groupByTermsCount(termsIDF).iteritems(), key = lambda (k, v): k):
                    for word, count in termCounter.most_common(200):
                        writer.write({
                            writer.FieldKeyword: keywordName,
                            writer.FieldCoword: " ".join(word) if isinstance(word, tuple) else word,
                            writer.FieldTermsCount: termCount,
                            writer.FieldTFIDF: count,
                            writer.FieldFrequency: counter[word]
                            })

    def cooccurrenceEntity(self, newsList, keywords, outputFile):
        """Analyze the news cooccurrence words
        """
        # Get the stop words
        stopwords = self.loadStopwordSet()
        # Build entity trie tree
        tree = self.buildEntityTrieTree()
        for namedKeyword in keywords:
            for word in namedKeyword.words:
                terms = list(self.tokenize(word, stopwords))
                if terms:
                    tree.add(terms, keyword = namedKeyword)
        keyword2Entities = { None: {} }
        # Get words
        self.logger.info("Start analyze")
        for terms in self.iterTerms(newsList, stopwords, perParagraph = True):
            # Search for each key words
            keywords = Set()
            entities = {}
            for node, _ in tree.search(terms):
                # Check keyword
                namedKeyword = node.attrs.get("keyword")
                if namedKeyword:
                    keywords.add(namedKeyword.name)
                # Check entities
                country = node.attrs.get(KeyCountry)
                if country:
                    if KeyCountry not in entities:
                        entities[KeyCountry] = Counter()
                    entities[KeyCountry][country.name] += 1
                # Check region
                region = node.attrs.get(KeyRegion)
                if region:
                    if KeyRegion not in entities:
                        entities[KeyRegion] = Counter()
                    entities[KeyRegion][region.name] += 1
                # Check province
                province = node.attrs.get(KeyProvince)
                if province:
                    if KeyProvince not in entities:
                        entities[KeyProvince] = Counter()
                    entities[KeyProvince][province.name] += 1
                # Check city
                city = node.attrs.get(KeyCity)
                if city:
                    if KeyCity not in entities:
                        entities[KeyCity] = Counter()
                    entities[KeyCity][city.name] += 1
            # Add to global
            for keyword in [ None ] + list(keywords):
                if not keyword in keyword2Entities:
                    keyword2Entities[keyword] = {}
                ents = keyword2Entities[keyword]
                for entType, counter in entities.iteritems():
                    if not entType in ents:
                        ents[entType] = Counter()
                    for key, value in counter.iteritems():
                        ents[entType][key] += value
        # Write out
        self.logger.info("Write output")
        with open(outputFile + ".csv", "wb") as fd:
            writer = CooccurrenceEntityResultWriter(fd)
            # Country
            if keyword2Entities[None].get(KeyCountry):
                for key, value in keyword2Entities[None][KeyCountry].most_common()[: 200]:
                    writer.write({
                        writer.FieldKeyword: "Global",
                        writer.FieldEntityType: KeyCountry,
                        writer.FieldEntity: key,
                        writer.FieldFrequency: value,
                    })
            # Region
            if keyword2Entities[None].get(KeyRegion):
                for key, value in keyword2Entities[None][KeyRegion].most_common()[: 200]:
                    writer.write({
                        writer.FieldKeyword: "Global",
                        writer.FieldEntityType: KeyRegion,
                        writer.FieldEntity: key,
                        writer.FieldFrequency: value,
                    })
            # Province
            if keyword2Entities[None].get(KeyProvince):
                for key, value in keyword2Entities[None][KeyProvince].most_common()[: 200]:
                    writer.write({
                        writer.FieldKeyword: "Global",
                        writer.FieldEntityType: KeyProvince,
                        writer.FieldEntity: key,
                        writer.FieldFrequency: value,
                    })
            # City
            if keyword2Entities[None].get(KeyCity):
                for key, value in keyword2Entities[None][KeyCity].most_common()[: 200]:
                    writer.write({
                        writer.FieldKeyword: "Global",
                        writer.FieldEntityType: KeyCity,
                        writer.FieldEntity: key,
                        writer.FieldFrequency: value,
                    })
            # Keywords
            for keyword, entities in keyword2Entities.iteritems():
                if not keyword:
                    continue
                for entType, counter in entities.iteritems():
                    for key, value in counter.most_common()[: 200]:
                        writer.write({
                            writer.FieldKeyword: keyword,
                            writer.FieldEntityType: entType,
                            writer.FieldEntity: key,
                            writer.FieldFrequency: value,
                            })

    def iterTerms(self, newsList, stopwords, perParagraph = False):
        """Iterate terms per news or per paragraph
        Yield:
            [ str ]: The terms
        """
        for news in newsList:
            if not news.content:
                continue
            if perParagraph:
                # Per paragraph
                for paragraph in [ x.strip() for x in news.content.split("\n") ]:
                    if paragraph:
                        # Tokenize the paragraph
                        terms = list(self.tokenize(paragraph, stopwords))
                        if terms:
                            yield terms
            else:
                # Per news
                terms = list(self.tokenize(paragraph, stopwords))
                if terms:
                    yield terms
