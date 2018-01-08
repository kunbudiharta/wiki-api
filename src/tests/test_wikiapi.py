# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import os
import shutil

import pytest
import six
from six.moves import urllib_parse
from wikiapi import WikiApi


def assert_url_valid(url):
    if not bool(urllib_parse.urlparse(url).netloc):
        raise AssertionError('{} is not a valid URL'.format(url))


DATA = {
    'en': {
        'keywords': ['president', 'hilary'],
        'name': 'Bill Clinton',
    },
    'es': {
        'keywords': ['presidente', 'hilary'],
        'name': 'Bill Clinton',
    },
    'ar': {
        'keywords': ['رئيس'],
        'name': 'بيل كلينتون',
    },
}


class TestWiki(object):

    @pytest.fixture
    def client_factory(self):
        def make(locale):
            return WikiApi(options={'locale': locale})
        return make

    @pytest.mark.parametrize('locale', DATA.keys())
    def test_heading(self, locale, client_factory):
        name = DATA[locale]['name']
        client = client_factory(locale=locale)
        article = client.get_article(client.find(name)[0])

        assert article.heading == name

    @pytest.mark.parametrize('locale', DATA.keys())
    def test_image(self, locale, client_factory):
        name = DATA[locale]['name']
        client = client_factory(locale=locale)
        article = client.get_article(client.find(name)[0])

        assert_url_valid(url=article.image)

    @pytest.mark.parametrize('locale', DATA.keys())
    def test_summary(self, locale, client_factory):
        name = DATA[locale]['name']
        client = client_factory(locale=locale)
        article = client.get_article(client.find(name)[0])

        assert isinstance(article.summary, str)

    @pytest.mark.parametrize('locale', DATA.keys())
    def test_content(self, locale, client_factory):
        name = DATA[locale]['name']
        client = client_factory(locale=locale)
        article = client.get_article(client.find(name)[0])

        assert len(article.content) > 200

    @pytest.mark.parametrize('locale', DATA.keys())
    def test_references(self, locale, client_factory):
        name = DATA[locale]['name']
        client = client_factory(locale=locale)
        article = client.get_article(client.find(name)[0])
        assert isinstance(article.references, list) is True

    @pytest.mark.parametrize('locale', DATA.keys())
    def test_url(self, locale, client_factory):
        name = DATA[locale]['name']
        client = client_factory(locale=locale)
        article = client.get_article(client.find(name)[0])

        assert_url_valid(url=article.url)
        assert 'wikipedia.org/wiki/' in article.url

    @pytest.mark.parametrize('locale', DATA.keys())
    def test_get_relevant_article(self, locale, client_factory):
        client = client_factory(locale=locale)
        name = DATA[locale]['name']
        keywords = DATA[locale]['keywords']
        _article = client.get_relevant_article(client.find(name), keywords)
        assert _article
        assert name in _article.heading
        assert len(_article.content) > 1000
        assert  DATA[locale]['keywords'][0] in _article.content
        assert name in _article.content

    @pytest.mark.parametrize('locale', DATA.keys())
    def test_get_relevant_article_no_result(self, locale, client_factory):
        client = client_factory(locale=locale)
        name = DATA[locale]['name']
        keywords = ['hockey player']
        _article = client.get_relevant_article(client.find(name), keywords)
        assert _article is None

    @pytest.mark.parametrize('locale', DATA.keys())
    def test__remove_ads_from_content(self, locale, client_factory):
        client = client_factory(locale=locale)
        content = (
            'From Wikipedia, the free encyclopedia. \n\nLee Strasberg '
            '(November 17, 1901 2013 February 17, 1982) was an American '
            'actor, director and acting teacher.\n'
            'Today, Ellen Burstyn, Al Pacino, and Harvey Keitel lead this '
            'nonprofit studio dedicated to the development of actors, '
            'playwrights, and directors.\n\nDescription above from the '
            'Wikipedia article\xa0Lee Strasberg,\xa0licensed under CC-BY-SA, '
            'full list of contributors on Wikipedia.'
        )

        result_content = client._remove_ads_from_content(content)

        expected_content = (
            ' \n\nLee Strasberg '
            '(November 17, 1901 2013 February 17, 1982) was an American '
            'actor, director and acting teacher.\n'
            'Today, Ellen Burstyn, Al Pacino, and Harvey Keitel lead this '
            'nonprofit studio dedicated to the development of actors, '
            'playwrights, and directors.'
        )
        assert expected_content == result_content


class TestCache(object):

    def _get_cache_size(self, wiki_instance):
        """Return a count of the items in the cache"""
        cache = os.path.exists(wiki_instance.cache_dir)
        if not cache:
            return 0
        _, _, cache_files = next(os.walk(wiki_instance.cache_dir))
        return len(cache_files)

    def test_cache_populated(self):
        wiki = WikiApi({'cache': True, 'cache_dir': '/tmp/wikiapi-test'})

        assert self._get_cache_size(wiki) == 0
        # Make multiple calls to ensure no duplicate cache items created
        assert wiki.find('Bob Marley') == wiki.find('Bob Marley')
        assert self._get_cache_size(wiki) == 1

        # Check cache keys are unique
        assert wiki.find('Tom Hanks') != wiki.find('Bob Marley')

        assert self._get_cache_size(wiki) == 2
        shutil.rmtree(wiki.cache_dir, ignore_errors=True)

    def test_cache_not_populated_when_disabled(self):
        wiki = WikiApi({'cache': False})

        assert self._get_cache_size(wiki) == 0
        wiki.find('Bob Marley')
        assert self._get_cache_size(wiki) == 0
        shutil.rmtree(wiki.cache_dir, ignore_errors=True)


class TestUnicode(object):

    @pytest.fixture
    def set_up(self):
        # using an Italian-Emilian locale that is full of unicode symbols
        wiki = WikiApi({'locale': 'eml'})
        result = wiki.find('Bulaggna')[0]
        return {
            'wiki': wiki,
            'result': result,
        }

    def test_search(self, locale, client_factory):
        # this is urlencoded.
        assert set_up['result'] == u'Bul%C3%A5ggna'

    def test_article(self, locale, client_factory):
        # unicode errors will likely blow in your face here
        assert client.get_article(set_up['result']) is not None
