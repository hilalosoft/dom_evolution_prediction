import itertools
import os

import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, InvalidSelectorException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

from Classes.DynamicPredictorClass import DynamicPredictor

considered_tag_dictionary = {"id": 0, "string": 0, "ul": 0, "li": 0, "h1": 0, "h2": 0, "h3": 0, "h4": 0, "h5": 0,
                             "div": 0
    , "span": 0, "form": 0, "input": 0, "p": 0, "img": 0, 'a': 0, "dl": 0, "dt": 0, "dd": 0, "svg": 0, "path": 0, "g": 0
    , "option": 0, "i": 0, "attribute": 0, "button": 0, "class": 0, "href": 0, "other": 0}
link_tags = ["src", "a", "action", "href"]


# we copy the dictionary containing considered tags iterate over all the siblings,
# determine the element position within its peers and divide in the end on the number of siblings to normalize.
# normalize the position in the end
def get_siblings_soup(soup):
    siblings_dict = considered_tag_dictionary.copy()
    count = 1
    for index, sibling in enumerate(itertools.chain(soup.previous_siblings, soup.next_siblings)):
        if sibling.name in siblings_dict:
            siblings_dict[sibling.name] += 1
        else:
            siblings_dict["other"] += 1
        count += 1

    for key in siblings_dict:
        siblings_dict[key] = siblings_dict[key] / count
    position = (sum(1 for _ in soup.previous_siblings) + 1) / count
    return position, siblings_dict


def get_siblings_attr(soup, attr):
    siblings_dict = considered_tag_dictionary.copy()
    for attribute in soup.attrs:
        if attribute == attr:
            continue
        if attribute in siblings_dict:
            siblings_dict[attribute] += 1
    return siblings_dict


# The function takes an element as input and returns an xpath string representation of the element, which can be used
# to locate the element in an XML or HTML document. The xpath is constructed by iterating over all the parents of the
# element, adding the element name to the path, and if there are multiple elements with the same name, adding the
# index of the element to the path.
def xpath_soup(element):
    components = []
    child = element if element.name else element.parent
    for parent in child.parents:  # type: bs4.element.Tag
        siblings = parent.find_all(child.name, recursive=False)
        components.append(
            child.name if 1 == len(siblings) else '%s[%d]' % (
                child.name,
                next(i for i, s in enumerate(siblings, 1) if s is child)
            )
        )
        child = parent
    components.reverse()
    return '/%s' % '/'.join(components)


# the function takes a dom object as input
# returns the maximum depth of the dom object by iterating through all the descendants of the dom
# ignoring certain tags and adding 1 to the maximum depth if the child has any attributes.
# This helps to find the depth of the HTML tree structure.
def cal_max_depth(dom):
    ignored_list = ["<class 'bs4.element.Script'>",
                    "<class 'bs4.element.Stylesheet'>",
                    "<class 'bs4.element.Comment'>",
                    "<class 'bs4.element.Declaration'>",
                    "<class 'bs4.element.TemplateString'>",
                    "<class 'bs4.element.NavigableString'>",
                    "<class 'bs4.element.Doctype'>",
                    "<class 'bs4.element.ProcessingInstruction'>"]
    maximum_depth = -1
    for child in dom.descendants:
        if child == '\n':
            continue
        child_depth = cal_depth(child)
        if child_depth > maximum_depth:
            maximum_depth = child_depth
            if (str(type(child)) not in ignored_list and
                    len(child.attrs) > 0):
                maximum_depth += maximum_depth + 1
    return maximum_depth


# in case max depth is not given then the calculation is not for the feature vector
# flag is to check if the element is attribute or not
def cal_depth(soup, max_depth=1, flag=False):
    count = 0
    for parent in soup.parents:
        count += 1
    if flag:
        count += 1
    return count / max_depth


def generate_vector(node, node_value, timestamp, position, depth, nr_siblings, nr_children, xpath, siblings, changed):
    vector = [node, node_value, timestamp, position, depth, nr_siblings, nr_children, xpath, siblings, changed]
    return vector


# process manager
class DriverObject:
    driver = None
    options = Options()
    filename = "comparing.html"

    def __init__(self):
        self.options.add_argument("start-maximized")
        self.options.add_argument("enable-automation")
        self.options.add_argument("--headless")
        self.options.add_argument("--no-sandbox")
        self.options.add_argument("--disable-dev-shm-usage")
        self.options.add_argument("--disable-browser-side-navigation")
        self.options.add_argument('--headless')
        self.options.add_argument('--disable-gpu')  # Last I checked this was necessary.
        self.driver = webdriver.Chrome(options=self.options)
        self.driver.set_page_load_timeout(120)

    def get_page(self, dom):
        textfile = open(os.getcwd() + self.filename, "w", encoding='utf-8')
        textfile.write(dom)
        textfile.close()
        self.driver.get(os.getcwd() + self.filename)

    def save_page(self, save_path):
        self.driver.save_screenshot(save_path)

    def close(self):
        self.driver.close()

    def element_changed(self, xpath, soup, attribute=None, text_content=None):
        try:
            elem = self.driver.find_element(By.XPATH, xpath)
            if attribute:
                if isinstance(text_content, list):
                    attribute_string = ""
                    for value in text_content:
                        attribute_string = attribute_string + value
                else:
                    attribute_string = text_content
                attribute_value = elem.get_attribute(attribute)
                if attribute_value == attribute_string:
                    return False
                else:
                    return True
            if text_content:
                if elem.text == text_content:
                    return False
                else:
                    return True
            if elem.tag_name == soup.name:
                return False
            else:
                return True
        except NoSuchElementException as e:
            return True
        except InvalidSelectorException as e:
            return False


