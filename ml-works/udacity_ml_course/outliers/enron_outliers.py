#!/usr/bin/python

import pickle
import sys
import matplotlib.pyplot
from operator import itemgetter

sys.path.append("../tools/")
from feature_format import featureFormat, targetFeatureSplit


# read in data dictionary, convert to numpy array
data_dict = pickle.load(open("../final_project/final_project_dataset.pkl", "r"))

features = ["salary", "bonus"]

data_dict.pop("TOTAL", None)

data = featureFormat(data_dict, features)

# your code below

data = sorted(data, key=itemgetter(1))

print(data[len(data)-2])
print(data[len(data)-3])

for point in data:
    salary = point[0]
    bonus = point[1]
    matplotlib.pyplot.scatter(salary, bonus)

matplotlib.pyplot.xlabel("salary")
matplotlib.pyplot.ylabel("bonus")
matplotlib.pyplot.show()
