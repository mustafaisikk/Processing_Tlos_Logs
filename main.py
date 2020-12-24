import re
import os
import openpyxl
from openpyxl import Workbook, load_workbook

# This is a sample Python script.

# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.
file_list = []
last_query_list = []
failed_data = []
last_file = "first"
in_logs_output_library = []
last_query_array = []

class query:
    def __init__(self, all_string, type, path, input_library, input_table, output_library, output_table, input_row,
                 output_row,is_local_maximum):
        self.all_string = all_string
        self.type = type
        self.path = path
        self.input_library = input_library
        self.input_table = input_table
        self.output_library = output_library
        self.output_table = output_table
        self.input_row = input_row
        self.output_row = output_row
        self.is_local_maximum = is_local_maximum


def get_table_and_library(table_and_library):
    table_and_library_return = table_and_library.split(".")

    if len(table_and_library_return) == 2:
        if table_and_library_return[0] == "" or table_and_library_return[1] == "":
            table_and_library_return = table_and_library.replace(".", "").split(".")
    if len(table_and_library_return) == 1:
        return "WORK", table_and_library_return[0]
    else:
        return table_and_library_return[0], table_and_library_return[1]

def read_directory_all_log_file(path):
    global last_file
    files = os.scandir(path)

    for file in files:
        if file.is_dir():
            read_directory_all_log_file(file)

        elif file.is_file() and (last_file.replace(".log","") not in file.name):
            if file.name.split(".")[1] == "log":
                file_list.append(file.path)
                last_file = file.name
        else:
            print("Error file: ", file.name)

def is_there_before(file):
    temp = file.path.split("\\")
    if temp[3] != "sas":
        return True
    temp[3] = "bidm"
    last = temp[0]
    for var in range(1,len(temp)):
        last+="\\"+temp[var]

    if last in file_list:
        return False
    else:
        return True

def find_which_library(output_library):
    di_libs = ["DASHLIBD","DMLIB","MIGLIB","NEDLIB","ODSLIB","ODSLIB2",
               "ODSLIB3","PILIB","PODSLIB1","PODSLIB2","PODSLIB3","QLIKLIB",
               "TMPLIB3","TMPLIB4","TRNLIB","TRNLIB2","UTFLIB"]

    miner_libs = ["PILIB2","BFLIB","TMPLIB2","DMLIB2","ARCLIB","AUTODIAL",
                  "IADM","IATMP","BCSDM","BLDM","BLTMP","BADM","BATMP","CCDM","CCDM2",
                  "CMPDM","CPSFRC","CPSHRLY","CPSREG","CPSUST","CXDM","D2DLIB","DSTDM",
                  "DSTTMP","DYMDM","DYMTMP","DBALIB","EAP_ETY","EAP_PAY","EAP_PR",
                  "EPYDM","EPYTMP","ETSDM","FADM","FPCLIB","FPCTMP","HRDM","KMHMDM",
                  "CSSLIB","MDLIB","MHMDM","MHMAYEDS","MKVR","MSADM","MSATMP","MTHEO",
                  "MTHKA","MTHMA","MTHSO","MTHTMP","MIGLIB2","OKMDM","OKMTMP","PMDM",
                  "PRCDM2","CNPRCDM","CNPRCTMP","PRCDM","PRCTMP","PRFTBLIB","FRCARC",
                  "FRCPRD","HDGARC","HDGPRD","PRCHARC","PRCHPRD","PRICARC","PRICPRD",
                  "QL_SALES","RAPARCH","RAPOUT","RAPREF","RAPTEST","RAPTMP","RAPVAS",
                  "REFCPS","SDLIB","RMCDM","RMCTMP","RODQLIK","SAHOL","SHFDM","SODM",
                  "SOPDM","SOSUF","SOTMP","SPDM","SSIMDM","STLF","SOMLIB","SMDM","SMTMP",
                  "TKDM","TSDM","TALDM","QVYDM","STJVYDM","VYDM","VYDMKVKK","EDULIB",
                  "TMPLIB","OGMDM","OGMTMP","RASTMP","CRLIB","SOSEC"]

    if output_library in di_libs:
        return ""
        # return "DILIB"
    elif output_library in miner_libs and output_library != "WORK":
        return "MINERLIBS"
    elif output_library == "WORK":
        return ""
        # return "WORK"
    else:
        return "Error LIB"

def read_log_file(path):
    match_list = []
    control = ""
    last_line = ""
    temp = ""

    with open(path, "r") as file:

        for line in file:
            line = line.upper()
            find_start = line.find("/*")
            find_end = line.find("*/")

            if find_start > 0 and find_end < 0:
                temp = "1"

            elif find_start < 0 and find_end > 0:
                temp = ""
            elif temp == "" and find_start < 0 and find_end < 0:

                if re.search("[0-9]+[ ]*PROC SQL[ ]*;", line) or re.search("[0-9]+[ ]*.[ ]*PROC SQL[ ]*;", line):
                    control = "PROC"
                    type = "PROC"
                    last_line = ""
                elif re.search("MPRINT(.*?)PROC SQL(.*?);", line):
                    control = "PROC"
                    type = "PROC MPRINT"
                    last_line = ""

                elif re.search("[0-9]+ [ ]* DATA ([A-Z,0-9,_]+[\.]*[A-Z,0-9,_]*)[ ]*;", line):
                    control = "DATA"
                    type = "DATA"
                    last_line = ""

                elif re.search("MPRINT(.*?) DATA ([A-Z,0-9,_]+[\.]*[A-Z,a-z,0-9,_]*)", line):
                    control = "DATA"
                    type = "DATA MPRINT"
                    last_line = ""

                if control == "PROC" or control == "DATA":
                    line = line.replace('\n', ' ')
                    line = line.replace('\t', '')
                    line = line.replace('\f', '')

                    last_line += line

                if "CPU TIME" in line and (control == "PROC" or control == "DATA"):
                    match_list.append([type, last_line])
                    last_line = ""
                    control = ""

    file.close()
    create_query_list(match_list, path)


