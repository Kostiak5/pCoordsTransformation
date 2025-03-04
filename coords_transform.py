from collections import defaultdict
import csv
import numpy as np
import matplotlib.pyplot as plt 

def calc_similarity(arr1, arr2):
    x_similarity = abs(arr1[0] - arr2[0])
    y_similarity = abs(arr1[1] - arr2[1])
    z_similarity = abs(arr1[2] - arr2[2])
    if x_similarity < 1e-05 and y_similarity < 1e-05:
        return True
    else:
        return False

def calc_box_union(box1, box2):
    always_bigger = True
    diff = 0
    for i in range(3):
        if not (box1[i] > box2[i] and box1[i + 3] < box2[i + 3]):
            always_bigger = False

    if always_bigger == False:
        for i in range(2):
            if box1[i + 3] < (box2[i] - 1e-05) or (box1[i] - 1e-05) > box2[i + 3]:
                return -1
            if abs(box1[i] - box2[i]) > 1e-04 or abs(box1[i + 3] - box2[i + 3]) > 1e-04:
                return -1
            
    for i in range(2):
        diff += abs(box1[i] - box2[i]) + abs(box1[i + 3] - box2[i + 3])
    
    if (abs(box1[2] - box2[2]) > 1 or abs(box1[5] - box2[5]) > 1):
        return -1
    
    return diff 

def resize_minmax(i, j):
    for k in range(3):
        row_min[k][j] = min(row_min[k][j], row_min[k][i])
        row_max[k][j] = max(row_max[k][j], row_max[k][i])
        row_avg[k][j] = (row_avg[k][j] + row_avg[k][i]) / 2
        row_med[k][j] = (row_med[k][j] + row_med[k][i]) / 2


csv_file_name = 'detections_with_real_coordinates.csv'

coords = []
x_row = []
y_row = []
z_row = []
ids = []
file_names = []
class_names_dict = {}
line_num = 0
    
with open(csv_file_name, mode ='r')as file:
  csv_file = csv.reader(file)
  for line in csv_file:
        if line_num == 0:
            line_num += 1
            continue
        file_names.append(line[0])
        ids.append(line[1])
        class_names_dict[line[1]] = line[2]
        line = [float(x) for x in line[7:] if x]
        if len(line) > 0:
            x_row.append(line[0::3])
            y_row.append(line[1::3])
            z_row.append(line[2::3])
        else:
            x_row.append([0])
            y_row.append([0])
            z_row.append([0])
        line_num += 1

ids = np.array(ids)

row_max = [[np.max(coords_row) for coords_row in x_row], [np.max(coords_row) for coords_row in y_row], [np.max(coords_row) for coords_row in z_row]]
row_min = [[np.min(coords_row) for coords_row in x_row], [np.min(coords_row) for coords_row in y_row], [np.min(coords_row) for coords_row in z_row]]

row_avg = [[np.average(coords_row) for coords_row in x_row], [np.average(coords_row) for coords_row in y_row], [np.average(coords_row) for coords_row in z_row]]
row_med = [[np.median(coords_row) for coords_row in x_row], [np.median(coords_row) for coords_row in y_row], [np.median(coords_row) for coords_row in z_row]]

class_dict = defaultdict(list)
sign_class_ids = {}
sign_nums = defaultdict(list)

sign_num = 0

for i in range(len(ids)):
    mn_diff = 1e-03
    mn_index = -1
    first_time = True
    if ids[i] in class_dict.keys():
        # if there already is sign of the same class_id, maybe we already calculated it in a different image
        for j in range(len(class_dict[ids[i]])):
            other_i = class_dict[ids[i]][j][1]
            other_sign_num = class_dict[ids[i]][j][0]

            new_avg_tuple = (row_avg[0][i], row_avg[1][i], row_avg[2][i])
            other_avg_tuple = (row_avg[0][other_i], row_avg[1][other_i], row_avg[2][other_i])
            avg_similar = calc_similarity(new_avg_tuple, other_avg_tuple)
            
            new_med_tuple = (row_med[0][i], row_med[1][i], row_med[2][i])
            other_med_tuple = (row_med[0][other_i], row_med[1][other_i], row_med[2][other_i])
            med_similar = calc_similarity(new_med_tuple, other_med_tuple)

            new_box = (row_min[0][i], row_min[1][i], row_min[2][i], row_max[0][i], row_max[1][i], row_max[2][i])
            other_box = (row_min[0][other_i], row_min[1][other_i], row_min[2][other_i], row_max[0][other_i], row_max[1][other_i], row_max[2][other_i])
            box_union = calc_box_union(new_box, other_box)
            
            if box_union != -1:
                # we already calculated the same sign in a different image => instead of adding a new sign to dictionary, we add it to set of imgs belonging to the same sign
                if first_time == True:
                    sign_nums[other_sign_num].append(i)
                    first_time = False
                mn_diff = 2
                mn_index = j
                #resize_minmax(i, other_i)
    if mn_diff == 1e-03:
        # if there is need to create a new sign id
        class_dict[ids[i]].append([sign_num, i])
        sign_class_ids[sign_num] = ids[i]
        sign_nums[sign_num].append(i)
        sign_num += 1