def generate_vectors_from_navigable_string(next_dom, timestamp, soup, index, max_depth):
    siblings_dict = considered_tag_dictionary.copy()
    xpath = xpath_soup(soup)
    changed = element_changed(next_dom, xpath, soup, text_content=soup.string)
    nodetype = considered_tag_dictionary.copy()
    nodetype["string"] = 1
    vector = generate_vector(nodetype, "", timestamp, index, cal_depth(soup, max_depth), 0, 0, xpath,
                             siblings_dict, changed)
    return vector


def generate_vectors_from_soup(next_dom, timestamp, soup, max_depth):
    nr_of_children = len(soup.contents) + len(soup.attrs)
    position, siblings_vector = get_siblings_soup(soup)
    xpath = xpath_soup(soup)
    depth = cal_depth(soup, max_depth)
    vector_list = []
    for vector in generate_vectors_for_attr(next_dom, timestamp, soup, max_depth, xpath):
        vector_list.append(vector)
    changed = element_changed(next_dom, xpath, soup)
    nodetype = considered_tag_dictionary.copy()
    if soup.name in nodetype.keys():
        nodetype[soup.name] = 1
    else:
        nodetype["other"] = 1
    vector_list.append(
        generate_vector(nodetype, "", timestamp, position, depth, len(siblings_vector), nr_of_children, xpath,
                        siblings_vector,
                        changed))
    return vector_list


def remove_link_prefix(link):
    links = link.split("http://")
    if len(links) == 1:
        links = link.split("https://")
        if len(links) > 2:
            weblinks = links[1][:15]
            if weblinks == "web.archive.org":
                return links[2]
            else:
                return links[1]
        elif len(links) > 1:
            return link[1]
        else:
            return link
    else:
        return links[1]


def generate_vectors_for_attr(next_dom, timestamp, soup, max_depth, xpath):
    final_vectors = []
    for attr in soup.attrs:
        if attr == "class":
            nr_of_children = len(soup.attrs[attr])
        else:
            nr_of_children = 1
        value = soup.attrs.get(attr)
        if attr in link_tags:
            value = remove_link_prefix(soup.attrs[attr])
        siblings_vector = get_siblings_attr(soup, attr)
        # xpath = xpath + "/" + attr
        depth = cal_depth(soup, max_depth, True)
        changed = element_changed(next_dom, xpath, soup, attribute=attr, text_content=value)
        nodetype = considered_tag_dictionary.copy()
        if attr in nodetype.keys():
            nodetype[attr] = 1
        else:
            nodetype["other"] = 1
        final_vectors.append(
            generate_vector(nodetype, str(value), timestamp, 0, depth, len(soup.attrs) - 1, 0, xpath,
                            siblings_vector,
                            changed))
    return final_vectors


# def element_changed(next_dom, xpath, soup, attribute=None, text_content=None):
#     element_to_compare = find_element_by_xpath_soup(xpath, next_dom)
#     if element_to_compare:
#         if attribute:
#             if attribute in element_to_compare.attrs:
#                 if attribute in link_tags:
#                     attribute_value = remove_link_prefix(element_to_compare.attrs[attribute])
#                 else:
#                     attribute_value = element_to_compare.attrs[attribute]
#             else:
#                 return True
#             if attribute_value == text_content:
#                 return False
#             else:
#                 return True
#         if text_content:
#             if element_to_compare.string == soup.string:
#                 return False
#             else:
#                 return True
#         if element_to_compare.name == soup.name:
#             return False
#         else:
#             return True
#     else:
#         return True

def element_changed(next_dom, xpath, soup, attribute=None, text_content=None):
    element_to_compare = find_element_by_xpath_soup(xpath, next_dom)
    if not element_to_compare:
        return True

    if attribute:
        attribute_value = element_to_compare.attrs.get(attribute)
        if attribute in link_tags:
            attribute_value = remove_link_prefix(attribute_value)
        if attribute_value != text_content:
            return True

    if text_content:
        if element_to_compare.string != soup.string:
            return True

    if element_to_compare.name != soup.name:
        return True

    return False


