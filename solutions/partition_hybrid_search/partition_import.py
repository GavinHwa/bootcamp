# import face_recognition
import os
import time
from milvus import *
import numpy as np
import random
from faker import Faker

fake = Faker()
milvus = Milvus()

milvus_collection = 'partition_query'

FILE_PATH = '/data/workspace/milvus_data/sift_data/bigann_base.bvecs'

VEC_NUM = 1000000
BASE_LEN = 100000
NUM = VEC_NUM // BASE_LEN

VEC_DIM = 128

SERVER_ADDR = "0.0.0.0"
SERVER_PORT = 19534


def load_bvecs_data(fname,base_len,idx):
    begin_num = base_len * idx
    # print(fname, ": ", begin_num )
    x = np.memmap(fname, dtype='uint8', mode='r')
    d = x[:4].view('int32')[0]
    data =  x.reshape(-1, d + 4)[begin_num:(begin_num+base_len), 4:]   
    data = (data + 0.5) / 255
    data = data.tolist()
    return data


def handle_status(status):
    if status.code != Status.SUCCESS:
        print(status)
        sys.exit(2)


def connect_milvus_server():
    print("connect to milvus")
    status =  milvus.connect(host=SERVER_ADDR, port=SERVER_PORT,timeout = 1000 * 1000 * 20 )
    handle_status(status=status)
    return status


def create_milvus_collection():
    if not milvus.has_collection(milvus_collection)[1]:
        param = {
            'collection_name': milvus_collection,
            'dimension': VEC_DIM,
            'index_file_size':1024,
            'metric_type':MetricType.L2
        }
        status = milvus.create_collection(param)
        print(status)
        build_collection()


def build_collection():
    index_param = { 'nlist': 16384}
    status = milvus.create_index(milvus_collection, 'index_type':IndexType.IVF_SQ8H, index_param)
    print(status)


def create_partition(partition_name,partition_tag):
    milvus.create_partition(milvus_collection, partition_name=partition_name, partition_tag=partition_tag)


def get_partition_tag():
    partition_tag=[]
    partition_name = []
    count = 0
    while count<NUM:
        sex = random.choice(['female','male'])
        get_time = fake.date_between(start_date="-30d", end_date="today")
        is_glasses = random.choice(['True','False'])
        p_tag = str(get_time) + "/" + sex + "/" + str(is_glasses)
        p_name = "partition" + str(count)
        if p_tag not in partition_tag:
            partition_tag.append(p_tag)
            partition_name.append(p_name)
            count = count + 1
    print(partition_tag)
    print(partition_name)
    return partition_tag, partition_name


def add_vectors(vectors,vectors_ids,partition_tag):
    time_start = time.time()    
    status, ids = milvus.add_vectors(collection_name=milvus_collection, records=vectors, ids=vectors_ids, partition_tag=partition_tag)
    time_end = time.time()
    print(status, "insert milvue time: ", time_end-time_start)


def main():
    connect_milvus_server()
    create_milvus_collection()
    partition_tag, partition_name = get_partition_tag()
    count = 0
    while count < (VEC_NUM // BASE_LEN):       
        vectors = load_bvecs_data(FILE_PATH,BASE_LEN,count)
        vectors_ids = [id for id in range(count*BASE_LEN,(count+1)*BASE_LEN)]
        create_partition(partition_name[count],partition_tag[count])
        add_vectors(vectors,vectors_ids,partition_tag[count])

        count = count + 1


if __name__ == '__main__':
    main()

