from sklearn.datasets import make_blobs
from sklearn.preprocessing import StandardScaler
import matplotlib.pyplot as plt
import numpy as np
from sklearn import metrics
from sklearn.cluster import DBSCAN
import csv
import copy
from collections import defaultdict
from scipy import stats as st

def mpl_visualize(): 
    # tool to visualize results in matplotlib 
    unique_labels = set(labels)
    core_samples_mask = np.zeros_like(labels, dtype=bool)
    core_samples_mask[db.core_sample_indices_] = True

    ax = plt.axes()

    colors = [plt.cm.Spectral(each) for each in np.linspace(0, 1, len(unique_labels))]
    for k, col in zip(unique_labels, colors):
        if k == -1:
            # black = noise
            col = [0, 0, 0, 1]

        class_member_mask = labels == k

        xy = X[class_member_mask & core_samples_mask]
        ax.scatter(xy[:, 0], xy[:, 1], color=tuple(col), s=14)
        xy = X[class_member_mask & ~core_samples_mask]
        ax.scatter(xy[:, 0], xy[:, 1], color=tuple(col), s=6)

    plt.show()

    print("Estimated number of clusters: %d" % cluster_count)
    print("Estimated number of noise points: %d" % noise_count)

def find_cluster(id, pt_i):
    # try to find possible cluster for the signs than were labeled as noise
    possible_cluster = -1
    mode = -1

    for i in range(len(clusters_x[id])):
        if clusters_x[id][i][0] < x_avgs[id][pt_i] and clusters_x[id][i][2] > x_avgs[id][pt_i] and clusters_y[id][i][0] < y_avgs[id][pt_i] and clusters_y[id][i][2] > y_avgs[id][pt_i]:
            # if label's avg/median is inside of this cluster's limits => assign it to this cluster
            possible_cluster = i
            break
    
        elif (abs(clusters_x[id][i][0] - x_avgs[id][pt_i]) < 2e-04 or abs(clusters_x[id][i][2] - x_avgs[id][pt_i]) < 2e-04) and clusters_y[id][i][0] < y_avgs[id][pt_i] and clusters_y[id][i][2] > y_avgs[id][pt_i]:
            # if label's median is close to x coord borders and is inside y coord borders of this cluster
            possible_cluster = i
            mode = 1
        
        elif clusters_x[id][i][0] < x_avgs[id][pt_i] and clusters_x[id][i][2] > x_avgs[id][pt_i] and (abs(clusters_y[id][i][0] - y_avgs[id][pt_i]) < 2e-04 or abs(clusters_y[id][i][2] - y_avgs[id][pt_i]) < 2e-04):
            # if label's median is close to y coord borders and is inside x coord borders of this cluster
            possible_cluster = i
            mode = 1

        elif abs(clusters_x[id][i][1] - x_avgs[id][pt_i]) < 2e-04 and abs(clusters_y[id][i][1] - y_avgs[id][pt_i]) < 2e-04:
            # if distance between the cluster's median and this coord is adequately small
            if mode != 1:
                possible_cluster = i
                mode = 0
 
    return possible_cluster