def find_element_by_xpath_soup(xpath, next_dom):
    dom_element = next_dom
    xpath_list = xpath.split('/')[1:]
    flag = True
    for tag in xpath_list:
        if tag.find('[') != -1:
            position = int(tag[tag.find('[') + 1:tag.find(']')])
            tag = tag[:tag.find('[')]
        else:
            position = None
        count_position = 1
        for element in dom_element.contents:
            if position is None:
                if element.name == tag:
                    dom_element = element
                    flag = True
                    break
                else:
                    flag = False
            else:
                if element.name == tag:
                    if position == count_position:
                        dom_element = element
                        flag = True
                        break
                    else:
                        count_position += 1
                else:
                    flag = False
    if flag:
        return dom_element
    else:
        return False


class featureClass:
    feature_vectors = []
    none_tag = "textual_content"
    max_depth = -1
    next_dom = None
    current_timestamp = None
    nr_elements = 0
    nr_changed_elements = 0

    def __init__(self):
        self.feature_vectors = []
        self.max_depth = -1

    def reset_feature_vectors(self):
        self.feature_vectors = []
        self.max_depth = -1

    def generate_feature_vector_dom(self, dom_list, timestamp_list, project_name):
        skipped_doms = []
        for i in range(0, len(dom_list) - 1):
            self.current_timestamp = timestamp_list[i]
            try:
                parsed_dom = BeautifulSoup(dom_list[i], 'html.parser')
                parsed_dom2 = BeautifulSoup(dom_list[i + 1], 'html.parser')
            except TypeError:
                continue
            self.next_dom = parsed_dom2
            self.max_depth = cal_max_depth(parsed_dom)
            for tag in parsed_dom.contents:
                if tag.name != "html":
                    continue
                self.compare_dom_recursive(tag)
            if self.nr_changed_elements / self.nr_elements > 0.7:
                skipped_doms.append(self.current_timestamp)
        self.create_feature_csv(project_name, skipped_doms)

    def create_feature_csv(self, project_name, skipped_doms):
        header = ["node", "value", "timestamp", "position", "depth", "nr_siblings", "nr_children", "xpath", "siblings",
                  "changed"]
        full_list = []
        for feature_vector in self.feature_vectors:
            if feature_vector[1] in skipped_doms:
                continue
            full_list.append(feature_vector)
        df_tags = pd.DataFrame(full_list)
        df_tags.to_csv('data/feature_list_' + str(project_name) + '.csv', header=header, index=False)
        pass

    def recursive_soup(self, element):
        if str(type(element)) != "<class 'bs4.element.Tag'>":
            return
        if element.name == "head":
            return
        child_index = 0
        for child in element.contents:
            child_index += 1
            if str(type(child)) == "<class 'bs4.element.NavigableString'>":
                if child == "\n":
                    continue
                vector = generate_vectors_from_navigable_string(element,
                                                                child_index / len(element.contents), self.max_depth)
                self.feature_vectors.append(vector)
            self.recursive_soup(child)
        for feature_vector in generate_vectors_from_soup(element, self.max_depth):
            self.feature_vectors.append(feature_vector)

    def set_comparing_dom(self, dom):
        self.next_dom = BeautifulSoup(dom, 'html.parser')

    # def compare_dom_recursive(self, element, DO):
    #     if str(type(element)) != "<class 'bs4.element.Tag'>":
    #         return
    #     if element.name == "head" or element.name == "script":
    #         return
    #     child_index = 0
    #     for child in element.contents:
    #         child_index += 1
    #         if str(type(child)) == "<class 'bs4.element.NavigableString'>":
    #             if child == "\n":
    #                 continue
    #             vector = generate_vectors_from_navigable_string(DO, element, child_index, self.max_depth)
    #             self.feature_vectors.append(vector)
    #         self.compare_dom_recursive(child, DO)
    #     for feature_vector in generate_vectors_from_soup(DO, element, self.max_depth):
    #         self.feature_vectors.append(feature_vector)


def compare_dom_recursive(self, element):
    if str(type(element)) != "<class 'bs4.element.Tag'>":
        return

    if element.name in ["head", "script", "style"]:
        return

    for child_index, child in enumerate(element.contents, start=1):
        if str(type(child)) == "<class 'bs4.element.NavigableString'>":
            if child == "\n":
                continue
            self.nr_elements += 1
            feature_vector = generate_vectors_from_navigable_string(self.next_dom, self.current_timestamp, element,
                                                                    child_index / len(element.contents),
                                                                    self.max_depth)
            if feature_vector[8]:
                self.nr_changed_elements += 1
            self.feature_vectors.append(feature_vector)
        self.compare_dom_recursive(child)

    for feature_vector in generate_vectors_from_soup(self.next_dom, self.current_timestamp, element,
                                                     self.max_depth):
        self.nr_elements += 1
        if feature_vector[8]:
            self.nr_changed_elements += 1
        self.feature_vectors.append(feature_vector)

    def generate_locators(dom, bf_elements):
        DP = DynamicPredictor()
        cal_max_depth(dom)
        # cal_probablities()
        # for element in bf_elements:
