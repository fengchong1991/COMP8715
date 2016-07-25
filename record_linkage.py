# Python program for general record linkage
#
# ----------------------------------------------------------------------------

import auxiliary
import encode
import stringcmp

import random
import os
import sys2
import time
import gzip
import string
import gc
import shutil

# ============================================================================

class Weights:

  def __init__(self, use_attr_index, blk_attr_index, encoding_methods, comparison_methods): 
    """Constructor. Initialise an index, set common parameters.

       Arguments:
       - use_attr_index        A list of the index numbers of the attributes
                               that are used in the linking.
       - blk_attr_index        A list of the index numbers of the attributes
                               that are used in the blocking.
       - encoding_methods      A list with (blocking) encoding methods, one
                               per blocking attribute (thus, this
                               list needs to be of length equal to the number
       - comparison_methods    A list with comparison methods, one per matching attributes
   """

    self.use_attr_index =   	 use_attr_index
    self.blk_attr_index =  	 blk_attr_index
    self.enco_methods 	=     	 encoding_methods
    self.comp_methods	=	 comparison_methods

    # Define the main data structures to be use

    self.rec_dict 		= [{},{}]  		# To hold the data set loaded from a file. Keys in
                        				# this dictionary are the record identifiers and
                        				# values are the cleaned records (without the
                        				# identifiers)

    self.block_index 		= [{},{}]		# The block index data structure. Keys are the (phonetic) 
                                                	# encoding and values are list of attribute values.

    self.intersection_list_BKVs = []

    self.weight_vectors 	= {}			# To store the weight vectors from records of p1 and p2

  # ---------------------------------------------------------------------------

  def read_database(self, file_name, party_name):
    """Load data set and store in memory as a dictionary with record
       identifiers as keys.
    """

    rec_dict = self.rec_dict  

    # Delete and create an empty directory for each party

    if os.path.exists(party_name):
      shutil.rmtree(party_name)
      os.makedirs(party_name)
    else: 
      os.makedirs(party_name)

    if party_name == 'p1':
      this_rec_dict = rec_dict[0]
      print 'Load data file: %s' % (file_name)
    else:
      this_rec_dict = rec_dict[1]
      print 'Load data file: %s' % (file_name)

    if (file_name.lower().endswith('.gz')):
      in_file =  gzip.open(file_name)  # Open gzipped file
    else:
      in_file =  open(file_name)  # Open normal file

    self.header_line = in_file.readline()  # Skip over header line

    for rec in in_file:
      rec = rec.lower().strip()
      rec = rec.split(',')
      clean_rec = map(string.strip, rec) # Remove all surrounding whitespaces        
        
      rec_id = ''
      rec_id = clean_rec[0]
      assert rec_id not in this_rec_dict, ('Record ID not unique:', rec_id)

      # Save the original record without the record identifier
      #
      this_rec_dict[rec_id] = clean_rec

    print '    Read %d records of %s' % (len(this_rec_dict), party_name)
    #print rec_dict[0]

  # ---------------------------------------------------------------------------

  def build_BI(self, party_name):
    """Build BI data structure to store the BKVs and the 
       corresponding list of record identifiers.
    """

    rec_dict = self.rec_dict  
    block_index = self.block_index
    enco_methods =  self.enco_methods
    blk_attr_index = self.blk_attr_index

    print 'Build Block Index for attributes:', blk_attr_index

    if party_name == 'p1':
      this_rec_dict = rec_dict[0]
      this_block_index = block_index[0]
    else:
      this_rec_dict = rec_dict[1]
      this_block_index = block_index[1]

    st = time.time()

    for (rec_id, clean_rec) in this_rec_dict.iteritems():
      compound_bkv = ""
      if blk_attr_index == None:
        compound_bkv = 'no_block'
      else:
        for attr in blk_attr_index:  # Process selected blocking attributes
          attr_val = clean_rec[attr]
          attr_encode = enco_methods[attr](attr_val)
          compound_bkv += attr_encode
      
      if (compound_bkv in this_block_index): 	 # Block value in index, only add attribute value
        rec_id_list = this_block_index[compound_bkv]
        rec_id_list.append(rec_id)
      else:					 # A new block, add block value and attribute value
        rec_id_list = [rec_id]
        this_block_index[compound_bkv] = rec_id_list

    print '    Generated %d blocks for %s' % (len(this_block_index), party_name)
    print '      Number of records in data set:', len(this_rec_dict)
    print '      Time used:', time.time()-st
    #print block_index

  # ---------------------------------------------------------------------------

  def commonBlocks(self):
    """Identify common blocks
    """

    rec_dict = self.rec_dict  
    block_index = self.block_index

    unique_blocks = set()

    intersection_set = set(block_index[0].keys()).intersection(set(block_index[1].keys())) # common
    unique_block_set = set(block_index[0].keys()).union(set(block_index[1].keys()))        # union

    print '      Number of intersection blocks: %d, number of all unique blocks: %d' % \
            (len(intersection_set), len(unique_block_set))
    print

    self.intersection_list_BKVs = list(intersection_set)

  # ---------------------------------------------------------------------------

  def match(self):
    """perform matching on records of p1 and p2.
    """

    block_index = self.block_index
    rec_dict = self.rec_dict
    intersection_list_BKVs = self.intersection_list_BKVs
    use_attr_index = self.use_attr_index
    comp_methods =  self.comp_methods

    weight_vectors = self.weight_vectors

    out_file_name = 'output.csv'
    out_file = open(out_file_name, 'w')

    for BKV in intersection_list_BKVs:
      p1_rec_list = block_index[0][BKV]
      p2_rec_list = block_index[1][BKV]
      for p1_rec in p1_rec_list:
        for p2_rec in p2_rec_list:
          out_file.write(p1_rec+','+p2_rec)
          p1_rec_vals = rec_dict[0][p1_rec]
          p2_rec_vals = rec_dict[1][p2_rec]
          this_weight_vectors = []
          for attr in use_attr_index:
              sim_val = comp_methods[attr](p1_rec_vals[attr],p2_rec_vals[attr])
              out_file.write(','+str(sim_val))
              this_weight_vectors.append(sim_val)
          weight_vectors[p1_rec+','+p2_rec] = this_weight_vectors
          out_file.write(os.linesep)
    
    out_file.close()
    print self.weight_vectors

  # ---------------------------------------------------------------------------

  def classify(self):
    """Classify weight vectors using SVM.
    """


    

    return

