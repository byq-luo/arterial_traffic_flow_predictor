# Arterial Traffic Flow Prediction

This repository contains all of the code that I have been using for my research.

All commands must be run from the top-level Code directory.

    # Command to generate distances and adjacency matrix
    python3 scripts/generate_graph_connections.py --plan_name P2 --dl 508302 508306 508201 508205 509101 509105 507202 507206 608101 608105 608104 608107 --adjacency_matrix_path test
    python3 DCRNN/scripts/gen_adj_mx.py --sensor_ids_filename data/inputs/model/sensors_advanced_5083.txt --distances data/inputs/model/distances_5083_P1.csv --output_pkl_filename data/inputs/model/adjacency_matrix_5083_P1.pkl

    # Command to run the training data generation script
    python3 scripts/generate_training_data.py --intersection 5083 --plan_name P2 --output_dir data/inputs -v
    python3 scripts/generate_training_data.py --intersection 5083 --plan_name P2 --x_offset 12 --y_offset 3 --output_dir data/inputs --timestamps_dir data/inputs -v
    python3 scripts/generate_training_data.py --intersection 5083 --plan_name P2 --x_offset 24 --y_offset 6 --start_time_buffer 24 --output_dir data/inputs --timestamps_dir data/inputs -v
    python3 scripts/generate_training_data.py --intersection 5083 --plan_name P2 --x_offset 3 --y_offset 6 --output_dir data/inputs --timestamps_dir data/inputs --timeseries -v

    # Command to run all models to have errors in a central location
    python3 model_runner.py config/model_runner_config.yaml -vv
    python3 experiment_runner.py config/experiment_runner_config.yaml -vv

    # Command to run DCRNN for sensor 5083
    python3 DCRNN/dcrnn_train.py --config_filename data/5083/5083.yaml | tee data/5083/5083.out

    # Command to get predictions
    python3 DCRNN/run_demo.py --config_filename data/5083/dcrnn_DR_2_h_12_64-64_lr_0.01_bs_64_0918120854/config_92.yaml --output_filename data/5083/predictions.npz

    # Command to plot predictions
    python3 DCRNN/scripts/graph_predictions.py data/5083/predictions.npz data/inputs/5083_sensor_data/test.npz
    
    # Command to get predictions metrics
    python3 scripts/experiment_metrics.py experiments/full-information_20200114-123958/ -d 508302 508306
    python3 scripts/predictions_metrics.py -d 508302 508306 --dl experiments/full-information_20200114-123958/inputs/model/detector_list.txt --h 1 --h 3 --h 6 --round 2 experiments/full-information_20200114-123958/experiments/dcrnn/

### Notes to self about DCRNN

- Validation loss is used for early stopping regularization
- `self._test_model` uses the variables from `self._train_model` because they share the same variable scope
- The constant shifting exhibited in the data is a property of the data; it's graphed correctly, at least

### Bug fixes

- `metrics.py:88`: In the function `masked_mape_np`, I added an epsilon to prevent blowup of MAPE
- `utils.py:178`: In `load_dataset`, change time to be first dimension and data to be in other dimensions. Update `dcrnn_supervisor.py` and `generate_training_data.py` as well.
- `dcrnn_model:39`: Changed labels shape from `input_dim` to `output_dim`
- `dcrnn_cell:103`: Changed to `(1 - u) * state + u * c` due to personal preferences
- `dcrnn_cell:165`: The whole for loop is really weird. I think that there was some sort of math error here, since the terms didn't add up and didn't follow the diffusion convolution presented in the paper. However, it looks like because `max_diffusion_step` is 2, that in the end the only differences were with scaling factors. To be safe, I changed it so that there is just 1 diffusion term for each step for each support; this increased the errors by almost 0.1, but that could easily just be random variation.
- Bootstrap in `DataLoader` if `shuffle` is `True`
- `dcrnn_model:48-49`: Used the same cell * `num_layers`, so changed to a list comprehension to use different cells inside the stacked cell; then reverted this, as it looks like RNNCells do not keep any meaningful state since state is passed into the `__call__` function
- `dcrnn_model:49`: It looks like the decoding cell is the same cell as the encoding cell, which may not perform as well, according to Sutskever's paper; however, changing this didn't help, for the same reason why `cell * num_layers` wasn't a problem

### Confusions/Weird things

- Change DCRNN so that it predicts with the shape `(num_data, offsets, num_detectors, num_dimensions)` and that time is not included in the output

### TODO

- Automatic exclusion of sensors that are too unhealthy (get health for each sensor for time period and remove max in loop until adequate)
- Verbosity in experiment_runner.py
- Predictions on dummy data that is linear
- Flow and occupancy and flow / occupancy
- Visualization library
