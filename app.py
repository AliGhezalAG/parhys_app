#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from tkinter import filedialog
import tkinter as tk
import os
import re
import shutil
import csv
import pandas as pd
from pandas import DataFrame
from datetime import datetime
import math
import copy
import numpy as np
import matplotlib
matplotlib.use("Agg")
from matplotlib import pyplot as plt

HEADER = ["Consigne °C", "Consigne %HR", "Consigne PPM", "Mean %HR", "σ %HR", "2xσ %HR", " Mean °C", " σ °C", "2xσ °C", "Mean PPM", "σ PPM", "2xσ PPM", "Start", "End"]

class App(tk.Frame):
    def __init__(self):
        tk.Frame.__init__(self)
        self.master.title("Parhys data processing")
        self.grid()

        # set grid columns config
        for i in range(2):
            self.grid_columnconfigure(index=i, weight=10, minsize=120)

        # set grid rows config
        for i in range(3):
            self.grid_rowconfigure(index=i, weight=10, minsize=40)

        # Select folder to process command button
        select_folder_label = tk.Label(self, text="Select folder")
        select_folder_label.grid(column=0, row=0, columnspan=1)
        get_data_btn = tk.Button(self, text="Browse", command = self.select_folder_btn_clicked)
        get_data_btn.grid(column=1, row=0, columnspan=1, sticky="W")

        # Process data command button
        get_data_btn = tk.Button(self, text="Process data", command = self.process_data_btn_clicked)
        get_data_btn.grid(column=0, row=1, columnspan=2)

        # State label
        self.state_var = tk.StringVar()
        self.state_var.set("Please select a folder to process")
        state_label = tk.Label(self, textvariable=self.state_var)
        state_label.grid(column=0, row=2, columnspan=2)

        self.folder_selected = ""

    def process_data_btn_clicked(self):
        if self.folder_selected == "":
            self.state_var.set("No folder selected!")
        else:
            self.state_var.set("Processing data...")
            self.update()
            try:
                self.folders_sec = []
                self.folders_humide = []

                self.target_dir = self.folder_selected+"\\results"

                if os.path.exists(self.target_dir) == True:
                    shutil.rmtree(self.target_dir)

                for _, dirs, _ in os.walk(self.folder_selected):
                    for dir in dirs:
                        if "humide" in dir:
                            self.folders_humide.append(dir)
                        else :
                            self.folders_sec.append(dir)

                if os.path.exists(self.target_dir) == False:
                    os.makedirs(self.target_dir)
                    os.makedirs(self.target_dir+"\\humide")
                    os.makedirs(self.target_dir+"\\sec")

                df_sec, last_three_df_sec = self.processCycles(self.folders_sec, "SEC")
                df_humide, last_three_df_humide = self.processCycles(self.folders_humide, "HUMIDE")

                df_sec.to_csv(self.target_dir + "\\sec\\final_result_sec.csv", sep=',', encoding='utf-8', index=False)
                df_humide.to_csv(self.target_dir + "\\humide\\final_result_humide.csv", sep=',', encoding='utf-8', index=False)

                last_three_df_sec.to_csv(self.target_dir + "\\sec\\last_three_final_result_sec.csv", sep=',', encoding='utf-8', index=False)
                last_three_df_humide.to_csv(self.target_dir + "\\humide\\last_three_final_result_humide.csv", sep=',', encoding='utf-8', index=False)

                self.state_var.set("Done!")
                self.update()
            except:
                self.state_var.set("Oups! Something went wrong, please try again.")
                self.update()

    def sortFunction(self, val): 
        return val[12]

    def dataFrameSortFunction(self, val): 
        return val['timestamp'].iloc[0]

    def processCycles(self, folderToProcess, type):
        if type == "SEC":
            fig_folder = os.path.join(self.folder_selected, "results\\sec")
        else:
            fig_folder = os.path.join(self.folder_selected, "results\\humide")

        final_result = []
        last_three_final_results = []
        for cycle in folderToProcess:
            currentCycle = os.path.join(self.folder_selected, cycle)
            cycle_results, last_three_data = self.processCycle(currentCycle)    

            
            fig = plt.figure()

            x = range(1, len(cycle_results)+1)
            y = [tup[9] for tup in cycle_results]
            yerr = [tup[11] for tup in cycle_results]

            plt.errorbar(x, y, yerr=yerr, uplims=True, lolims=True)
            fig.suptitle(cycle)
            plt.xlabel('Sample number')
            plt.ylabel('Mean pressure & standard deviation (PPM)')
            fig.savefig(fig_folder + '\\' + cycle +'.png')
            plt.close(fig)

            cycle_results_copy = copy.deepcopy(cycle_results)
            cycle_results.append(last_three_data)
            final_result.extend(cycle_results)
            general_params = cycle_results_copy[0][:3]
            cycle_results_copy.sort(key = self.sortFunction)
            last_three = cycle_results_copy[-3:]
            last_three[0][0] = general_params[0]
            last_three[0][1] = general_params[1]
            last_three[0][2] = general_params[2]
            for i in range(1,min(len(last_three),3)):
                last_three[i][0] = ''
                last_three[i][1] = ''
                last_three[i][2] = ''

            last_three_final_results.extend(last_three)

        df = DataFrame(final_result, columns= HEADER)
        last_three_df = DataFrame(last_three_final_results, columns= HEADER)

        return df, last_three_df

    def processFile(self, df, data):
        data.append(df["rel_humidity"].mean()/10.0)
        data.append(df["rel_humidity"].std())
        data.append(df["rel_humidity"].std()*2.0)
        data.append(df["temp"].mean()/10.0)
        data.append(df["temp"].std())
        data.append(df["temp"].std()*2.0)
        data.append(df["comp_h2"].mean())
        data.append(df["comp_h2"].std())
        data.append(df["comp_h2"].std()*2.0)
        data.append(datetime.fromtimestamp(df["timestamp"].iloc[0]))
        data.append(datetime.fromtimestamp(df["timestamp"].iloc[-1]))
        return data

    def processCycle(self, currentCycleFolder):
        humidity = re.findall(r'°C - (.+?)%HR',currentCycleFolder)
        if len(humidity) > 0:
            pressure = re.findall(r'%HR - (.+?)PPM',currentCycleFolder)
        else:
            pressure = re.findall(r'°C (.+?)PPM',currentCycleFolder)
            humidity = ['0']

        
        temperature = re.findall(r'CYCLE 1-2-3 - (.+?)°C',currentCycleFolder)
        if len(temperature) == 0:
            temperature = re.findall(r'CYCLE 1-2-3 (.+?)°C',currentCycleFolder)
        if len(temperature) == 0:
            temperature = re.findall(r'CYCLE 1-2-3- (.+?)°C',currentCycleFolder)

        final_result = []
        last_three_measures = []
        for _, _, files in os.walk(currentCycleFolder):
            for file in files:
                try:
                    tt = pd.read_csv(os.path.join(currentCycleFolder, file))
                    if len(tt.columns) == 7:
                        tt = tt[tt['timestamp'].map(math.isnan) == False]
                        tt = tt[tt['adc_mv'].map(math.isnan) == False]
                        tt = tt[tt['comp_h2']  != 0]

                        if len(tt.values) > 0:
                            if len(last_three_measures) < 3:
                                last_three_measures.append(tt)
                            else:
                                last_three_measures.sort(key = self.dataFrameSortFunction)
                                if tt["timestamp"].iloc[0] > last_three_measures[2]["timestamp"].iloc[0]:
                                    last_three_measures[0] = tt

                            data = []
                            # Consignes
                            if len(final_result) == 0:
                                data.append(temperature[0])
                                data.append(humidity[0])
                                data.append(pressure[0])
                            else:
                                data.extend(['', '', ''])
                            final_result.append(self.processFile(tt, data))
                except pd.errors.EmptyDataError:
                    pass

        last_three_concat = []
        last_three_measures.sort(key = self.dataFrameSortFunction)
        for dtf in last_three_measures:
            last_three_concat.extend(dtf.values)
        try:
            last_three = pd.DataFrame(last_three_concat, columns=last_three_measures[0].columns)
            data = ['', '', '']
            data = self.processFile(last_three, data)
        except:
            print(last_three_measures[2].columns)
            print(currentCycleFolder)

        return final_result, data

    def select_folder_btn_clicked(self):
        self.folder_selected = filedialog.askdirectory()
        print(self.folder_selected)
        self.state_var.set("Folder selected!")

if __name__ == "__main__":
    root = tk.Tk()
    app = App()
    app.mainloop()