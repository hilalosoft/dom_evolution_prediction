import os

import pandas as pd
import generate_statistics
from database.statistics import graphics


def main():
    filename = "filename.csv"
    chunksize = 100
    # chunksize = 10
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
    filename = os.getcwd() + "\\data\\feature_list_1688.csv"
    df = pd.read_csv(filename, delimiter=",")
    graphics.lineplot(df, "feature_list_1688", x=df.timestamp.apply(lambda f: pd.to_datetime(str(f))),
                      y=df['changed'])
    # graphics.lineplot(df, "feature_list_1337x", x=df["position"], y=df['changed'])
    # for column in list(df.columns):
    #     # graphics.lineplot(df, "tags_apple" + str(colum), x=df.index, y=column)
    #     graphics.lineplot(df, "facebook_" + "number_of_tags", x=df.index, y=column)
    # graphics.violinplot(df, "tags", x=df.index, y='string')
    # graphics.countplot(df, "tags", x='string')


generate_graphics()
# main()