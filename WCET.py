###############################################################################
# Description:  The WCET method of our TPDS. Compared with the SOTA method in [6], 
#               we measured the bus activities, and we compute the BASE time and 
#               EXTRA time indepedently.
###############################################################################


PORT_MAP = ["LPD","HPC0","HPC1","HP0","HP1","HP2","HP3"]

# return the corresponding time of PS-PL interconnect
def connection_rules(tmpconnection:dict,transaction_transfer_time:list)->list:

    connection = [PORT_MAP.index(tmpconnection["ins"]),PORT_MAP.index(tmpconnection["data_0"]),PORT_MAP.index(tmpconnection["data_1"])]
    time = [0,0,0,0,0]
    if connection[0] == 0:
        # INS is LPD
        time[0] = transaction_transfer_time[5]
    elif connection[0] == 1 or connection[0] == 2:
        # INS is HPC
        time[0] = transaction_transfer_time[2]
    else:
        # INS is HP
        time[0] = transaction_transfer_time[0]

    if connection[1] == 0:
        # data0 is LPD
        time[1] = transaction_transfer_time[4]
        time[2] = transaction_transfer_time[6]
    elif connection[1] == 1 or connection[1] == 2:
        # data0 is HPC
        time[1] = transaction_transfer_time[2]
        time[2] = transaction_transfer_time[3]
    else:
        # data0 is HP:
        time[1] = transaction_transfer_time[0]
        time[2] = transaction_transfer_time[1]

    if connection[2] == 0:
        # data1 is LPD
        time[3] = transaction_transfer_time[4]
        time[4] = transaction_transfer_time[6]
    elif connection[2] == 1 or connection[2] == 2:
        # data1 is HPC 
        time[3] = transaction_transfer_time[2]
        time[4] = transaction_transfer_time[3]
    else:
        # data1 is HP
        time[3] = transaction_transfer_time[0]
        time[4] = transaction_transfer_time[1]
    
    return time

# get connection trace, following the system architecture of DPUs.
def get_trace(portname:str):
    tmpmap = {"LPD":["CCI","S1"],"HPC0":["HPC0_HPC1","S2"],"HPC1":["HPC0_HPC1","S2"],"HP0":["HP0","S3"],"HP1":["HP1_HP2","S4"],"HP2":["HP1_HP2","S4"],"HP3":["HP3","S5"]}
    tmp = tmpmap[portname]
    tmp.insert(0,portname)
    return tmp

# single DPU config
class config:
    def __init__(self,seq_number:int,transaction_parameter:list,transaction_transfer_time:list, data_transfer_time:list,connection:dict):  
        # model
        self.seq = seq_number
        self.model =  connection["model"]
        self.ins_port_name = connection["ins"]
        self.ins_port_trace = get_trace(connection["ins"])
        self.data0_port_name = connection["data_0"]
        self.data0_port_trace = get_trace(connection["data_0"])
        self.data1_port_name = connection["data_1"]
        self.data1_port_trace = get_trace(connection["data_1"])
        
        # counts
        self.N_ins = transaction_parameter[0]
        self.delta_ins = transaction_parameter[1]
        self.N_read_0 = transaction_parameter[2]
        self.delta_read_0 = transaction_parameter[3]
        self.N_write_0 = transaction_parameter[4]
        self.delta_wrtie_0 = transaction_parameter[5]
        self.N_read_1 = transaction_parameter[6]
        self.delta_read_1 = transaction_parameter[7]
        self.N_write_1 = transaction_parameter[8]
        self.delta_wrtie_1 = transaction_parameter[9]

        self.count_list = [self.N_ins,self.N_read_0,self.N_write_0,self.N_read_1,self.N_write_1]

        # time for PS-PL
        time = connection_rules(connection,transaction_transfer_time)
        self.t_ins_read = time[0]
        self.t_data_0_read = time[1]
        self.t_data_0_write = time[2]
        self.t_data_1_read = time[3]
        self.t_data_1_write = time[4]

        # time for DDR
        self.t_addr_read = data_transfer_time[0]
        self.t_word_read = data_transfer_time[1]
        self.t_addr_write = data_transfer_time[2]
        self.t_word_write = data_transfer_time[3]
        self.t_resp_write = data_transfer_time[4]

    def __show__(self):
        print("Model: {}".format(self.model))
        print("INS port: {}".format(self.ins_port_name))
        # print("INS port trace: {}".format(self.ins_port_trace))
        print("Data0 port: {}".format(self.data0_port_name))
        # print("Data0 port trace: {}".format(self.data0_port_trace))
        print("Data1 port: {}".format(self.data1_port_name))
        # print("Data1 port trace: {}".format(self.data1_port_trace))
    
