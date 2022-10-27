import pandas as pd
from bs4 import BeautifulSoup
import soup_operations as so
import database.statistics.graphics as graphics
from database.Database_class import get_websites, get_history


def generate_statistics_from_dom(dom, timestamp):
    parsed_dom = BeautifulSoup(dom, 'html.parser')
    tag_dictionary = {}
    depth_list = []
    tag_list = []
    count_tags = 0
    max_depth = so.cal_max_depth(parsed_dom)

    for child in parsed_dom.descendants:
        if child.name is None:
            continue
        elif "id" in child.attrs and child['id'] == "wm-ipp":
            del child
            continue
        count_tags += 1
        position, siblings = so.get_siblings_soup(child)
        depth_list.append((child.name, so.cal_depth(child, max_depth), so.xpath_soup(child), position, siblings))
        if child.name in tag_dictionary:
            tag_dictionary[child.name] += 1
        else:
            tag_dictionary[child.name] = 1
    for key in tag_dictionary:
        tag_list.append((key, tag_dictionary[key]))

    df_tags = pd.DataFrame(tag_list)
    df_depth = pd.DataFrame(depth_list)
    # if not os.path.isfile('list.csv'):
    df_tags.to_csv('data/list_' + str(timestamp) + '.csv', header=["tag", "Occurrences"], index=False)
    df_depth.to_csv('data/tag_list_' + str(timestamp) + '.csv',
                    header=["tag", "depth", "xpath", "position", "siblings"],
                    index=False)
    # else:
    #     df_tags.to_csv('list.csv', mode='a', header=None, index=False)
    #     df_depth.to_csv('tag_list.csv', mode='a', header=None, index=False)

    df = pd.read_csv('data/list_' + str(timestamp) + '.csv')
    graphics.boxplot(df, "tag_list_" + str(timestamp), x='Occurrences', y="tag")


def generate_graphics_dom_list(dom_list, project_name):
    tag_dictionary = {}
    none_tag = "string"
    index = 1
    feature_vectors = []
    for dom in dom_list:
        dom_dictionary = {}
        count_tags = 0
        parsed_dom = BeautifulSoup(dom, 'html.parser')
        max_depth = so.cal_max_depth(parsed_dom)
        for child in parsed_dom.descendants:
            if str(type(child)) == "<class 'bs4.element.Script'>" or str(type(child)) == "<class 'bs4.element" \
                                                                                         ".Stylesheet'>" or str(
                type(child)) == "<class 'bs4.element.Comment'>" or str(
                type(child)) == "<class 'bs4.element.Declaration'>" or str(
                type(child)) == "<class 'bs4.element.TemplateString'>" or str(
                type(child)) == "<class 'bs4.element.typetext'>" or str(
                type(child)) == "<class 'bs4.element.Doctype'>":
                continue
            count_tags += 1
            if str(type(child)) == "<class 'bs4.element.NavigableString'>":
                # vector_array.append((none_tag, so.cal_depth(child), so.xpath_soup(child)))
                if none_tag in dom_dictionary:
                    dom_dictionary[none_tag] += 1
                else:
                    dom_dictionary[none_tag] = 1
            elif "id" in child.attrs and child['id'] == "wm-ipp":
                del child
                continue
            else:
                if child.name == "script":
                    continue
                feature_vectors.append(so.generate_vectors_from_soup(child, max_depth))
                if child.name in dom_dictionary:
                    dom_dictionary[child.name] += 1
                else:
                    dom_dictionary[child.name] = 1
        dom_dictionary['number_of_tags'] = count_tags
        for key in dom_dictionary:
            if key in tag_dictionary:
                tag_dictionary[key].append((index, dom_dictionary[key]))
            else:
                tag_dictionary[key] = []
                tag_dictionary[key].append((index, dom_dictionary[key]))
        index += 1

    # create_feature_csv(feature_vectors, project_name)

    # header = []
    # tag_list = [[0 for x in range(0, len(tag_dictionary))] for y in range(0, 1000)]
    # tag_indexes = {}
    # counter = 0
    # for key in tag_dictionary:
    #     header.append(key)
    #     tag_indexes[key] = counter
    #     counter += 1
    # for i in range(0, 1000):
    #     for key in tag_dictionary:
    #         for index_array in tag_dictionary[key]:
    #             if index_array[0] == i:
    #                 tag_list[i][tag_indexes[key]] = index_array[1]
    #                 continue
    #
    # df_tags = pd.DataFrame(tag_list)
    # df_tags.to_csv('data/list_' + str(project_name) + '.csv', header=header, index=False)

    # graphics.violinplot(df_tags, "tag_list_", x='Occurrences', y="tag")


def process(chunk):
    count = 0
    dom_list = []
    timestamp_list = []
    fc = so.featureClass()
    project_name = chunk.iloc[1][3]
    for index, row in chunk.iterrows():
        print(row[0], row[2], row[3], row[4], row[5], row[6], row[7])
        if row[3] != project_name:
            break
            # project_name = row[3]
        # generate_statistics_from_dom(row[1], row[7])
        dom_list.append(row[1])
        timestamp_list.append(row[7])

        count += 1
    if len(dom_list) > 2:
        fc.generate_feature_vector_dom(dom_list,timestamp_list, project_name)
    # generate_graphics_dom_list(dom_list, project_name)
    print('process number: ' + str(count))


def process_from_database():
    websites = get_websites()
    dom_list = []
    for website in websites:
        website_history = get_history(website)
        for version in website_history:
            dom_list.append(version[0])
        generate_graphics_dom_list(dom_list, website)
