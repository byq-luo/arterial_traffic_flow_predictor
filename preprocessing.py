import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import datetime as dt
from statsmodels.tsa.seasonal import seasonal_decompose

import utils
import visualization

def reindex_with_nans(data, data_freq):
    time = data.index.to_pydatetime()
    full_time = min(time) + np.arange((max(time) - min(time)) / data_freq + 1)*data_freq

    data_unimputed = data.reindex(full_time, fill_value=np.nan)

    return data_unimputed

def seasonal_decomposition_linear_interpolation_imputation(data, data_freq, seasonal_freq, graph=False, lower_bound=None, upper_bound=None, title=None, ylabel=None, figsize=None):
    """Imputes seasonal time series data for a dataframe with a Datetime
    Index with missing values."""

    data_unimputed = reindex_with_nans(data, data_freq)

    # Perform linear interpolation so we can use seasonal_decompose
    data = data_unimputed.interpolate()

    sd = seasonal_decompose(data, freq=seasonal_freq)

    if graph:
        visualization.plot_data_over_time(sd.observed, title="{} Original".format(title), ylabel=ylabel, figsize=figsize)
        visualization.plot_data_over_time(sd.trend, title="{} Trend".format(title), ylabel=ylabel, figsize=figsize)
        visualization.plot_data_over_time(sd.resid, title="{} Resid".format(title), ylabel=ylabel, figsize=figsize)
        visualization.plot_data_over_time(sd.seasonal, title="{} Seasonal".format(title), ylabel=ylabel, figsize=figsize)

    sd.trend[data_unimputed.isnull()] = np.nan
    sd.resid[data_unimputed.isnull()] = np.nan

    if graph:
        visualization.plot_data_over_time(sd.trend, title="{} Trend Broken".format(title), ylabel=ylabel, figsize=figsize)
        visualization.plot_data_over_time(sd.resid, title="{} Resid Broken".format(title), ylabel=ylabel, figsize=figsize)

    sd.trend = sd.trend.interpolate()
    sd.resid = sd.resid.interpolate()

    if graph:
        visualization.plot_data_over_time(sd.trend, title="{} Trend Interpolated".format(title), ylabel=ylabel, figsize=figsize)
        visualization.plot_data_over_time(sd.resid, title="{} Resid Interpolated".format(title), ylabel=ylabel, figsize=figsize)

    data_imputed = (sd.trend + sd.resid + sd.seasonal).clip(lower=lower_bound, upper=upper_bound)
    data_imputed.fillna(data_unimputed, inplace=True)

    if graph:
        visualization.plot_data_over_time(data_imputed, title="{} Imputed".format(title), ylabel=ylabel, figsize=figsize)

    return data_imputed

def get_longest_continuous_stretch_of_data(data, freq):
    data = data.dropna()
    index = data.index

    break_indices = np.argwhere((index[1:] - index[:-1]) != freq).flatten() + 1
    stretch_starts = np.concatenate(([0], break_indices, [data.shape[0]]))
    stretch_lengths = stretch_starts[1:] - stretch_starts[:-1]
    longest_stretch_start_index = stretch_lengths.argmax()

    stretch_start = stretch_starts[longest_stretch_start_index]
    stretch_end = stretch_starts[longest_stretch_start_index + 1]

    indices = (stretch_start, stretch_end)
    stretch = data.iloc[stretch_start:stretch_end]

    return indices, stretch

def get_longest_missing_data_stretch_length(data, freq):
    data = data.dropna()
    index = data.index

    break_ends = np.argwhere((index[1:] - index[:-1]) != freq).flatten()

    if len(break_ends) == 0:
        return dt.timedelta()

    break_lengths = index[break_ends + 1] - index[break_ends]
    longest_break_length = max(break_lengths) - freq

    return longest_break_length

def test_imputation(data, data_freq, seasonal_freq, imputation_function, imputation_params={}, k=10, error="mape", error_params={}, graph=False, figsize=None, graph_zoom=False):
    stretch_length = int(get_longest_missing_data_stretch_length(data, data_freq) / data_freq)

    if stretch_length == 0:
        return data

    _, data = get_longest_continuous_stretch_of_data(data, data_freq)

    test_indices = np.random.randint(1, data.shape[0] - stretch_length - 1, k)
    errors = []

    if error == "mape":
        error_function = utils.mape
    elif error == "mase":
        error_function = utils.mase
    else:
        raise ValueError("Invalid error type")

    for i in range(k):
        test_index = test_indices[i]
        test_stretch = data.iloc[test_index:test_index + stretch_length]
        current_data = data.drop(data.index[test_index:test_index + stretch_length])

        imputed_data = imputation_function(current_data, data_freq, seasonal_freq, **imputation_params)
        imputed_stretch = imputed_data.iloc[test_index:test_index + stretch_length]
        current_error = error_function(test_stretch, imputed_stretch, **error_params)
        errors.append(current_error)

        if graph:
            plt.figure(figsize=figsize)
            plt.title("{}: {}".format(error, current_error[0]))

            if graph_zoom:
                plt.plot(data[max(0, test_index - stretch_length):min(data.shape[0], test_index + stretch_length + stretch_length)])
            else:
                plt.plot(data)

            plt.plot(imputed_stretch)
            plt.show()

    average_error = sum(errors) / len(errors)

    return average_error, errors
