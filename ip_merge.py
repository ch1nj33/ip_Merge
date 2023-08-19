# -*- coding:utf-8 -*-
# @Time : 2023/8/13 15:29
# @Author : Ch1nJ33
# @Project : 0x03 Python_Script_Chin
# @File : ip_merge.py
# @Description :


import socket
import getopt
import sys
import os
import re
from alive_progress import alive_bar


# IP地址格式检查
def re_match_ip_format(ip):
    ip_pattern = re.compile(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$')
    if re.match(ip_pattern, ip):
        return ip
    else:
        return ""


def re_match_ip_list_format(ip_list):
    ip_pattern = re.compile(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$')
    ip_pattern2 = re.compile(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}-\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$')
    ip_list_plus = []  # 要增加的ip
    ip_list_minus = []  # 要删除的ip段
    for ip in ip_list:
        if re.match(ip_pattern, ip):
            # print(ip, "格式为单ip - 保留")
            continue
        elif re.match(ip_pattern2, ip):
            # print(ip, "格式为ip段 - 转换")
            for i in range(int(ip.split('-')[0].split('.')[-1]), int(ip.split('-')[1].split('.')[-1]) + 1):
                ip_list_plus.append(ip.split('-')[0].rsplit('.', 1)[0] + '.' + str(i))
            ip_list_minus.append(ip)
        else:
            # print(ip, "格式错误 - 删除")
            ip_list_minus.append(ip)
    ip_list = ip_list + ip_list_plus  # 列表扩展，直接用加号
    for ip in ip_list_minus:  # 删除ip段，只能循环remove
        ip_list.remove(ip)
    return ip_list


# 使用socket库对ip进行排序
def get_sorted_ipList(ip_file_path):
    ip_file = open(ip_file_path, 'r')
    ip_list = ip_file.readlines()
    ip_file.close()
    ip_list = [ip.strip() for ip in ip_list]  # 去除换行符
    ip_list = list(set(ip_list))  # 第一次去重
    ip_list = re_match_ip_list_format(ip_list)  # 非法格式置空
    while "" in ip_list:
        ip_list.remove("")  # 去除空值
    ip_list = list(set(ip_list))  # 再次去重
    ip_list_sort = sorted(ip_list, key=socket.inet_aton)
    return ip_list_sort


# 对排序好的列表，按C段进行分组
def group_iplist_by_c(ip_list_sort):
    ip_list_group = []  # 组名list
    ip_list_group_by_c = []
    for ip in ip_list_sort:
        ip_list_group.append(ip.split('.')[0] + '.' + ip.split('.')[1] + '.' + ip.split('.')[2])
    # 去重
    ip_list_group = list(set(ip_list_group))
    len_mult = len(ip_list_group) * len(ip_list_sort)
    # with alive_bar(len_mult, title="loading", bar="blocks", spinner='waves') as bar:
    #     for group in ip_list_group:
    #         group_set = []
    #         for ip in ip_list_sort:
    #             ip_c = ip.split('.')[0] + '.' + ip.split('.')[1] + '.' + ip.split('.')[2]
    #             if ip_c == group:
    #                 group_set.append(ip)
    #             bar()
    #         ip_list_group_by_c.append(group_set)
    with alive_bar(len_mult, title="loading", bar="blocks", spinner='waves') as bar:
        for ip in ip_list_sort:
            ip_c = ip.split('.')[0] + '.' + ip.split('.')[1] + '.' + ip.split('.')[2]
            group_set = []
            for group in ip_list_group:
                bar()
                if ip_c == group:
                    group_set.append(ip)
                    # break

            ip_list_group_by_c.append(group_set)
    return ip_list_group_by_c, len(ip_list_sort)


# 对连续ip进一步合并分组
def get_continuous_blocks(ip_list_group_by_c, len_of_list):
    ip_list_group_by_c_continuous_blocks = []
    with alive_bar(len_of_list, title="loading", bar="blocks", spinner='waves2') as bar:
        for ip_block in ip_list_group_by_c:
            res = []
            for i in range(len(ip_block)):
                if not res:
                    res.append([ip_block[i]])
                elif int(ip_block[i - 1].split('.')[-1]) + 1 == int(ip_block[i].split('.')[-1]):
                    res[-1].append(ip_block[i])
                else:
                    res.append([ip_block[i]])
                bar()
            ip_list_group_by_c_continuous_blocks.append(res)
    return ip_list_group_by_c_continuous_blocks


def ip_format(ip_list_group_by_c_continuous_blocks):
    ip_list_format = []
    with alive_bar(title="loading", unknown="stars") as bar:
        for ip_block in ip_list_group_by_c_continuous_blocks:
            if len(ip_block) == 1:
                if len(ip_block[0]) == 1:
                    ip_list_format.append(ip_block[0][0])
                    bar()
                else:
                    ip_list_format.append(ip_block[0][0] + '-' + ip_block[0][-1])
                    bar()
            elif len(ip_block) >= 253:
                ip_list_format.append(ip_block[0].replace(ip_block[0].split('.')[-1], '0/24'))
                bar()
            else:
                for ip in ip_block:
                    if len(ip) == 1:
                        ip_list_format.append(ip[0])
                    else:
                        ip_list_format.append(ip[0] + '-' + ip[-1])  # 格式为IP列表的第一个-IP列表的最后一个
                    bar()
    return ip_list_format


def write_to_file(ip_list_format, file_path_format):
    file = open(file_path_format, 'w')
    file_name_format = os.path.basename(file_path_format)
    len_of_list = len(ip_list_format)
    with alive_bar(len_of_list, title="loading", bar="blocks", spinner='waves3') as bar:
        for ip in ip_list_format:
            file.write(ip + '\n')
            bar()
    file.close()
    print("[*] 格式化文件写入成功！文件名为：", file_name_format)


def main():
    try:
        opts, args = getopt.getopt(sys.argv[1:], '-h-f:-v', ['help', 'filename=', 'version', 'output='])
    except getopt.GetoptError as err:
        print("[-] 参数错误", str(err))
        usage()
        sys.exit(2)

    output = None
    for opt, arg in opts:
        if opt in ('-h', '--help'):
            usage()
            sys.exit()
        elif opt in ('-v', '--version'):
            print("[*] 版本信息 Version is 1.01 ")
            exit()
        elif opt in ('-f', '--filename'):
            file_path = arg
            file_name = os.path.basename(file_path)
            print("[*] IP列表文件读取成功！文件名为：", file_name)
            # do something
            file_path_new = str(file_path).replace('.txt', '') + '_format.txt'
            print("[*] 开始排序--->")
            ip_list_sort = get_sorted_ipList(file_path)
            # print(ip_list_sort)
            print("[*] 开始分组--->")
            ip_list_group_by_c, len_of_list = group_iplist_by_c(ip_list_sort)
            # print(ip_list_group_by_c)
            print("[*] 开始合并--->")
            ip_list_group_by_c_continuous_blocks = get_continuous_blocks(ip_list_group_by_c, len_of_list)
            # print(ip_list_group_by_c_continuous_blocks)
            print("[*] 开始格式化--->")
            ip_list_format = ip_format(ip_list_group_by_c_continuous_blocks)
            # print(ip_list_format)
            print("[*] 开始写入文件--->")
            write_to_file(ip_list_format, file_path_new)
            exit()
        # elif opt == "--output":
        #     output = arg
        else:
            usage()
    usage()


def usage():
    print("usage: ip_merge.py [-f <ip_list.txt>] ")
    print("                   [-v] [--version] ")
    print("                   [-h] [--help]")


if __name__ == '__main__':
    print("""
     ___________  ___  ___ ___________ _____  _____ 
    |_   _| ___ \ |  \/  ||  ___| ___ \  __ \|  ___|
      | | | |_/ / | .  . || |__ | |_/ / |  \/| |__  
      | | |  __/  | |\/| ||  __||    /| | __ |  __| 
     _| |_| |     | |  | || |___| |\ \| |_\ \| |___ 
     \___/\_|     \_|  |_/\____/\_| \_|\____/\____/ 
                                                    
                                    Power by Ch1nJ33""")
    main()