def flattern(input:list[list]):
    if len(input) == 0:
        return []
    flattened_list = [item for sublist in input for item in sublist]
    return flattened_list

# multi-DPUs config
class group_config:
    def __init__(self,number:int,parameter_dir:dict,transaction_transfer_time:list,data_transfer_time:list,connection:list[dict]):
        # according to the connection of AXI, we should init the DPUs independently
        self.dpu_vector:list[config] = []
        self.dpu_number = number
        self.IC_1_counter:dict[list] = {"LPD":[],"HPC0":[],"HPC1":[],"HP0":[],"HP1":[],"HP2":[],"HP3":[]}
        
        for i in range(self.dpu_number):
            # For each dpu init itself
            model = connection[i]["model"]
            dpu_i = config(i,parameter_dir[model],transaction_transfer_time,data_transfer_time,connection[i])
            self.dpu_vector.append(dpu_i)

            # We use a tuple such as (dpu_number, dpu_port_name, read_count, write_count) to record 
            # the total number of transactions of a certain DPU port.
            self.IC_1_counter[dpu_i.ins_port_name].append([(dpu_i.seq,"ins",dpu_i.N_ins,0)])
            self.IC_1_counter[dpu_i.data0_port_name].append([(dpu_i.seq,"data_0",dpu_i.N_read_0,dpu_i.N_write_0)])
            self.IC_1_counter[dpu_i.data1_port_name].append([(dpu_i.seq,"data_1",dpu_i.N_read_1,dpu_i.N_write_1)])


        self.IC_2_counter:dict[list] = \
            {"CCI":[flattern(self.IC_1_counter["LPD"])],\
            "HPC0_HPC1":[flattern(self.IC_1_counter["HPC0"]) , flattern(self.IC_1_counter["HPC1"])],\
            "HP0":[flattern(self.IC_1_counter["HP0"])],\
            "HP1_HP2":[flattern(self.IC_1_counter["HP1"]) , flattern(self.IC_1_counter["HP2"])],\
            "HP3":[flattern(self.IC_1_counter["HP3"])]}

        self.PA_counter = [\
                        flattern(self.IC_2_counter["CCI"]) ,\
                        flattern(self.IC_2_counter["HPC0_HPC1"]),\
                        flattern(self.IC_2_counter["HP0"]),\
                        flattern(self.IC_2_counter["HP1_HP2"]),\
                        flattern(self.IC_2_counter["HP3"])
                        ]
        self.contention_layers:list[dict] = [self.IC_1_counter,self.IC_2_counter,self.PA_counter]


    def __show__(self):
        print("Display the current connection:")
        print("{} DPU(s) in total".format(self.dpu_number))
        print()
        for i in range(self.dpu_number):
            print("DPU {}:".format(self.dpu_vector[i].seq))
            self.dpu_vector[i].__show__()
            print()
        # print("IC1 Contention:")
        # for key,value in self.IC_1_counter.items():
        #     print("{}: {}".format(key,value))
        # print()
        # print("IC2 Contention:")
        # for key,value in self.IC_2_counter.items():
        #     print("{}: {}".format(key,value))
        # print()                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                
        # print("PA Contention:")
        # print(self.PA_counter)
        print()


# get T_BASE
def get_T_base(p:config):
    # T_a^{base} = T_a^{trsf} + T_a^{wait}, a belong to {R, W, INS}
    T_INS_trsf = (p.N_ins * p.t_ins_read) + (p.N_ins * p.t_addr_read) + (p.delta_ins * p.t_word_read)
    T_R_trsf = ((p.N_read_0 + p.N_read_1) * p.t_data_0_read) + ((p.N_read_0 + p.N_read_1) * p.t_addr_read) + \
        ((p.delta_read_0 + p.delta_read_1) * p.t_word_read)
    T_W_trsf = ((p.N_write_0 + p.N_write_1) * p.t_data_0_write) + ((p.N_write_0 + p.N_write_1) * (p.t_addr_write + p.t_resp_write)) + \
        ((p.delta_wrtie_0 + p.delta_wrtie_1) * p.t_word_write)
    
    T_INS_wait = min((2*p.N_ins), p.N_read_0 + p.N_read_1) * max(p.t_data_0_read,p.t_data_1_read)
    T_R_wait = min(p.N_ins, (p.N_read_0 + p.N_read_1)) * p.t_ins_read

    T_R_base = T_R_trsf + T_R_wait
    T_INS_base = T_INS_trsf + T_INS_wait
    T_W_base = T_W_trsf

    print("T_R_BASE: {:6f} s\nT_INS_BASE: {:6f} s\nT_W_BASE: {:6f} s\n".format(Time_transform(T_R_base,300000000),Time_transform(T_INS_base,300000000),Time_transform(T_W_base,300000000)))
    T_BASE = max(T_R_base,T_W_base + T_INS_base)

    return T_BASE

# get the N of contention transactions number in IC1 , IC2 and PA
def get_contention_N_IC(dpu_id:int,layer:int,node:str,portname:str,op:int,gp:group_config):

    contention_N = 0
    if layer == 2:
        interconnect_node = gp.contention_layers[layer]
    else:
        interconnect_node = gp.contention_layers[layer][node]  
    number = len(interconnect_node)
    if number <= 1:
        return contention_N
    # op==0 means read , op ==1 means write
    N_read = 0           
    N_write = 0
    if portname == "ins":
        N_read = gp.dpu_vector[dpu_id].count_list[0]
        N_write = 0
    elif portname == "data_0":
        N_read = gp.dpu_vector[dpu_id].count_list[1]
        N_write = gp.dpu_vector[dpu_id].count_list[2]
    elif portname == "data_1":
        N_read = gp.dpu_vector[dpu_id].count_list[3]
        N_write = gp.dpu_vector[dpu_id].count_list[4]
    origin_port = (dpu_id,portname,N_read,N_write)      
    local_count = 0
    if op == 0:
        local_count = N_read
    elif op ==1 :
        local_count = N_write

    for port_sub_list in interconnect_node:
        other_count = 0
        if origin_port in port_sub_list:
            continue
        else:
            for port in port_sub_list:
                if port[0] == origin_port[0]:
                    continue
                else:
                    if op == 0:
                        other_count += port[2]
                    elif op == 1:
                        other_count += port[3]
            contention_N += min(local_count,other_count)
    return contention_N