def optimal_cluster_choice(cluster_count, line, labels):
    # try to find an optimal cluster in the single sign's coords
    cl_avg_x = [[0] for i in range(cluster_count)]
    cl_avg_y = [[0] for i in range(cluster_count)]
    cl_avg_z = [[0] for i in range(cluster_count)]
    cl_min = [[1E9, 1E9, 1E9] for i in range(cluster_count)]
    cl_max = [[0, 0, 0] for i in range(cluster_count)] 
    min_area = 1E9
    min_in = -1
    this_area = 0

    print(cluster_count)
    for i in range(0, int(len(line) / 3)):
        if labels[i] != -1:
            this_cl = labels[i]
            cl_avg_x[this_cl].append(line[i * 3])
            cl_avg_y[this_cl].append(line[i * 3 + 1])
            cl_avg_z[this_cl].append(line[i * 3 + 2]) # append coords of pts inside the cluster
            for j in range(3):
                cl_min[this_cl][j] = min(cl_min[this_cl][j], line[i * 3 + j])
                cl_max[this_cl][j] = max(cl_max[this_cl][j], line[i * 3 + j]) # search for the borders of the cluster

    for i in range(cluster_count):
        this_area = (cl_max[i][0] - cl_min[i][0]) * (cl_max[i][1] - cl_min[i][1])
        print(f"len {len(cl_avg_x[i])}")
        if this_area < min_area and len(cl_avg_x[i]) > 35 and this_area != 0.0: # optimal cluster: minimal area, more than 35 pts
            print(f" len {len(cl_avg_x[i])}")
            min_in = i
            min_area = this_area
        print(min_in)
    if min_in == -1: # if no cluster meets the optimal cluster criteria => just choose the one with the most points 
        min_in = 0
        for i in range(cluster_count):
            if len(cl_avg_x[i]) > len(cl_avg_x[min_in]):
                min_in = i

    """
    xs = []
    ys = []
    colors = []
    
    if file_name == 'lens_fixed2-001312.jpg' and class_id == 29: # visualization tool
        for i in range(cluster_count):
            xs.append(cl_min[i][0])
            ys.append(cl_min[i][1])
            colors.append([1, 0, 0])
            xs.append(cl_max[i][0])
            ys.append(cl_max[i][1])
            colors.append([0,0,1])
            for j in range(1, len(cl_avg_x[i])):
                xs.append(cl_avg_x[i][j])
                ys.append(cl_avg_y[i][j])
                colors.append([0,1,0])
            xs.extend([cl_max[this_cl][0], cl_min[this_cl][0]])
            ys.extend([cl_max[this_cl][1], cl_min[this_cl][1]])
            colors.extend([[0,1,1], [0,1,1]])
    
        plt.scatter(xs, ys, color=colors)
        plt.show()
    """

    return min_in
    
    
    


def find_deviations(line, class_id):
    # try to find pts far from the median
    x_med = np.median(line[0::3])
    y_med = np.median(line[1::3])
    z_med = np.median(line[2::3])
    deviations = 0
    for i in range(0, len(line), 3):
        if abs(line[i] - x_med) > 2e-05 or abs(line[i+1] - y_med) > 2e-05:
            deviations += 1 # find pts far away from the median value (indication that there are more clusters)

    if deviations > (len(line) / 3) / 4: # if more than quarter of all the pts is too far => maybe there is more than 1 cluster
        LINE_X = [[line[i], line[i + 1]] for i in range(0, len(line), 3)]
        LINE_X = StandardScaler().fit_transform(LINE_X)
        db_line = DBSCAN(eps=0.3, min_samples=20).fit(LINE_X) # perform clustering
        labels_line = db_line.labels_
        
        cluster_count = len(set(labels_line)) - (1 if -1 in labels_line else 0)
        if cluster_count > 0:
            cl_in = optimal_cluster_choice(cluster_count, line, labels_line) # find the optimal cluster among available
            print(cl_in)
            x_avg = []
            y_avg = []
            z_avg = []
            for i in range(len(labels_line)):
                if labels_line[i] == cl_in:
                    x_avg.append(line[i * 3])
                    y_avg.append(line[i * 3 + 1])
                    z_avg.append(line[i * 3 + 2])
            x_avgs[class_id].append(np.median(x_avg))
            y_avgs[class_id].append(np.median(y_avg))
            z_avgs[class_id].append(np.median(z_avg))
            line_avgs.append((np.median(x_avg), np.median(y_avg), np.median(z_avg), file_name))
            return

    x_avgs[class_id].append(x_med)
    y_avgs[class_id].append(y_med)
    z_avgs[class_id].append(z_med)
    line_avgs.append((x_med, y_med, z_med, file_name))
    return 

