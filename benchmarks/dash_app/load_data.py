#!/usr/bin/env python3

# Copyright (c) Facebook, Inc. and its affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.


import os

import pandas as pd


def get_available_dates(data_dir):
    """Returns list of available dates in DATA_PATH directory"""
    available_dates = []

    for sub_dir in os.listdir(data_dir):
        if os.path.isdir(os.path.join(data_dir, sub_dir)):
            available_dates.append(sub_dir)

    return available_dates


def read_data(data_dir, dates, cuda=False):
    """Builds dataframe for model and func benchmarks Assumes directory is structured as
     DATA_PATH
        |_2020-02-20
            |_func_benchmarks.csv
            |_model_benchmarks.csv
            |_func_benchmarks_cuda.csv (optional)
            |_model_benchmarks_cuda.csv (optional)
    Args:
        data_dir (pathlib.path): path containing month subdirectories
        dates (list of str): containing dates / subdirectories available
    Returns: tuple of pd.DataFrames containing func and model benchmarks with dates
    """
    func_df, model_df = pd.DataFrame(), pd.DataFrame()
    postfix = "_cuda" if cuda else ""
    device = "gpu" if cuda else "cpu"

    for date in dates:
        path = os.path.join(data_dir, date)

        func_path = os.path.join(path, f"func_benchmarks{postfix}.csv")
        model_path = os.path.join(path, f"model_benchmarks{postfix}.csv")

        tmp_func_df, tmp_model_df = None, None

        if os.path.exists(func_path):
            tmp_func_df = pd.read_csv(func_path)
            set_metadata(tmp_func_df, date, device)
        if os.path.exists(model_path):
            tmp_model_df = pd.read_csv(model_path)
            set_metadata(tmp_model_df, date, device)

        func_df = func_df.append(tmp_func_df)
        model_df = model_df.append(tmp_model_df)

    if not func_df.empty:
        func_df = compute_runtime_gap(func_df)
        func_df = add_error_bars(func_df)
    return func_df, model_df


def set_metadata(df, date, device):
    """Set the device and date attribute for the dataframe"""
    df["date"] = date
    df["device"] = device


def compute_runtime_gap(func_df):
    """Computes runtime gap between CrypTen and Plain Text"""
    func_df["runtime gap"] = func_df["runtime crypten"] / func_df["runtime"]
    func_df["runtime gap Q1"] = func_df["runtime crypten Q1"] / func_df["runtime"]
    func_df["runtime gap Q3"] = func_df["runtime crypten Q3"] / func_df["runtime"]
    return func_df


def add_error_bars(func_df):
    """Adds error bars for plotting based on Q1 and Q3"""
    columns = ["runtime crypten", "runtime gap"]
    for col in columns:
        func_df = calc_error_bar(func_df, col)
    return func_df


def calc_error_bar(df, column_name):
    """Adds error plus and minus for plotting"""
    error_plus = df[column_name + " Q3"] - df[column_name]
    error_minus = df[column_name] - df[column_name + " Q1"]
    df[column_name + " error plus"] = error_plus
    df[column_name + " error minus"] = error_minus
    return df
