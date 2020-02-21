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

HEADER = ["Consigne %HR", "Consigne °C", "Consigne PPM", "Mean %HR", "Std %HR", " Mean °C", " Std °C", "Mean PPM", "Std PPM", "Start", "End"]

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

            df_sec = self.processCycles(self.folders_sec)
            df_humide = self.processCycles(self.folders_humide)

            df_sec.to_csv(self.target_dir + "\\final_result_sec.csv", sep=',', encoding='utf-8')
            df_humide.to_csv(self.target_dir + "\\final_result_humide.csv", sep=',', encoding='utf-8')

            self.state_var.set("Done!")

    def processCycles(self, folderToProcess):
        final_result = []
        for cycle in folderToProcess:
            currentCycle = os.path.join(self.folder_selected, cycle)
            final_result.extend(self.processCycle(currentCycle))

        df = DataFrame(final_result, columns= HEADER)
        #df.to_csv(self.target_dir + "\\final_result_sec.csv", sep=',', encoding='utf-8')
        return df

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
        try:
            for _, _, files in os.walk(currentCycleFolder):
                for file in files:
                    tt = pd.read_csv(os.path.join(currentCycleFolder, file))
                    try:
                        tt = tt[tt['timestamp'].map(math.isnan) == False]
                    except:
                        print("exception!")
                    data = []
                    # Consignes
                    if len(final_result) == 0:
                        data.append(humidity[0])
                        data.append(temperature[0])
                        data.append(pressure[0])
                    else:
                        data.append('')
                        data.append('')
                        data.append('')
                    # Mesures
                    data.append(tt["rel_humidity"].mean())
                    data.append(tt["rel_humidity"].std())
                    data.append(tt["temp"].mean())
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