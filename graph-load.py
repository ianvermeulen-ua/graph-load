import os
import os.path

import json

import re

import numpy
import dateutil

import matplotlib
matplotlib.use('Agg')

import matplotlib.pyplot as plot
import seaborn as sns

#["2017-04-26T14:11:07.098757", 98.9, 0.008773621240292634]


class Sample:
    def __init__(self, timestamp=None, cpu_percent=0.0, memory_percent=0.0):
        self.__timestamp = timestamp
        self.__cpu_percent = cpu_percent
        self.__memory_percent = memory_percent

    @classmethod
    def read(cls, data):
        timestamp = data[0]
        cpu_percent = data[1]
        memory_percent = data[2]

        return cls(timestamp, cpu_percent, memory_percent)

    @property
    def timestamp(self):
        return self.__timestamp

    @property
    def cpu_percent(self):
        return self.__cpu_percent

    @property
    def memory_percent(self):
        return self.__memory_percent


class SamplesReader:
    def __init__(self, *run_paths_args):
        self.__run_files = []

        for i in range(0, len(run_paths_args)):
            run_path_arg = run_paths_args[i]

            self.__run_files += [{}]

            for run_path in run_path_arg:
                self.__run_files[i][run_path] = \
                    [x for x in os.listdir(run_path) if os.path.isfile(os.path.join(run_path, x))]

    def read(self, files_index=0):
        all_samples = {}

        for run_path, run_files in self.__run_files[files_index].items():
            print("Now at experiment %s" % run_path)

            path_match = re.match(r".*\/experiment([0-9])+\/reports\/runs", run_path)

            if path_match:
                experiment_id = int(path_match.group(1))

                print("Processing experiment %d" % experiment_id)

                for run_file in run_files:
                    file_match = re.match(r"[0-9]\_([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+)\_lvap\_([0-9]+)\_wtp\_([0-9]+)",
                                           run_file)

                    if file_match:
                        controller = file_match.group(1)
                        lvap_amount = int(file_match.group(2))
                        wtp_amount = int(file_match.group(3))

                        with open(os.path.join(run_path, run_file), 'r') as f:
                            run_samples = json.load(f)

                            if experiment_id not in all_samples:
                                all_samples[experiment_id] = {}

                            if controller not in all_samples[experiment_id]:
                                all_samples[experiment_id][controller] = {}

                            if wtp_amount not in all_samples[experiment_id][controller]:
                                all_samples[experiment_id][controller][wtp_amount] = {}

                            all_samples[experiment_id][controller][wtp_amount][lvap_amount] = \
                                [Sample.read(x) for x in run_samples]

        return all_samples


class SamplesAnalyzer:
    def __init__(self, samples):
        self.__samples = samples

    def average(self, wtp_amount, lvap_amount, controller=None):
        cpu_percentages = []
        memory_percentages = []

        samples = self.__samples

        for experiment_id in samples:
            if controller:
                cpu_percentages += \
                    [x.cpu_percent for x in samples[experiment_id][controller][wtp_amount][lvap_amount]]

                memory_percentages += \
                    [x.memory_percent for x in samples[experiment_id][controller][wtp_amount][lvap_amount]]
            else:
                for current_controller in samples[experiment_id]:
                    cpu_percentages += \
                        [x.cpu_percent for x in samples[experiment_id][current_controller][wtp_amount][lvap_amount]]

                    memory_percentages += \
                        [x.memory_percent for x in samples[experiment_id][current_controller][wtp_amount][lvap_amount]]

        cpu_average = numpy.average(cpu_percentages)
        memory_average = numpy.average(memory_percentages)

        cpu_deviation = numpy.std(cpu_percentages)
        memory_deviation = numpy.std(cpu_percentages)

        return cpu_average, cpu_deviation, memory_average, memory_deviation

    def get_stats(self, wtp_amount, controller=None):
        lvap_amounts = list(range(25, 625, 25))

        cpu_plot_data = {}
        memory_plot_data = {}

        for lvap_amount in lvap_amounts:
            averages = self.average(wtp_amount, lvap_amount, controller)
            cpu_plot_data[lvap_amount] = averages[:2]
            memory_plot_data[lvap_amount] = averages[2:]

        return cpu_plot_data, memory_plot_data


class SamplePlotter:
    def __init__(self):
        pass

    def create_wtp_graph(self, wtp_amount, cpu_plot_data, memory_plot_data, controller=None):
        if controller:
            cpu_filename = "%s_wtp_%d_cpu.png" % (controller, wtp_amount)
            memory_filename = "%s_wtp_%d_memory.png" % (controller, wtp_amount)
        else:
            cpu_filename = "avg_wtp_%d_cpu.png" % wtp_amount
            memory_filename = "avg_wtp_%d_memory.png" % wtp_amount

        self.create_plot(cpu_plot_data, "Number of LVAPs", "CPU usage(%)", cpu_filename)
        self.create_plot(memory_plot_data, "Number of LVAPs", "Memory usage(%)", memory_filename)

    def create_plot(self, plots_data, x_label, y_label, filename):
        _, ax = plot.subplots()

        for plot_name, plot_data in plots_data.items():
            lists = sorted(plot_data.items())

            x, y = zip(*lists)

            y_0 = [i[0] for i in y]
            y_1 = [i[1] for i in y]

            ax.plot(x, y_0, label="Average %s" % plot_name)

        plot.xlabel(x_label)
        plot.ylabel(y_label)

        ax.legend()

        plot.savefig(filename)
        plot.gcf().clear()

if __name__ == "__main__":
    run_paths_1 = ["/Users/ianvermeulen/Google Drive/School/Thesis/tests/load/1 controllers/experiment1/reports/runs"]
    run_paths_2 = ["/Users/ianvermeulen/Google Drive/School/Thesis/tests/load/2 controllers/experiment1/reports/runs",
                   "/Users/ianvermeulen/Google Drive/School/Thesis/tests/load/2 controllers/experiment2/reports/runs"]

    sample_reader = SamplesReader(run_paths_1, run_paths_2)

    samples_1 = sample_reader.read(0)
    samples_2 = sample_reader.read(1)

    samples_analyzer_1 = SamplesAnalyzer(samples_1)
    samples_analyzer_2 = SamplesAnalyzer(samples_2)

    cpu_1, memory_1 = samples_analyzer_1.get_stats(20)
    cpu_2, memory_2 = samples_analyzer_2.get_stats(10)

    diff = {lvap : numpy.subtract(cpu_1[lvap], cpu_2[lvap]) for lvap in cpu_1}

    sample_plotter = SamplePlotter()
    sample_plotter.create_wtp_graph(20, {"1 controller" : cpu_1,
                                         "2 controllers" : cpu_2,
                                         "1 controller - Average 2 controllers" : diff},
                                    {"1 controller" : memory_1, "2 controllers" : memory_2})