#############################################################

p1_database = './Datasets/Non_corrupted/ncvr_numrec_5000_nocorr_dataset1.csv' #database 1
p2_database = './Datasets/Non_corrupted/ncvr_numrec_5000_nocorr_dataset2.csv' #database 2
block_attr_list = [1,2] #None #sys.argv[3]
comp_attr_list =       [1,2,3,4] #sys.argv[4]

# Two encoding methods for postcode
#
def first3digits(pc):  # Return first 3 digits
  return pc[:3]
def first2digits(pc):  # Return first 2 digits
  return pc[:2]

# The four attributes are: surname, given name, suburb name, postcode
#
encode_methods =    [encode.soundex, encode.soundex, encode.soundex, encode.soundex, first3digits]

comp_methods = [stringcmp.editdist, stringcmp.editdist, stringcmp.editdist, stringcmp.editdist, stringcmp.editdist]

weights = Weights(comp_attr_list, block_attr_list, encode_methods, comp_methods) 

# Step 1: Blocking Phase
#
start_time = time.time()

weights.read_database(p1_database, 'p1')
weights.read_database(p2_database, 'p2')

weights.build_BI('p1')
weights.build_BI('p2')

blocking_phase_time = time.time() - start_time 
blocking_phase_time /= 2

start_time = time.time()

weights.commonBlocks()

blocking_phase_time += (time.time() - start_time)

# Step 2: Matching phase
#
start_time = time.time()

weights.match()

matching_phase_time = time.time() - start_time

# Step 3: Classification phase
#
start_time = time.time()

weights.classify()

classification_phase_time = time.time() - start_time

#Measure how much memory used, then print timing results
#
#memo_usage =     auxiliary.get_memory_usage() 
#memo_usage_val = auxiliary.get_memory_usage_val() / 2

#print memo_usage
#print 'Memory:', memo_usage_val

print
print 'Blocking phase time:   		', blocking_phase_time
print 'Matching phase time:   		', matching_phase_time
print 'Classification phase time:     	', classification_phase_time
tot_time = blocking_phase_time + matching_phase_time + classification_phase_time
print 'Total time:   		               ', tot_time
print

# Write memory and timing results into a log file
#
#logfile_name = 'results_PPRL_AL.log'
#logfile = open(logfile_name, 'a')

#data_set = p1_database
#data_set_name = data_set.split(os.sep)[-1]

#log_str = data_set_name + ',' + attr_str + ',' + block_atr_str +','+ str(min_sim_val) +',' + str(max_sim_val) +','+\
#        '%.4f,%.4f' % \
#       (tot_time,memo_usage_val) #,prec,rec,fsco)

#logfile.write(log_str+os.linesep)
#logfile.close()




    
