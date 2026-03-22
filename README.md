# Spatial Detection Clustering & 3D Visualizer

A utility for processing, clustering, and visualizing 3D object detections from CSV data. This tool identifies when multiple detections across different frames refer to the same physical object based on coordinate proximity and bounding box overlaps.

Used to transform given local coordinates of road signs on different photos to a global coordinate system and then match the same road signs found on different photos.

## Features

* **Spatial Clustering**: Groups detections of the same class that share nearly identical 3D coordinates (X, Y, Z).
* **Bounding Box Union Logic**: Merges overlapping detection boxes to handle "duplicate" objects seen from different angles or timestamps.
* **Statistical Analysis**: Calculates Min, Max, Average, and Median coordinates for every detection group.
* **CSV Data Pipeline**: 
    * **Input**: Reads `detections_with_real_coordinates.csv`.
    * **Output**: Generates `sign_coordinates.csv` containing grouped data, class names, and file counts per group.
* **3D Visualization**: Built-in Matplotlib engine to scatter-plot detection clusters in 3D space with distinct color coding for different groups.

## Requirements

* Python 3.x
* NumPy
* Matplotlib

Install dependencies via pip:

    pip install numpy matplotlib

## Usage

1.  **Prepare your data**: Ensure you have a file named `detections_with_real_coordinates.csv` in the root directory. The script expects:
    * Column 0: File Name
    * Column 1: Class ID
    * Column 2: Class Name
    * Column 7+: Coordinate triplets (X, Y, Z).

2.  **Run the script**:
    python coords_transform.py

3.  **Output**:
    * A 3D plot will open showing the spatial clusters (specifically filtered for Class ID '29' in the default visualization).
    * A new file `sign_coordinates.csv` will be created with categorized group data.

## Logic Overview

| Function | Purpose |
| :--- | :--- |
| calc_similarity | Checks if two coordinate arrays are within a 1e-05 tolerance. |
| calc_box_union | Determines if two 3D bounding boxes overlap or if one is contained within the other. |
| resize_minmax | Dynamically updates the boundaries of a cluster as new detections are added. |

## Data Mapping

The script maps raw detections into a `sign_group`. If a detection in frame B is spatially similar to one in frame A, they are assigned the same group ID, allowing you to track unique objects across an entire dataset.