def create_query_list(query_list, path):
    for _query_and_type in query_list:

        type = _query_and_type[0]
        input_library = []
        input_table = []
        output_library = ""
        output_table = ""
        input_row = []
        output_row = ""
        which_library = ""
        _query = _query_and_type[1]

        if "PROC" in type:

            if "MPRINT" not in type:
                value = re.findall("TABLE ([A-Z]+[A-Z,0-9,_]*[\.]*[A-Z,0-9,_]*) CREATED", _query)
                if len(value) > 0:
                    output_library, output_table = get_table_and_library(value[0])

                if output_library == "" and output_table == "":
                    value = re.findall("CREATE TABLE ([A-Z]+[A-Z,0-9,_]*[\.]*[A-Z,0-9,_]*)", _query)
                    if len(value) > 0:
                        output_library, output_table = get_table_and_library(value[0])

                    if output_library == "" and output_table == "":

                        value = re.findall("INTO[ ]?:([A-Z]+[A-Z,0-9,_]*[\.]*[A-Z,0-9,_]*)", _query)
                        if len(value) > 0:
                            output_library, output_table = get_table_and_library(value[0])

                        if output_library == "" and output_table == "":

                            value = re.findall("INSERT INTO[ ]*([A-Z]+[A-Z,0-9,_]*[\.]*[A-Z,0-9,_]*)", _query)
                            if len(value) > 0:
                                output_library, output_table = get_table_and_library(value[0])

                value = re.findall("DELETE[ ,0-9]*FROM(.[^ ]*)", _query)
                if len(value) > 0:
                    output_library, output_table = get_table_and_library(value[0])
                    value_input = re.findall("SELECT ID FROM (\w+\.?\w*)", _query)
                    if len(value_input) > 0:
                        input_library.append(get_table_and_library(value_input[0])[0])
                        input_table.append(get_table_and_library(value_input[0])[1])

                if len(input_library) == 0:
                    value = re.findall("FROM[0-9, ,\+]*([A-Z]+[A-Z,0-9,_]*[\.]*[A-Z,0-9,_]*)", _query)
                    if len(value) > 0:
                        for sub_value in value:
                            input_library.append(get_table_and_library(sub_value)[0])
                            input_table.append(get_table_and_library(sub_value)[1])

                    value = re.findall(
                        "[0-9]+ [ ]* [LEFT,RIGHT,FULL,INNER]* JOIN ([A-Z]+[A-Z,0-9,_]*[\.]*[A-Z,0-9,_]*)", _query)
                    if len(value) > 0:
                        for sub_value in value:
                            input_library.append(get_table_and_library(sub_value)[0])
                            input_table.append(get_table_and_library(sub_value)[1])

                value = re.findall("WITH ([0-9]+) ROWS ", _query)
                if len(value) > 0:
                    output_row = value[0]

                value = re.findall("([0-9]+) ROWS WERE [INSERTED,DELETED]", _query)
                if len(value) > 0:
                    output_row = value[0]

            elif "MPRINT" in type:

                value = re.findall("SELECT COUNT.*INTO[ ]?:([A-Z]+[A-Z,0-9,_]*[\.]*[A-Z,0-9,_]*)", _query)
                if len(value) > 0:
                    output_library, output_table = get_table_and_library(value[0])
                value = re.findall("FROM ([A-Z]+[A-Z,0-9,_]*[\.]*[A-Z,0-9,_]*)", _query)
                if len(value) > 0:
                    input_library.append(get_table_and_library(value[0])[0])
                    input_table.append(get_table_and_library(value[0])[1])
            if "CONNECT TO SQLSVR" in _query:
                input_library = ["SQLSVR"]
                input_table = ["SQLSVR"]

        elif "DATA" in type:

            value = re.findall("THE DATA SET (\w+\.?\w*) HAS", _query)
            if len(value) > 0:
                output_library, output_table = get_table_and_library(value[0])

            if len(output_library) == 0:
                value = re.findall("[0-9]+ [ ]* DATA (\w+\.?\w*) *;", _query)
                if len(value) > 0:
                    output_library, output_table = get_table_and_library(value[0])

                if len(output_library) == 0:
                    value = re.findall("DATA (\w+\.?\w*)[ ]*;", _query)
                    if len(value) > 0:
                        output_library, output_table = get_table_and_library(value[0])

            value = re.findall("READ FROM THE DATA SET (\w+\.?\w*)", _query)
            if len(value) > 0:#(\w+\.?\w*)
                for var in value:
                    input_library.append(get_table_and_library(var)[0])
                    input_table.append(get_table_and_library(var)[1])

            if len(input_library) == 0 and "ERROR:" in _query:
                value = re.findall("[0-9]+ [ ]* SET(.[^;]*)[ ]*;", _query)
                if len(value) > 0:
                    value2 = re.findall("\w+\.?\w*",value[0])
                    if len(value2)>0:
                        for var in value2:
                            input_library.append(get_table_and_library(var)[0])
                            input_table.append(get_table_and_library(var)[1])

            # if len(input_library) == 0:
            #     value = re.findall("[0-9]+ [ ]* MERGE(.[^;]*)[ ]*;", _query)
            #     if len(value) > 0:
            #         value2 = re.findall("[A-Z,0-9,_]+[\.]+[A-Z,0-9,_]+", value[0])
            #         if len(value2) > 0:
            #             for var in value2:
            #                 input_library.append(get_table_and_library(var)[0])
            #                 input_table.append(get_table_and_library(var)[1])

            value = re.findall("WERE ([0-9]+) OBSERVATIONS", _query)
            if len(value) > 0:
                for var in value:
                    input_row.append(var)
            value = re.findall("HAS ([0-9]+) OBSERVATIONS", _query)
            if len(value) > 0:
                output_row = value[0]

            if len(input_table) == 0 and len(input_library) == 0:
                input_library.append("HARD CODED")
                input_table.append("HARD CODED")

        # which_library = find_which_library(output_library)
        # last_query_list.append(
        #     query(_query, type, path, input_library, input_table, output_library, output_table, input_row,output_row))

        make_test(query(_query, type, path, input_library, input_table, output_library, output_table, input_row,
                        output_row,""))


def which_library_is_maximum(libs):
    global last_query_list

    for query in last_query_list:
        temp = query[1] + "." + query[2]
        if temp in libs:
            libs.remove(temp)


    return libs

def update_query_list(libs):
    global last_query_list

    for query in last_query_list:
        temp = query[3] + "." + query[4]
        if temp in libs:
            query[7] = "Maximum"

def get_different_array(list):
    different_array=[]

    for var in list:
        if var not in different_array:
            different_array.append(var)
    return different_array

def create_xlsx_file():
    global last_query_list
    global in_logs_output_library
    wb = Workbook()
    ws = wb.active
    ws.title = "Addictions"
    ws.append(
        ["PATH", "Input_Table_Library", "Input_Table", "Output_Table_Library", "Output_Table", "Input_Row_Num",
         "Output_Row_Num","Is_Local_Maximum"])

    for file in file_list:
        read_log_file(file)
        local_maximum = which_library_is_maximum(in_logs_output_library)
        update_query_list(local_maximum)
        last_query_list = get_different_array(last_query_list)
        in_logs_output_library = []
        for query in last_query_list:
            ws.append(
                [query[0], query[1], query[2], query[3],
                 query[4], query[5], query[6], query[7]])


        last_query_list = []

    wb.save("Addictions.xlsx")


