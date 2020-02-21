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

HEADER = ["Consigne °C", "Consigne %HR", "Consigne PPM", "Mean %HR", "Std %HR", " Mean °C", " Std °C", "Mean PPM", "Std PPM", "Start", "End"]

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
            self.folders_sec = []
            self.folders_humide = []
            for _, dirs, _ in os.walk(self.folder_selected):
                for dir in dirs:
                    if "results" in dir:
                        pass
                    elif "humide" in dir:
                        self.folders_humide.append(dir)
                    else :
                        self.folders_sec.append(dir)

            self.target_dir = self.folder_selected+"\\results"

            if os.path.exists(self.target_dir) == False:
                os.makedirs(self.target_dir)
                #shutil.rmtree(self.target_dir)

            df_sec, last_three_df_sec = self.processCycles(self.folders_sec)
            df_humide, last_three_df_humide = self.processCycles(self.folders_humide)

            df_sec.to_csv(self.target_dir + "\\final_result_sec.csv", sep=',', encoding='utf-8', index=False)
            df_humide.to_csv(self.target_dir + "\\final_result_humide.csv", sep=',', encoding='utf-8', index=False)

            last_three_df_sec.to_csv(self.target_dir + "\\last_three_final_result_sec.csv", sep=',', encoding='utf-8', index=False)
            last_three_df_humide.to_csv(self.target_dir + "\\last_three_final_result_humide.csv", sep=',', encoding='utf-8', index=False)

            self.state_var.set("Done!")

    def sortFunction(self, val): 
        return val[9]

    def processCycles(self, folderToProcess):
        final_result = []
        last_three_final_results = []
        for cycle in folderToProcess:
            currentCycle = os.path.join(self.folder_selected, cycle)
            cycle_results = self.processCycle(currentCycle)
            cycle_results_copy = copy.deepcopy(cycle_results)
            final_result.extend(cycle_results)
            general_params = cycle_results_copy[0][:3]
            cycle_results_copy.sort(key = self.sortFunction)
            last_three = cycle_results_copy[-3:]
            last_three[0][0] = general_params[0]
            last_three[0][1] = general_params[1]
            last_three[0][2] = general_params[2]
            for i in range(1,3):
                last_three[i][0] = ''
                last_three[i][1] = ''
                last_three[i][2] = ''

            last_three_final_results.extend(last_three)

        df = DataFrame(final_result, columns= HEADER)
        last_three_df = DataFrame(last_three_final_results, columns= HEADER)
        
        return df, last_three_df

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
        for _, _, files in os.walk(currentCycleFolder):
            for file in files:
                try:
                    tt = pd.read_csv(os.path.join(currentCycleFolder, file))
                    tt = tt[tt['timestamp'].map(math.isnan) == False]
                    data = []
                    # Consignes
                    if len(final_result) == 0:
                        data.append(temperature[0])
                        data.append(humidity[0])
                        data.append(pressure[0])
                    else:
                        data.append('')
                        data.append('')
                        data.append('')
                    # Mesures
                    data.append(tt["rel_humidity"].mean())
                    data.append(tt["rel_humidity"].std())
                    data.append(tt["temp"].mean()/10.0)
                    data.append(tt["temp"].std())
                    data.append(tt["comp_h2"].mean())
                    data.append(tt["comp_h2"].std())
                    data.append(datetime.fromtimestamp(tt["timestamp"].iloc[0]))
                    data.append(datetime.fromtimestamp(tt["timestamp"].iloc[-1]))
                    final_result.append(data)
                except:
                    pass
                    #print("yo!")
                    #print(os.path.join(currentCycleFolder, file))
        
        return final_result

    def select_folder_btn_clicked(self):
        self.folder_selected = filedialog.askdirectory()
        print(self.folder_selected)
        self.state_var.set("Folder selected!")

if __name__ == "__main__":
    root = tk.Tk()
    app = App()
    app.mainloop()