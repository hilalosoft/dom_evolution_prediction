import unittest

from bs4 import BeautifulSoup

from database.statistics.soup_operations import cal_max_depth, cal_depth, get_siblings_soup, \
    generate_vectors_for_attr, generate_vectors_from_soup


class dataTestCase(unittest.TestCase):
    def test_cal_max_depth(self):
        html_doc = """
        <html><head><title>The Dormouse's story</title></head>
        <body>
        <p class="title"><b>The Dormouse's story</b></p>

        <p class="story">Once upon a time there were three little sisters; and their names were
        <a href="http://example.com/elsie" class="sister" id="link1">Elsie</a>,
        <a href="http://example.com/lacie" class="sister" id="link2">Lacie</a> and
        <a href="http://example.com/tillie" class="sister" id="link3">Tillie</a>;
        and they lived at the bottom of a well.</p>

        <p class="story">...</p>
        </body>
        </html>
        """

        parsed_dom = BeautifulSoup(html_doc, 'html.parser')
        max_depth = cal_max_depth(parsed_dom)
        self.assertEqual(max_depth, 5)  # add assertion here

    def test_cal_depth(self):
        html_doc = """
                <html><head><title>The Dormouse's story</title></head>
                <body>
                <p class="title"><b>The Dormouse's story</b></p>

                <p class="story">Once upon a time there were three little sisters; and their names were
                <a href="http://example.com/elsie" class="sister" id="link1">Elsie</a>,
                <a href="http://example.com/lacie" class="sister" id="link2">Lacie</a> and
                <a href="http://example.com/tillie" class="sister" id="link3">Tillie</a>;
                and they lived at the bottom of a well.</p>

                <p class="story">...</p>
                </body>
                </html>
                """
        parsed_dom = BeautifulSoup(html_doc, 'html.parser')
        depth = cal_depth(parsed_dom.a, 5)
        self.assertEqual(depth, 4 / 5)  # add assertion here

    def test_siblings_soup(self):
        html_doc = """
                        <html><head><title>The Dormouse's story</title></head>
                        <body>
                        <p class="title"><b>The Dormouse's story</b></p>

                        <p class="story">Once upon a time there were three little sisters; and their names were
                        <a href="http://example.com/elsie" class="sister" id="link1">Elsie</a>,
                        <a href="http://example.com/lacie" class="sister" id="link2">Lacie</a> and
                        <a href="http://example.com/tillie" class="sister" id="link3">Tillie</a>;
                        and they lived at the bottom of a well.</p>

                        <p class="story">...</p>
                        </body>
                        </html>
                        """
        parsed_dom = BeautifulSoup(html_doc, 'html.parser')
        position, siblings_list = get_siblings_soup(parsed_dom.body.a)
        siblings_dictionary = {"id": 0, "string": 0, "ul": 0, "li": 0, "h1": 0, "h2": 0, "h3": 0, "h4": 0,
                               "h5": 0,
                               "div": 0
            , "span": 0, "form": 0, "input": 0, "p": 0, "img": 0, 'a': 2 / 7, "dl": 0, "dt": 0, "dd": 0, "svg": 0,
                               "path": 0, "g": 0
            , "option": 0, "i": 0, "attribute": 0, "button": 0, "class": 0, "href": 0}
        self.assertEqual(siblings_list, siblings_dictionary)  # add assertion here
        self.assertEqual(position, 2 / 7)  # add assertion here

    # def test_xpath_soup(self):
    #     self.assertEqual(True, False)  # add assertion here

    def test_generate_vectors_for_attr(self):
        html_doc = """
                    <html><head><title>The Dormouse's story</title></head>
                    <body>
                    <p class="title"><b>The Dormouse's story</b></p>

                    <p class="story">Once upon a time there were three little sisters; and their names were
                    <a href="http://example.com/elsie" class="sister" id="link1">Elsie</a>,
                    <a href="http://example.com/lacie" class="sister" id="link2">Lacie</a> and
                    <a href="http://example.com/tillie" class="sister" id="link3">Tillie</a>;
                    and they lived at the bottom of a well.</p>

                    <p class="story">...</p>
                    </body>
                    </html>
                    """
        parsed_dom = BeautifulSoup(html_doc, 'html.parser')

        vectors = generate_vector_from_soup(parsed_dom.body.a, 5)
        # vectors = generate_vectors_for_attr(parsed_dom.body.a)
        self.assertEqual(True, False)  # add assertion here


if __name__ == '__main__':
    unittest.main()
