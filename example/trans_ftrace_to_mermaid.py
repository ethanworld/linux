import os
import sys
import subprocess

from enum import Enum

ftrace_filename = "ftrace_do_sys_open"
ftrace_filename = "ftrace_do_splice_read"
white_list = ["fs", "mm", "kernel"]
func_file_map = {}
func_file_modules = ["default"]
output = []

class Direction(Enum):
    CALL = 1
    RETURN = 2
    STOP = 3

def format_print(tab: int, left: str, right:str, direction: Direction):
    src = func_file_map[left] if left in func_file_map else "default"
    dest = func_file_map[right] if right in func_file_map else "default"
    if src not in func_file_modules:
        func_file_modules.append(src)
    if dest not in func_file_modules:
        func_file_modules.append(dest)
    print_prefix = "|-" * tab
    file_prefix = "  " * tab
    if direction == Direction.CALL:
        line = "{} ->>+ {}: {}".format(src, dest, right)
    if direction == Direction.RETURN:
        line = "{} ->>- {}: ret".format(src, dest)
    if direction == Direction.STOP:
        line = "{} ->> {}: {}".format(src, dest, right)
    output.append(file_prefix + line)
    print(print_prefix + line)

def ftrace_dfs(path:list, all_lines:list, pos:int):
    if pos >= len(all_lines):
        return
    line = str(all_lines[pos])
    func = line.split("(")[0]
    # 调用栈到底
    if line.endswith(";"):
        format_print(len(path), path[-1], func, Direction.STOP)
    if line.endswith("{"):
        format_print(len(path), path[-1], func, Direction.CALL)
        path.append(func)
    if line.endswith("}"):
        func = path.pop()
        format_print(len(path),  func, path[-1], Direction.RETURN)
    ftrace_dfs(path, all_lines, pos + 1)

def ftrace_read():
    filepath = os.path.join(os.path.dirname(os.path.abspath(__file__)), ftrace_filename)
    all_lines = []
    with open(filepath) as f:
        for line in f.readlines():
            all_lines.append("".join(line.split("|")[1:]).strip())
    ftrace_dfs(["start"], all_lines, 0)


def get_functions_nm(filepath: str):
    filemodule = filepath.split("kernel_dev/linux/")[1]
    try:
        # 执行 nm 命令
        # -g: 只显示外部符号 (全局函数)
        # -C: 解码 C++ 符号名 (如果是 C++ 文件)
        result = subprocess.run(['nm' , filepath], 
                                capture_output=True, text=True, check=True)
        
        for line in result.stdout.splitlines():
            # nm 输出格式通常为: 地址 类型 名称
            # 我们寻找类型为 'T' (代码段) 的行
            parts = line.split()
            if len(parts) >= 3 and parts[1] in ['T', 't']:
                func_file_map[parts[2]] = filemodule
                
    except subprocess.CalledProcessError as e:
        print(f"命令执行错误: {e}")


def filepath_dfs(dirpath: str):
    for root, dirs, files in os.walk(dirpath):
        for file in files:
            if not str(file).endswith(".o"):
                continue
            filepath = os.path.join(root, file)
            get_functions_nm(filepath=filepath)
        for dirpath in dirs:
            filepath_dfs(os.path.join(root, dirpath))

def get_functions_map():
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    for root, dirs, files in os.walk(root_dir):
        for dirname in dirs:
            if dirname not in white_list:
                continue
            filepath_dfs(os.path.join(root, dirname))

def generate_mermaid():
    filepath = os.path.join(os.path.dirname(os.path.abspath(__file__)), "{}_output.mermaid".format(ftrace_filename))
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write("sequenceDiagram\n")
        for line in func_file_modules:
            f.write("participant  " + line + "\n")
        
        for line in output:
            f.write(line + '\n')
        

if __name__ == '__main__':
    get_functions_map()
    ftrace_read()
    generate_mermaid()