just_copies = [False] * len(sign_nums)
sign_nums_union = [0] * len(sign_nums)
print(sign_nums)
for i in range(len(sign_nums) - 1, 0, -1):
    i_id = sign_nums[i][0]
    mn_diff = 1e-03
    mn_index = -1
    first_time = True
    for j in range(i, -1, -1):
        j_id = sign_nums[j][0]
        if sign_class_ids[i] == sign_class_ids[j] and i != j:
            other_box = (row_min[0][i_id], row_min[1][i_id], row_min[2][i_id], row_max[0][i_id], row_max[1][i_id], row_max[2][i_id])
            new_box = (row_min[0][j_id], row_min[1][j_id], row_min[2][j_id], row_max[0][j_id], row_max[1][j_id], row_max[2][j_id])
            
           
            
            box_union = calc_box_union(new_box, other_box)
            if box_union != -1:
                print((i_id, j_id), first_time)
                if first_time == True:
                    mn_diff = box_union
                    mn_index = j
                    first_time = False
                    sign_nums[mn_index].extend(sign_nums[i])
                    just_copies[i] = True
                #resize_minmax(i_id, j_id)

print(sign_nums)
        
"""
for i in range(len(sign_nums)):
    if just_copies[i] == False:
        print(i)
        print(ids[sign_nums[i][0]])
        for y in sign_nums[i]:
            print(f"{file_names[y]} {(row_min[0][y], row_min[1][y], row_min[2][y], row_max[0][y], row_max[1][y], row_max[2][y])} {(row_med[0][y], row_med[1][y], row_med[2][y])}")
"""
xs = []
ys = []
zs = []
cs = []
color_id = 1
sign_avgs = []
for i in range(len(sign_nums)):
    if just_copies[i] == False:
        this_sign_avg = [0] * 3
        for sign in sign_nums[i]:
            for coord in range(3):
                this_sign_avg[coord] += row_avg[coord][sign]
        for coord in range(3):
            this_sign_avg[coord] /= len(sign_nums[i])
        sign_avgs.append(this_sign_avg)

#COMPARE SIGN AVGS, FIND CLUSTERS OF CLOSEST

with open('sign_coordinates.csv', 'w', newline='') as file:
    csv_file = csv.writer(file, delimiter=';')
    csv_file.writerow(['sign_group', 'file_name', 'class_id', 'class_name', 'sign_center_x', 'sign_center_y', 'sign_center_z', 'sign_center_x', 'sign_center_y', 'sign_center_z', 'file_count'])
    for i in range(len(sign_nums)):   
        if just_copies[i] == False:
            for x in sign_nums[i]:
                csv_file.writerow([i, file_names[x], sign_class_ids[i], class_names_dict[sign_class_ids[i]], row_min[0][x], row_min[1][x], row_min[2][x], row_max[0][x], row_max[1][x], row_max[2][x], len(sign_nums[i])])
                if sign_class_ids[i] == '29' and row_avg[0][x] != 0:
                    xs.append(row_avg[0][x])
                    ys.append(row_avg[1][x])
                    zs.append(row_avg[2][x])   
                    cs.append((0.01 * (color_id % 100),0.3  * (color_id % 3),0.1 * (color_id % 10)))
            if sign_class_ids[i] == '29':
                color_id += 1
            #for sign_id in sign_nums[i]:
            #csv_file.writerow([i, file_names[sign_id], sign_class_ids[i], class_names_dict[sign_class_ids[i]], this_sign_avg[0], this_sign_avg[1], this_sign_avg[2], len(sign_nums[i])])
fig = plt.figure()
ax = plt.axes(projection='3d')
ax.scatter(xs, ys, zs, color=cs, s = 157, linewidths=0)
plt.show()
#print(sign_class_ids['21'])
#print(group_ids['21'])

#print(class_dict)

