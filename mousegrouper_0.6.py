# Mousegrouper 0.5
# 2015-06-15 going to fix a bug in sigdig chop off.
import argparse
import random
import time
import csv
import numpy as np
import sys
import pandas as pd
from scipy import stats
import ggplot

# creates a list of indices that correspond to mouse groups
def group_index_gen(group_sizes):
    group_indices = [0]
    counter = 0
    for i in group_sizes:
        counter += i
        group_indices.append(counter)
    return group_indices

# iterator takes a transposed df, shuffles it, records the order of indices of
# df, the p values, and the mean p value in the a three element list.
# Note, transposed df used because np.random.shuffle only shuffles along first
# index of data frame.
def iterator(df, iter_N, group_indices, n_measure, debug=0):
    t1 = time.time()
    big_table = [[0.,0.,0.] for i in range(iter_N)] #init container
    t2 = time.time()
    for i in range(iter_N):
        if i%5000==0:print(i)
        np.random.shuffle(df)
        big_table[i][0] = [int(i) for i in df[:,0]]
        big_table[i][1], big_table[i][2] = stat_test(df, n_measure, group_indices) #p_values and mean respectively
    t3 = time.time()
    print("Time for: Table Initiation, {0} secs; Stats, {1} secs.".format(t2-t1, t3-t2))
    return big_table

# stat_test does a one way ANOVA along all the measurements, given specific
# group indices
def stat_test(df, n_measure, g_i): # tests vertical groups. g_i = group_indices
    p_values = []
    n_groups = len(group_indices)
    for i in range(1, n_measure+1):
        p_values.append(
                stats.f_oneway(
                    *[df[:,i][g_i[x]:g_i[x+1]] for x in range(n_groups-1)]
                    )[1]) #stat test using group indices
    return p_values, np.mean(p_values)


# System argument parser for filenames etc.
def parse_args(args):
    parser = argparse.ArgumentParser(description='Mousegrouper v0.6')
    parser.add_argument('-d', '--debug', help = 'Debug mode, print values after each iteration.',
                    action = 'store_true')
    parser.add_argument('-c', '--custom_group', help = 'NOT USED Prompt for custom group sizes ', 
                    action ='store_true')
    parser.add_argument('-b','--batch_mode',
                    help = 'Skips time estimation and prompt, use to run batches, collects time data.',
                            action = 'store_true')
    parser.add_argument('filename', help = 'Enter file name of input data file')
    parser.add_argument('groups_file', help = 'Enter file name of group numbers in csv format')
    parser.add_argument('output_filename', help = '(MUST END WITH .xlsx !) Enter file name of output data file')
    parser.add_argument('iterations', help = 'Number of cycles to try. 1 million is a good default')
    return parser.parse_args(args)

# Parse sys.argv, optionally preprovided args for debugging
args = parse_args(sys.argv[1:])
#args = parse_args(['input.csv', 'groups.csv', 'output.xlsx', '10000'])

# Debug mode prints more things for iterator function
if args.debug == True:
        debug = 1 
else:
        debug = 0 
# Setup Data and Groups File.
# Outputs data_table with just table plus indexes as first row,
# the original mouse_IDs and days_IDs.
# also group_sizes.

data_table = pd.read_csv(args.filename)
mouse_IDs = data_table.columns
n_measure = len(data_table.index)
# Convert data_table to an NumPy array for (presumably) faster performance
data_table_array = np.transpose(
                    np.vstack((
                            np.array(range(0,len(mouse_IDs))),
                            np.array(data_table, dtype='f')                            
                            ))
                               )


with open(args.groups_file, 'r') as f:
    group_sizes = list(map(int, next(csv.reader(f, delimiter = ','))))


group_indices = group_index_gen(group_sizes)

assert len(mouse_IDs) % sum(group_sizes) == 0

t1 = time.time()
tested_mice  = iterator(data_table_array, int(args.iterations), group_indices, n_measure)
t2 = time.time()
sorted_table = sorted(tested_mice, key= lambda x: x[2], reverse = True)[0:10]
t3 = time.time()
print("Time for: Iterator: {0} secs. Sorting: {1} secs.".format(t2-t1, t3-t2))
print("Top 10 p values are: ")
for i in range(10):
    print(sorted_table[i][2])
print("Writing output to: {0}".format(args.output_filename))

def create_group_labels(group_sizes):
    l = []    
    for i in range(len(group_sizes)):
        l += ['Group{0}'.format(i+1)]*int(group_sizes[i])
    return l

ordered_df_list = [data_table.iloc[:,i[0]] for i in sorted_table]
ordered_df_list = [pd.concat((i, pd.DataFrame(create_group_labels(group_sizes)).T)) for i in ordered_df_list]

#data_table.iloc[:,sorted_table[0][0]].to_excel(args.output_filename, sheet_name = '01')
with pd.ExcelWriter(args.output_filename) as writer:    
    for i in range(10):
        data_table.iloc[:,sorted_table[i][0]].to_excel(writer, sheet_name = 'Output{0}'.format(i+1))
        

    