# get T_EXTRA for DPU_i
def get_T_extra(seq:int,gp:group_config):
    # T_EXTRA = T_INS^EXTRA + T_R^EXTRA + T_W^EXTRA
    target_dpu_id = seq
    target_ins_trace = gp.dpu_vector[target_dpu_id].ins_port_trace
    target_data0_trace = gp.dpu_vector[target_dpu_id].data0_port_trace
    target_data1_trace = gp.dpu_vector[target_dpu_id].data1_port_trace

    N_ins_IC1 = get_contention_N_IC(target_dpu_id,0,target_ins_trace[0],"ins",0,gp)

    N_data_0_read_IC1 = get_contention_N_IC(target_dpu_id,0,target_data0_trace[0],"data_0",0,gp)
    N_data_1_read_IC1 = get_contention_N_IC(target_dpu_id,0,target_data1_trace[0],"data_1",0,gp)

    N_data_0_write_IC1 = get_contention_N_IC(target_dpu_id,0,target_data0_trace[0],"data_0",1,gp)
    N_data_1_write_IC1 = get_contention_N_IC(target_dpu_id,0,target_data1_trace[0],"data_1",1,gp)


    N_ins_IC2 = get_contention_N_IC(target_dpu_id,1,target_ins_trace[1],"ins",0,gp)

    N_data_0_read_IC2 = get_contention_N_IC(target_dpu_id,1,target_data0_trace[1],"data_0",0,gp)
    N_data_1_read_IC2 = get_contention_N_IC(target_dpu_id,1,target_data1_trace[1],"data_1",0,gp)

    N_data_0_write_IC2 = get_contention_N_IC(target_dpu_id,1,target_data0_trace[1],"data_0",1,gp)
    N_data_1_write_IC2 = get_contention_N_IC(target_dpu_id,1,target_data1_trace[1],"data_1",1,gp)

    
    N_ins_PA = get_contention_N_IC(target_dpu_id,2,target_ins_trace[2],"ins",0,gp)

    N_data_0_read_PA = get_contention_N_IC(target_dpu_id,2,target_data0_trace[2],"data_0",0,gp)
    N_data_1_read_PA = get_contention_N_IC(target_dpu_id,2,target_data1_trace[2],"data_1",0,gp)

    N_data_0_write_PA = get_contention_N_IC(target_dpu_id,2,target_data0_trace[2],"data_0",1,gp)
    N_data_1_write_PA = get_contention_N_IC(target_dpu_id,2,target_data1_trace[2],"data_1",1,gp)



    T_ins_IC1 = N_ins_IC1 * gp.dpu_vector[target_dpu_id].t_ins_read
    T_read_IC1 = (N_data_0_read_IC1 * gp.dpu_vector[target_dpu_id].t_data_0_read) + \
                    (N_data_1_read_IC1 * gp.dpu_vector[target_dpu_id].t_data_1_read)

    T_write_IC1 = (N_data_0_write_IC1 * gp.dpu_vector[target_dpu_id].t_data_0_write) + \
                    (N_data_1_write_IC1 * gp.dpu_vector[target_dpu_id].t_data_1_write ) 

    T_ins_IC2 = N_ins_IC2 * gp.dpu_vector[target_dpu_id].t_ins_read
    T_read_IC2 = (N_data_0_read_IC2 * gp.dpu_vector[target_dpu_id].t_data_0_read) + \
                    (N_data_1_read_IC2 * gp.dpu_vector[target_dpu_id].t_data_1_read)
    T_write_IC2 = (N_data_0_write_IC2 * gp.dpu_vector[target_dpu_id].t_data_0_write )+ \
                    (N_data_1_write_IC2 * gp.dpu_vector[target_dpu_id].t_data_1_write)

    T_ins_PA = N_ins_PA * TRANSACTION_TRANSFER_TIME[0]
    # two data ports in the same XPI port
    if target_data0_trace[2] == target_data1_trace[2]:
        T_read_PA = (N_data_0_read_PA + N_data_1_read_PA) * TRANSACTION_TRANSFER_TIME[0]
        T_write_PA = (N_data_0_write_PA + N_data_1_write_PA) * TRANSACTION_TRANSFER_TIME[0]
    # two data ports in different XPI ports
    else :

        for single_PA_list in gp.contention_layers[2]:
            N_data_0_read_local = gp.dpu_vector[target_dpu_id].N_read_0
            N_data_1_read_local = gp.dpu_vector[target_dpu_id].N_read_1
            N_data_0_write_local = gp.dpu_vector[target_dpu_id].N_write_0
            N_data_1_write_local = gp.dpu_vector[target_dpu_id].N_write_1

            N_PA_read_i = 0
            N_PA_write_i = 0
            T_read_PA = 0
            T_write_PA  = 0
            for port in single_PA_list:
                N_PA_read_i += port[2]
                N_PA_write_i += port[3]
            T_read_PA += (min(N_PA_read_i,N_data_0_read_local + N_data_1_read_local) - \
                          N_data_0_read_local - N_data_1_read_local +\
                           2 * min(N_data_0_read_PA,N_data_1_read_PA) ) * TRANSACTION_TRANSFER_TIME[0]
            T_write_PA += (min(N_PA_write_i,N_data_0_write_local + N_data_1_write_local) - \
                          N_data_0_write_local - N_data_1_write_local +\
                           2 * min(N_data_0_write_PA,N_data_1_write_PA) ) * TRANSACTION_TRANSFER_TIME[1]
            

    T_ins_extra = T_ins_IC1 + T_ins_IC2 + T_ins_PA
    T_read_extra = T_read_IC1 + T_read_IC2 + T_read_PA
    T_write_extra = T_write_IC1 + T_write_IC2 + T_write_PA

    print("T_R_EXTRA: {:.6f} s\nT_INS_EXTRA: {:.6f} s\nT_W_EXTRA: {:.6f} s\n".format(Time_transform(T_read_extra,300000000),Time_transform(T_ins_extra,300000000),Time_transform(T_write_extra,300000000)))

    return max(T_ins_extra + T_write_extra,T_read_extra)

# turn the cycles into real time in second
def Time_transform(cycles,frequency):
    time = cycles/frequency
    return time

# TransactionCounter Bus acitvity, 10 parameters:
# N_ins, delta_ins, N_R^0, delta_R^0, N_W^0, delta_W^0, N_R^1, delta_R^1, N_W^1, delta_W^1