def find_deviations_new(line, class_id):
    z_med_sample_arr = np.round(line[2::3][int(len(line) / 3 / 5 * 2) : int(len(line) / 3 / 5 * 3)], 2)
    z_med_sample = np.median(z_med_sample_arr)
    x_arr = []
    y_arr = []
    z_arr = []
    fit_coord_count = 0
    for i in range(0, len(line), 3):
        if abs(line[i + 2] - z_med_sample) < 0.5:
            x_arr.append(line[i])
            y_arr.append(line[i + 1])
            z_arr.append(line[i + 2])
            fit_coord_count += 1


    
    if len(x_arr) == 0:
        print(z_med_sample_arr)
        print(file_name)
        print(line[2::3])
    
    if fit_coord_count > 30:
        x_med = np.median(x_arr)
        y_med = np.median(y_arr)
        z_med = np.median(z_arr)

        x_avgs[class_id].append(x_med)
        y_avgs[class_id].append(y_med)
        z_avgs[class_id].append(z_med)
        line_avgs.append((x_med, y_med, z_med, file_name))
        return 1
    else:
        return 0

def divide_into_clusters():
    # clustering algorithm
    if len(x_avgs[class_id]) > 50: # use full and more exact clustering in case there are enough samples
        db = DBSCAN(eps=0.1, min_samples=5).fit(X)
        labels = db.labels_
    elif len(x_avgs[class_id]) > 20:
        db = DBSCAN(eps=0.2, min_samples=int(len(x_avgs[class_id]) / 5)).fit(X)
        labels = db.labels_
    elif len(x_avgs[class_id]) > 5:
        db = DBSCAN(eps=0.5, min_samples=1).fit(X)
        labels = db.labels_
    else:
        db = None # if group of signs is too small to perform automatic clustering => perform it manually
        labels = [0] * len(x_avgs[class_id])
        non_cl_num = 0 
        cl_num = 10
        for i in range(len(x_avgs[class_id])):
            if labels[i] < 10:
                cl_found = False
            else:
                cl_found = True
            for j in range(i + 1, len(x_avgs[class_id])):
                if ((x_avgs[class_id][i] - x_avgs[class_id][j])**2 + (y_avgs[class_id][i] - y_avgs[class_id][j])**2)**0.5 < 1e-04: # if distance between two coords is small => assign them to one cluster
                    cl_found = True
                    if labels[i] >= 10: # if this (i) sign already is in a cluster => assign new (j) sign to the same cluster
                        labels[j] = labels[i]  
                    else:
                        labels[i] = cl_num
                        labels[j] = cl_num
                        cl_num += 1 # increment number for eventual new cluster
            if cl_found == False:
                labels[i] = non_cl_num
                non_cl_num += 1 # increment number for eventual new sign without cluster
    
    return (db, labels)
    
csv_file_name = 'detections_with_real_coordinates.csv'

x_avgs = defaultdict(list) # to store median/avg for every sign on every photo
y_avgs = defaultdict(list)
z_avgs = defaultdict(list)
row_nums = defaultdict(list)
row_num = 0
line_avgs = []
class_names = {}
first_line = False
with open(csv_file_name, mode ='r')as file:
  csv_file = csv.reader(file)
  for line in csv_file:
        if first_line == False: # skip the header row
            first_line = True
            continue
        file_name = line[0]
        id = int(line[1])
        class_names[id] = line[2]
        sign_area = float(line[5]) * float(line[6])
        line = [float(x) for x in line[7:] if x]
        if len(line) > 0 and sign_area >= 5e-05: # if there are any coords for the sign 
            #find_deviations(line, id)
            if find_deviations_new(line, id) == 1:
                row_nums[id].append(row_num) # add number of the row to access further coord infos (will be useful later in case this sign doesn't match any signs on the other photos)
                row_num += 1

clusters_x = defaultdict(list)
clusters_y = defaultdict(list)
clusters_z = defaultdict(list)
clusters_row_nums = defaultdict(list)

