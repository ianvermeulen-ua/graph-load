import json

import numpy

import matplotlib
matplotlib.use('Agg')

import matplotlib.pyplot as plot
import seaborn as sns

if __name__ == "__main__":
    with open("diff-mat-1.json", "r") as f:
        diff_1 = json.load(f)

    with open("diff-mat-2.json", "r") as f:
        diff_2 = json.load(f)

    if diff_1['x'] != diff_2['x']:
        print("Cannot create diff graph")
    else:
        x = diff_1['x']
        y_0 = numpy.subtract(diff_1['y_0'], diff_2['y_0'])

        _, ax = plot.subplots()

        ax.plot(x, y_0, label="Average difference")

        plot.xlabel("Number of LVAPs")
        plot.ylabel("CPU usage(%)")

        ax.legend()

        plot.savefig("diff.png")
        plot.gcf().clear()

