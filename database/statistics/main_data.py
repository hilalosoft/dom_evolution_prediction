import os

import pandas as pd
import generate_statistics
from database.statistics import graphics


def main():
    filename = "filename.csv"
    # chunksize = 10 ** 3
    chunksize = 10
    count = 0
    # get_websites
    with pd.read_csv(filename, chunksize=chunksize) as reader:
        for chunk in reader:
            count += 1
            # if count < 15:
            #     continue
            generate_statistics.process(chunk)
            continue
        print('chunk number: ' + str(count))
    # generate_statistics.process_from_database()


def generate_graphics():
    filename = os.getcwd() + "\\data\\list_duckduckgo.csv"
    df = pd.read_csv(filename)
    # graphics.violinplot(df, "tags", x=df.index, y='string')
    # graphics.countplot(df, "tags", x='string')

    graphics.lineplot(df, "duckduckgo" + "number_of_tags", x=df.index, y=df['number_of_tags'])
    # for column in list(df.columns):
    #     # graphics.lineplot(df, "tags_apple" + str(column), x=df.index, y=column)
    #     graphics.lineplot(df, "facebook_" + "number_of_tags", x=df.index, y=column)


# generate_graphics()
main()