def make_test(_query):
    control = ""
    if re.search("[CREATE,DROP]+ VIEW ([A-Z,0-9,_]+[\.]*[A-Z,0-9,_]*)", _query.all_string):
        control = "NOT IN"

    # if "DATA _NULL_;" in _query.all_string:
    #     control = "NOT IN"

    if "DROP TABLE" in _query.all_string:
        control = "NOT IN"

    # if "CREATE TABLE" in _query.all_string:
    #     control = "NOT IN"

    # if len(_query.input_library) > 0:
    #     if _query.input_library[0] == "HARD CODED" and len(_query.input_row) == 0:
    #         control = "NOT IN"
    #     if _query.input_library[0] == "SQLSVR" and (_query.output_library == "" and _query.output_table == ""):
    #         control = "NOT IN"

    # problem = ""
    #
    # if len(_query.input_library) == 0 or len(_query.input_table) == 0:
    #     problem = "problem input"
    #
    # elif _query.output_library == "" or _query.output_table == "":
    #     problem = "problem output"

    # if _query.output_library == "":
    #     print("")

    if control != "NOT IN":
        for i in range(len(_query.input_library)):
            if len(_query.input_row) > i:
                _query_array = [_query.path, _query.input_library[i], _query.input_table[i],
                                _query.output_library, _query.output_table, _query.input_row[i],
                                _query.output_row, _query.is_local_maximum]
            else:
                _query_array = [_query.path, _query.input_library[i], _query.input_table[i],
                                _query.output_library, _query.output_table, "",
                                _query.output_row, _query.is_local_maximum]
            if _query_array not in last_query_list:
                last_query_list.append(_query_array)


        if _query.output_library != "WORK" and _query.output_library != "":
            if (_query.output_library + "." + _query.output_table ) not in in_logs_output_library:
                in_logs_output_library.append(_query.output_library + "." + _query.output_table)


def read_and_create_new_xlsx_file():
    path = r"C:\Users\mustafaisik\PycharmProjects\pythonProject\Addictions.xlsx"
    wb_object = openpyxl.load_workbook(path)
    sheet_obj = wb_object.active
    max_row = sheet_obj.max_row
    temp = []
    say = 1
    wb = Workbook()
    ws = wb.active
    ws.title = "Addictions_last"
    ws.append(
        ["PATH", "Input_Table_Library", "Input_Table", "Output_Table_Library", "Output_Table", "Input_Row_Num",
         "Output_Row_Num", "Is_Local_Maximum","Before_is_Maximum"])

    for i in range(2, (max_row+1)):
        before_record_output_library = sheet_obj.cell(row=i, column=4).value

        if before_record_output_library != "WORK" and before_record_output_library is not None:
            before_record_path = sheet_obj.cell(row=i, column=1).value
            before_record_output_table = sheet_obj.cell(row=i, column=5).value
            before_record_local_max = sheet_obj.cell(row=i, column=8).value

            for j in range(2, (max_row+1)):
                after_record_path = sheet_obj.cell(row=j, column=1).value
                if before_record_path != after_record_path:
                    after_record_input_library = sheet_obj.cell(row=j, column=2).value
                    if after_record_input_library != "WORK":
                        after_record_input_table = sheet_obj.cell(row=j, column=3).value

                        if before_record_output_library + "." + before_record_output_table == after_record_input_library + "." + after_record_input_table:
                            print(say)
                            say += 1
                            ws.append(
                                [after_record_path, after_record_input_library, after_record_input_table,sheet_obj.cell(row=j, column=4).value ,
                                 sheet_obj.cell(row=j, column=5).value, sheet_obj.cell(row=j, column=6).value, sheet_obj.cell(row=j, column=7).value,
                                 sheet_obj.cell(row=j, column=8).value,before_record_local_max])



    wb.save("Addictions_Last.xlsx")

if __name__ == '__main__':

    read_directory_all_log_file(r'C:\Users\mustafaisik\PycharmProjects\pythonProject\logs')

    create_xlsx_file()

    read_and_create_new_xlsx_file()

    print("hey")