for class_id in x_avgs.keys(): 
    X = []
    for i in range(len(x_avgs[class_id])):
        X.append([x_avgs[class_id][i], y_avgs[class_id][i]]) # add into this array - to be used for the clustering algorithm 
        # (could be further optimized)

    X = StandardScaler().fit_transform(X)

    db, labels = divide_into_clusters()

    cluster_count = len(set(labels)) - (1 if -1 in labels else 0) # num of clusters (noise excluded)
    noise_count = list(labels).count(-1)

    cluster_labels = copy.deepcopy(labels)
    cluster_dict_x = defaultdict(list)
    cluster_dict_y = defaultdict(list)
    cluster_dict_z = defaultdict(list)
    cluster_ln = defaultdict(list)

    for i in range(len(cluster_labels)):
        if cluster_labels[i] != -1:
            cluster_dict_x[cluster_labels[i] + 1].append(x_avgs[class_id][i]) # assign signs (their avgs/medians/info) to their clusters
            cluster_dict_y[cluster_labels[i] + 1].append(y_avgs[class_id][i])
            cluster_dict_z[cluster_labels[i] + 1].append(z_avgs[class_id][i])
            cluster_ln[cluster_labels[i] + 1].append(row_nums[class_id][i])
    
    
    for i in cluster_dict_x.keys():
        clusters_x[class_id].append((np.min(cluster_dict_x[i]), np.median(cluster_dict_x[i]), np.max(cluster_dict_x[i]))) # min/median/max coordinate of every cluster
        clusters_y[class_id].append((np.min(cluster_dict_y[i]), np.median(cluster_dict_y[i]), np.max(cluster_dict_y[i])))
        clusters_z[class_id].append((np.min(cluster_dict_z[i]), np.median(cluster_dict_z[i]), np.max(cluster_dict_z[i])))

        clusters_row_nums[class_id].append(cluster_ln[i])
    
    clusters_row_nums[class_id].append([])
    for i in range(len(cluster_labels)):  # try to assign previously unassigned labels to their clusters
        """
        if cluster_labels[i] == -1:
            labels[i] = find_cluster(class_id, i)
            if labels[i] == -1:
                clusters_row_nums[class_id][-1].append(row_nums[class_id][i]) # if cluster not found => label as -1
            else:
                clusters_row_nums[class_id][labels[i]].append(row_nums[class_id][i])
        else:
        """
        labels[i] = cluster_labels[i]
        if labels[i] == -1:
            clusters_row_nums[class_id][-1].append(row_nums[class_id][i]) # if cluster not found => label as -1

    if class_id == 21:
        mpl_visualize() # can be activated to visualize coords with matplotlib

with open('sign_coordinates.csv', 'w', newline='') as file:
    csv_file = csv.writer(file, delimiter=';')
    csv_file.writerow([ 'file_name', 'class_id', 'class_name', 'sign_id', 'sign_center_x', 'sign_center_y', 'sign_center_z', 'width_x', 'height_y', 'depth_z'])
    for class_id in x_avgs.keys():
        for sign_id in range(len(clusters_row_nums[class_id])):
            for sign in clusters_row_nums[class_id][sign_id]:
                if sign_id == len(clusters_row_nums[class_id]) - 1: # = if sign_id equals to -1 (=this sign didn't find its cluster/group)
                    sign_id_str = str(class_id) + "|X"
                    center_x = line_avgs[sign][0] # use median/avg coords of the sign only on that photo
                    center_y = line_avgs[sign][1]
                    center_z = line_avgs[sign][2]
                    width = 0 # leave w/h/d as 0 to indicate error, as this sign most probably belongs to a cluster (probably a mistake in original coordinates determination)
                    height = 0
                    depth = 0
                else:
                    sign_id_str = str(class_id) + "|" + str(sign_id)
                    center_x = clusters_x[class_id][sign_id][1] # center pt equals to median/avg of its cluster/group
                    center_y = clusters_y[class_id][sign_id][1]
                    center_z = clusters_z[class_id][sign_id][1]
                    width = clusters_x[class_id][sign_id][2] - clusters_x[class_id][sign_id][0] # w/h/d equals to difference between the min. and max. coord in this direction in the cluster/group
                    height = clusters_y[class_id][sign_id][2] - clusters_y[class_id][sign_id][0]
                    depth = clusters_z[class_id][sign_id][2] - clusters_z[class_id][sign_id][0]
                csv_file.writerow([line_avgs[sign][-1], class_id, class_names[class_id], sign_id_str, center_x, center_y, center_z, width, height, depth])
