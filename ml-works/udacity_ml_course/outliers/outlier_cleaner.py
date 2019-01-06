#!/usr/bin/python
import math


def outlierCleaner(predictions, ages, net_worths):
    """
        Clean away the 10% of points that have the largest
        residual errors (difference between the prediction
        and the actual net worth).

        Return a list of tuples named cleaned_data where 
        each tuple is of the form (age, net_worth, error).
    """

    cleaned_data = []

    # your code goes here
    for index, prediction in enumerate(predictions):
        error = prediction[0] - net_worths[index]
        cleaned_data.append((ages[index][0], net_worths[index][0], error[0]))

    cleaned_data = sorted(cleaned_data, key=lambda x: x[2])

    total_length = len(cleaned_data)
    ten_percent = math.floor(0.1 * total_length)

    cleaned_data = cleaned_data[:int(total_length - ten_percent)]

    return cleaned_data
