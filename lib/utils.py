import numpy as np
import pandas as pd

def mse(y, y_hat):
    return np.mean(np.power(y - y_hat, 2))

def rmse(y, y_hat):
    return np.sqrt(mse(y, y_hat))

def mae(y, y_hat):
    return np.mean(np.abs(y - y_hat))

def mape(y, y_hat, replace_zeros=True, epsilon=0.01):
    if replace_zeros:
        y[y == 0] = epsilon

    return np.mean(np.abs(y - y_hat) / y)

#def mape(data, test, replace_zeros=True, epsilon=0.01):
#    if replace_zeros:
#        data[data == 0] = epsilon
#
#    ape = np.sum(np.abs(data - test) / data)
#    return 1 / data.shape[0] * ape

def mase(data, test, seasonal_freq=1):
    s = seasonal_freq
    T = data.shape[0]

    if s >= T:
        raise ValueError("Seasonality {} is larger than data size".format(s, T))

    mae = 1 / (T - s) * np.sum(np.abs(data[s:].values - data[:T-s].values))
    return 1 / T * np.sum(np.abs(data - test)) / mae

def get_standard_errors(y, y_hat, suffix=None):
    suffix = "_" + suffix if suffix else ""

    return {
        "mse" + suffix: mse(y, y_hat),
        "rmse" + suffix: rmse(y, y_hat),
        "mae" + suffix: mae(y, y_hat),
        "mape" + suffix: mape(y, y_hat)
    }

def compare_timedeltas(operation, timedelta1, timedelta2):
    if operation == "==":
        return pd.to_timedelta(timedelta1) == pd.to_timedelta(timedelta2)
    elif operation == "!=":
        return pd.to_timedelta(timedelta1) != pd.to_timedelta(timedelta2)
    elif operation == ">":
        return pd.to_timedelta(timedelta1) > pd.to_timedelta(timedelta2)
    elif operation == "<":
        return pd.to_timedelta(timedelta1) < pd.to_timedelta(timedelta2)
    elif operation == ">=":
        return pd.to_timedelta(timedelta1) >= pd.to_timedelta(timedelta2)
    elif operation == "<=":
        return pd.to_timedelta(timedelta1) <= pd.to_timedelta(timedelta2)
    else:
        raise Exception("Operation {} not recognized".format(operation))

def get_stretches(datetimes, frequency):
    break_indices = np.argwhere(compare_timedeltas("!=", datetimes[1:] - datetimes[:-1], frequency)).flatten() + 1
    stretch_starts = np.concatenate(([0], break_indices))
    stretch_ends = np.concatenate((stretch_starts, [datetimes.shape[0]]))[1:]
    stretches = np.vstack((stretch_starts, stretch_ends)).T

    return stretches

# Flattens a matrix composed of sections of rolling values into one flat array
# The first 2 dimensions of matrix should have the rolling values
def flatten_circulant_like_matrix_by_stretches(matrix, stretches):
    flattened = np.empty((0,) + matrix.shape[2:], dtype=matrix.dtype)
    for start, end in stretches:
        flattened = np.concatenate((flattened, matrix[start:end, 0, ...], matrix[end - 1, 1:, ...]), axis=0)

    return flattened