# B3136 for vivado 2021.2 
# TRANSACTION_PARAMETERS = {
#     # mobilenetv2 B3136
#     "mobilenetv2": [15073,241180,17676,201364,2667,41125,17420,198497,2665,41115],
#     # squeezenet B3136
#     "squeezenet": [5931,94906,8037,89512,5668,37139,7876,87763,5141,32986],
#     # yolov3 B3136
#     "yolov3": [109206,1747308,389287,3924561,77050,1083905,390396,3929578,76240,1071641],
#     # yolov4 B3136
#     "yolov4": [64110,1025763,289449,2924614,132577,1289706,280804,2859145,129431,1266401],
#     # VPGnet B3136
#     "VPGnet": [12552,200844,23071,234938,32518,174841,22939,233901,29715,174175],
#     # OD_SSD B3136
#     "OD_SSD": [11646,186349,33275,360383,20482,307502,33416,362339,19254,291694],
#     # PD_SSD B3136
#     "PD_SSD": [12156,194503,29188,305487,16860,256068,31625,330589,17181,261103]
# }
# T_elab = {"mobilenetv2":0.00102 ,
#     # squeezenet B4096
#     "squeezenet": 0.00042,
#     # yolov3 B4096
#     "yolov3": 0.00124,
#     # yolov4 B4096
#     "yolov4": 0.00111,
#     # VPGnet B4096
#     "VPGnet": 0.00087,
#     # OD_SSD B4096
#     "OD_SSD": 0.00231,
#     # PD_SSD B4096
#     "PD_SSD":0.00161 }

# B4096 for vivado 2021.2 
TRANSACTION_PARAMETERS = {
    # mobilenetv2 B4096
    "mobilenetv2": [14878,238059,16652,188888,2368,34247,16376,186011,2361,34169],
    # squeezenet B4096
    "squeezenet": [5520,88324,5456,62557,3928,25827,7762,83946,4918,31688],
    # yolov3 B4096
    "yolov3": [61350,981609,387837,3799013,73605,1097426,386894,3800027,71829,1067367],
    # yolov4 B4096
    "yolov4": [57838,925419,277159,2773556,124835,1212134,274291,2760906,128951,1242525],
    # VPGnet B4096
    "VPGnet": [12549,200793,22953,234596,32680,175038,23047,234888,29761,174678],
    # OD_SSD B4096
    "OD_SSD": [8053,128862,32969,345949,18349,279404,32895,345167,16588,252439],
    # PD_SSD B4096
    "PD_SSD": [7970,127532,28406,297299,16337,247791,28303,295502,15395,233835],
}
T_elab = {"mobilenetv2":0.0002 ,
    # squeezenet B4096
    "squeezenet": 0.0001,
    # yolov3 B4096
    "yolov3": 0.00058,
    # yolov4 B4096
    "yolov4": 0.00055,
    # VPGnet B4096
    "VPGnet": 0.00023,
    # OD_SSD B4096
    "OD_SSD": 0.00034,
    # PD_SSD B4096
    "PD_SSD":0.0007 }




# Transfer time of DDR
# t_read^addr, t_read^word, t_write^addr, t_write^word, t_write^resp
DATA_TRANSFER_TIME = [1,1,1,2,1]

# Transfer time of PS-PL ports
# t_read^HP, t_write^HP, t_read^HPC, t_write^HPC, t_read^LPD_D, t_read^LPD_INS, t_write^LPD
TRANSACTION_TRANSFER_TIME = [35,25,38,28,146,40,74]

PORT_MAP = ["LPD","HPC0","HPC1","HP0","HP1","HP2","HP3"]

# Current configuration
ALL_CONNECTION:list[dict] = [
    {"ins":"LPD","data_0":"HP0","data_1":"HP1","model":"yolov4"},
    {"ins":"LPD","data_0":"HP2","data_1":"HP3","model":"yolov4"},
    {"ins":"LPD","data_0":"HPC0","data_1":"HPC1","model":"mobilenetv2"},
    ]


if __name__ == "__main__":

    dpus = group_config(len(ALL_CONNECTION), TRANSACTION_PARAMETERS,TRANSACTION_TRANSFER_TIME, DATA_TRANSFER_TIME,ALL_CONNECTION)
    dpus.__show__()

    # get T_BASE in seq
    for i in range(dpus.dpu_number):
        print("Modelname: {}".format(dpus.dpu_vector[i].model))
        time_base = get_T_base(dpus.dpu_vector[i])
        if dpus.dpu_number == 1:
            time_extra = 0
        else:
            time_extra = get_T_extra(i,dpus)
        time = time_base + time_extra 
        time = Time_transform(time, 300000000) + T_elab[dpus.dpu_vector[i].model]
        print("{} base time: {} s".format(dpus.dpu_vector[i].model,Time_transform(time_base,300000000)))
        print("{} extra time: {} s".format(dpus.dpu_vector[i].model,Time_transform(time_extra,300000000)))
        print("{} total time: {} s".format(dpus.dpu_vector[i].model,time))
        print()




  

