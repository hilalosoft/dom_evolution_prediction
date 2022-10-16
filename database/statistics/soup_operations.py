import pandas as pd
from bs4 import BeautifulSoup

considered_tag_dictionary = {"id": 0, "string": 0, "ul": 0, "li": 0, "h1": 0, "h2": 0, "h3": 0, "h4": 0, "h5": 0,
                             "div": 0
    , "span": 0, "form": 0, "input": 0, "p": 0, "img": 0, 'a': 0, "dl": 0, "dt": 0, "dd": 0, "svg": 0, "path": 0, "g": 0
    , "option": 0, "i": 0, "attribute": 0, "button": 0, "class": 0, "href": 0}


# we copy the dictionary containing considered tags iterate over all the siblings,
# determine the element position within its peers and divide in the end on the number of siblings to normalize.
# normalize the position in the end
def get_siblings_soup(soup):
    siblings_dict = considered_tag_dictionary.copy()
    count = 1
    for sibling in soup.previous_siblings:
        count += 1
        if sibling.name in siblings_dict:
            siblings_dict[sibling.name] += 1
        # siblings_list.append(sibling.name)
    position = count
    for sibling in soup.next_siblings:
        count += 1
        if sibling.name in siblings_dict:
            siblings_dict[sibling.name] += 1
        # siblings_list.append(sibling.name)
    for key in siblings_dict:
        siblings_dict[key] = siblings_dict[key] / count
    position = position / count
    return position, siblings_dict


def get_siblings_attr(soup, attr):
    siblings_dict = considered_tag_dictionary.copy()
    for attribute in soup.attrs:
        if attribute == attr:
            continue
        if attribute in siblings_dict:
            siblings_dict[attribute] += 1
    return siblings_dict


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


def cal_max_depth(dom):
    ignored_list = ["<class 'bs4.element.Script'>", "<class 'bs4.element.Stylesheet'>", "<class 'bs4.element.Comment'>"
        , "<class 'bs4.element.Declaration'>", "<class 'bs4.element.TemplateString'>"
        , "<class 'bs4.element.NavigableString'>", "<class 'bs4.element.Doctype'>"]
    maximum_depth = -1
    for child in dom.descendants:
        if child == '\n':
            continue
        child_depth = cal_depth(child)
        if child_depth > maximum_depth:
            maximum_depth = child_depth
            if str(type(child)) not in ignored_list and len(child.attrs) > 0:
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


def generate_vector(node, position, depth, nr_siblings, nr_children, xpath, siblings):
    vector = [node, position, depth, nr_siblings, nr_children, xpath, siblings]
    return vector


def generate_vectors_from_navigable_string(soup, index, max_depth):
    siblings_dict = considered_tag_dictionary.copy()
    vector = generate_vector("textual_content", index, cal_depth(soup, max_depth), 0, 0, xpath_soup(soup),
                             siblings_dict)
    return vector


def generate_vectors_from_soup(soup, max_depth):
    nr_of_children = len(soup.contents) + len(soup.attrs)
    position, siblings_vector = get_siblings_soup(soup)
    xpath = xpath_soup(soup)
    depth = cal_depth(soup, max_depth)
    vector_list = []
    for vector in generate_vectors_for_attr(soup, max_depth):
        vector_list.append(vector)
    vector_list.append(
        generate_vector(soup.name, position, depth, len(siblings_vector), nr_of_children, xpath, siblings_vector))
    return vector_list


def generate_vectors_for_attr(soup, max_depth):
    final_vectors = []
    for attr in soup.attrs:
        if attr == "class":
            nr_of_children = len(soup.attrs[attr])
        else:
            nr_of_children = 1
        siblings_vector = get_siblings_attr(soup, attr)
        xpath = xpath_soup(soup) + "/" + str(soup.attrs[attr])
        depth = cal_depth(soup, max_depth, True)
        final_vectors.append(
            generate_vector(attr + str(soup.attrs[attr]), 0, depth, len(soup.attrs) - 1, 0, xpath, siblings_vector))
    return final_vectors


def create_feature_csv(feature_vectors, project_name):
    header = ["node", "position", "depth", "nr_siblings", "nr_children", "xpath", "siblings"]
    full_list = []
    for feature_vector in feature_vectors:
        full_list.append(feature_vector)
    df_tags = pd.DataFrame(full_list)
    df_tags.to_csv('data/feature_list_' + str(project_name) + '.csv', header=header, index=False)
    pass


class featureClass:
    feature_vectors = []
    none_tag = "textual_conent"
    max_depth = -1
    dom1 = None
    dom2 = None

    def __init__(self):
        self.feature_vectors = []
        self.max_depth = -1

    def reset_feature_vectors(self):
        self.feature_vectors = []
        self.max_depth = -1

    def generate_feature_vector_dom(self, dom_list, project_name):
        for dom in dom_list:
            parsed_dom = BeautifulSoup(dom, 'html.parser')
            self.max_depth = cal_max_depth(parsed_dom)
            for tag in parsed_dom.contents:
                if tag.name != "html":
                    continue
                self.recursive_soup(tag)
        create_feature_csv(self.feature_vectors, project_name)

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
                vector = generate_vectors_from_navigable_string(element, child_index, self.max_depth)
                self.feature_vectors.append(vector)
            self.recursive_soup(child)
        for feature_vector in generate_vectors_from_soup(element, self.max_depth):
            self.feature_vectors.append(feature_vector)

    def set_comparing_doms(self, dom1, dom2):
        self.dom1 = BeautifulSoup(dom1, 'html.parser')
        self.dom2 = BeautifulSoup(dom2, 'html.parser')

    def compare_dom_recursive(self, element):
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
                vector = generate_vectors_from_navigable_string(element, child_index, self.max_depth)
                self.feature_vectors.append(vector)
            self.recursive_soup(child)
        for feature_vector in generate_vectors_from_soup(element, self.max_depth):
            self.feature_vectors.append(feature_vector)
