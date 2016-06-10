# Mousegrouper 0.5
# 2015-06-15 going to fix a bug in sigdig chop off.
import argparse

parser = argparse.ArgumentParser(description='Mousegrouper v0.3')
parser.add_argument('-d', '--debug', help = 'Debug mode, print values after each iteration.',
                action = 'store_true')
parser.add_argument('-c', '--custom_group', help = 'NOT USED Prompt for custom group sizes ', 
                action ='store_true')
parser.add_argument('-b','--batch_mode',
                help = 'Skips time estimation and prompt, use to run batches, collects time data.',
                        action = 'store_true')
parser.add_argument('filename', help = 'Enter file name of input data file')
parser.add_argument('groups_file', help = 'Enter file name of group numbers in csv format')
parser.add_argument('output_filename', help = 'Enter file name of output data file')
parser.add_argument('iterations', help = 'Number of cycles to try')
args = parser.parse_args()

if args.debug == True:
        debug = 1 
else:
        debug = 0 


import random
import time
import csv
import numpy as np
from scipy import stats

#arguments

infilename = args.filename
iter_N = int(args.iterations)
groups_file = args.groups_file
outfilename = args.output_filename

# Setup Data and Groups File.
# Outputs data_table with just table plus indexes as first row,
# the original mouse_IDs and days_IDs.
# also group_sizes.
with open(infilename, 'r') as f:
    data_table = np.genfromtxt(infilename, delimiter=',', dtype='string')
    mouse_IDs = data_table[0,1:]
    days_IDs = data_table[:,0]
    n_measure = len(days_IDs)-1
    data_table = data_table[1:,1:].astype('float')
    # add "indexing row" so can I figure out scrambling later
    data_table = np.vstack((np.array(range(0,len(mouse_IDs))),data_table )) 
    data_table_TP = np.array(data_table.T) #Transposes data_table for np.random.shuffle convenience
    # need to np.array the transpose to override aliasing

#print(data_table_TP)

with open(groups_file, 'r') as f:
    group_sizes = map(int, next(csv.reader(f, delimiter = ',')))

def group_index_gen(group_sizes):
    group_indices = [0]
    counter = 0
    for i in group_sizes:
        counter += i
        group_indices.append(counter)
    return group_indices

group_indices = group_index_gen(group_sizes)

assert len(mouse_IDs) % sum(group_sizes) == 0

def iterator(df, iter_N, group_indices, n_measure, debug=0): # use a transposed df! note in place shuffle of df
    t1 = time.time()
    big_table = [[0.,0.,0.] for i in range(iter_N)] # init container
    t2 = time.time()
    for i in range(iter_N):
        if i%5000==0:print i
        np.random.shuffle(df)
        big_table[i][0] = tuple(df[:,0])
        p_values, mean = stat_test(df, n_measure, group_indices) 
        big_table[i][1] = p_values
        big_table[i][2] = mean
    t3 = time.time()
    print("Time for: Table Initiation, {0} secs; Stats, {1} secs.".format(t2-t1, t3-t2))
    return big_table

def stat_test(df, n_measure, g_i): # tests vertical groups. g_i = group_indices
    p_values = []
    n_groups = len(group_indices)
    for i in range(1, n_measure+1):
        #print i
        p_values.append(
                stats.f_oneway(
                    *[df[:,i][g_i[x]:g_i[x+1]] for x in range(n_groups-1)]
                    )[1])
        #print p_values
    return p_values, np.mean(p_values)

t1 = time.time()
tested_mice  = iterator(data_table_TP, iter_N, group_indices, n_measure)
t2 = time.time()
sorted_table = sorted(tested_mice, key= lambda x: x[2], reverse = True)[0:10]
t3 = time.time()
print("Time for: Iterator: {0} secs. Sorting: {1} secs.".format(t2-t1, t3-t2))
print("Top 10 p values are: ")
for i in range(10):
    print(sorted_table[i][2])
print("Writing output to: {0}".format(outfilename))

# Takes a tuple of mouse indices, calls data_table according to indices by col
def mouse_data_output_cleanup(df, mouse_indices, mouse_IDs, days_IDs):
    print("DF following")
    print(df)
    ordered_df = df[:,mouse_indices]
    print("ordered_df following")
    print(ordered_df)
    ordered_mouse_IDs = [mouse_IDs[i] for i in mouse_indices]
    vertical_days_IDs = np.array([[i] for i in days_IDs])
    print ordered_df.shape
    ordered_df = np.vstack((ordered_mouse_IDs, ordered_df))
    print("Vstacked ordered df following")
    print(ordered_df)
    return ordered_df

print sorted_table[0][0]
#print("data_table following")
#print(data_table)
#test = mouse_data_output_cleanup(data_table, sorted_table[0][0], mouse_IDs, days_IDs)
#print test
np.savetxt(outfilename, sorted_table[0][0], delimiter = ',', fmt='%9s')

