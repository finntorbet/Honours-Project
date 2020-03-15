# Do all work here for now
#       CONTROLLER
from . import Input
from . import Algorithm
from . import Metrics
import pandas as pd
import numpy as np
import os


def pipeline(input, algos, metrics, model):
    #       Setup pandas dataframe : Results
    temp = ['ID', 'Correct', 'Score', 'Predicted', 'Truth']
    for m in metrics:
        temp.append(m.name)
    x = pd.DataFrame(columns=temp)

    # Create n copies of x based on the number of algos
    results = []
    for i in range(len(algos)):
        results.append(x)

    data_counter = 0

    # Load all the data through the interpretability algorithm and metrics
    while input.has_next():

        # load data
        data = input.get_next()
        id = input.get_id()

        for x, a in enumerate(algos):

            def add_common_attributes(id, model, img, label):
                pred = model.predict(np.array([img]))
                pred_label = np.argmax(pred)
                score = pred[0][pred_label]
                if label == pred_label:
                    correct = True
                else:
                    correct = False
                return [id, correct, score, pred_label, label]

            # Process the default output (Correct, Score, Predicted, Labelled)
            current_row = add_common_attributes(id, model, data[0], data[1])

            matrix = a.pass_through(data[0], data[1])  # Send image and label away

            # Process algorithm result through all metrics
            for y, m in enumerate(metrics):
                current_row.append(m.process(matrix, data[2]))  # Send matrix and segmentation away

            results[x].loc[data_counter] = current_row
            data_counter = data_counter + 1

    return results


'''

    Plotting of data

'''

import seaborn as sns
import matplotlib.pyplot as plt


def histogram(results, save_path, metric_index):
    correct = results.loc[results['Correct'] == True].iloc[:, metric_index + 6]
    incorrect = results.loc[results['Correct'] == False].iloc[:, metric_index + 6]

    sns.distplot(correct, color='g', kde=False)
    sns.distplot(incorrect, color='r', kde=False)
    plt.savefig(save_path + "_hist.png")

    plt.clf()


def scatterplot(results, save_path, metric_index, y_name="Score"):
    sns.scatterplot(x=results.iloc[:, metric_index + 6], y=y_name, hue="Correct", style="Correct", data=results)
    plt.savefig(save_path + "_" + y_name + "_scatter.png")

    plt.clf()


"""
    Hons Pipeline  
        The Hons pipeline is the given pipeline for comparing grad_cam and shap against metrics Average and
        N. It takes a specified filepath 2D array, model and relevant model parameters.

        Filepaths should come as a 2D array of images, label then segmentation filepaths

"""


# e.g. filepath = [[list of image paths], [path to csv, target column], [list of segmentation paths]]
def Hons(model, filepaths, tags, input_size=(225, 300), output_size=(1022, 767),
         output=os.getcwd(), background=[], inside_colour=255,
         save_matrices=False, save_imgs=False, save_csv=False):
    #       INPUT
    # IMPROVE: Validate filepath[n] = expected_input_type[n]
    containers = [Input.Input_Image(filepaths[0], tags[0], input_size),
                  Input.Label(filepaths[1][0], tags[1], filepaths[1][1]),
                  Input.Segmentation(filepaths[2], tags[2], output_size)]
    input = Input.Sorter(containers)

    #       ALGO
    if background == []:
        l = Input.Linear_Loader(filepaths[0])
        while l.has_next():
            background.append(np.array([l.get_next()]))

    algos = [Algorithm.gradient_shap(background, model, output_size)]

    #       METRICS
    metrics = [Metrics.Average(inside_colour),
               Metrics.N(inside_colour, 1),
               Metrics.N(inside_colour, 2),
               Metrics.N(inside_colour, 3)]

    data = pipeline(input, algos, metrics)

    for i, result in enumerate(data):
        for m in range(len(metrics)):
            histogram(result, output + "_" + str(i), m)
            scatterplot(result, output + "_" + str(i), m)
            scatterplot(result, output + "_" + str(i), m, y_name="Average")

        if save_csv:
            result.to_csv(output + "" + str(i) + ".csv")


# e.g. filepath = [[list of image paths], [path to csv, target column], [list of segmentation paths]]
def pre_loaded_shap(filepath, tags, input_size=(225, 300), output_size=(1022, 767),
         output=os.getcwd(), inside_colour=255,
         save_matrices=False, save_imgs=False, save_csv=False):
    #       INPUT

    container = Input.Matrix(filepath)
    input = Input.Linear_Loader(container)

    #       ALGO
    algos = [Algorithm.empty()]

    #       METRICS
    metrics = [Metrics.Average(inside_colour),
               Metrics.N(inside_colour, 1),
               Metrics.N(inside_colour, 2),
               Metrics.N(inside_colour, 3)]

    data = pipeline(input, algos, metrics)

    for i, result in enumerate(data):
        for m in range(len(metrics)):
            histogram(result, output + "_" + str(i), m)
            scatterplot(result, output + "_" + str(i), m)
            scatterplot(result, output + "_" + str(i), m, y_name="Average")

        if save_csv:
            result.to_csv(output + "" + str(i) + ".csv")