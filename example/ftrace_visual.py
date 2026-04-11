import os
import sys
import subprocess

from enum import Enum

class Direction(Enum):
    CALL = 1
    RETURN = 2
    STOP = 3

class Visual(Enum):
    MERMAID = 1
    PLANTUML = 2

class Ftrace:

    def __init__(self, ftrace_filename):
        self.output = []
        self.func_file_map = {}
        self.resources_dirname = "resources"
        self.ftrace_filename = ftrace_filename
        self.white_list = ["fs", "mm"]
        self.func_file_modules = ["default"]

    def format_print(self, tab: int, left: str, right:str, direction: Direction):
        pass

    def ftrace_dfs(self, path:list, all_lines:list, pos:int):
        if pos >= len(all_lines):
            return
        line = str(all_lines[pos])
        func = line.split("(")[0]
        # 调用栈到底
        if line.endswith(";"):
            self.format_print(len(path), path[-1], func, Direction.STOP)
        if line.endswith("{"):
            self.format_print(len(path), path[-1], func, Direction.CALL)
            path.append(func)
        if line.endswith("}"):
            func = path.pop()
            self.format_print(len(path),  func, path[-1], Direction.RETURN)
        self.ftrace_dfs(path, all_lines, pos + 1)

    def ftrace_read(self):
        filepath = os.path.join(os.path.dirname(os.path.abspath(__file__)), "{}/{}".format(self.resources_dirname, self.ftrace_filename))
        all_lines = []
        with open(filepath) as f:
            for line in f.readlines():
                all_lines.append("".join(line.split("|")[1:]).strip())
        self.ftrace_dfs(["start"], all_lines, 0)


    def get_functions_nm(self, filepath: str):
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
                    self.func_file_map[parts[2]] = filemodule
                    
        except subprocess.CalledProcessError as e:
            print(f"命令执行错误: {e}")


    def filepath_dfs(self, dirpath: str):
        for root, dirs, files in os.walk(dirpath):
            for file in files:
                if not str(file).endswith(".o"):
                    continue
                filepath = os.path.join(root, file)
                self.get_functions_nm(filepath=filepath)
            for dirpath in dirs:
                self.filepath_dfs(os.path.join(root, dirpath))

    def get_functions_map(self):
        root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        for root, dirs, files in os.walk(root_dir):
            for dirname in dirs:
                if dirname not in self.white_list:
                    continue
                self.filepath_dfs(os.path.join(root, dirname))


    def generate_visual(self):
        pass

    def run(self):
        self.get_functions_map()
        self.ftrace_read()
        self.generate_visual()

class FtraceMermaid(Ftrace):
    
    def generate_visual(self):
        filepath = os.path.join(os.path.dirname(os.path.abspath(__file__)), "{}/{}_mermaid.md".format(self.resources_dirname, self.ftrace_filename))
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("```mermaid\n")
            f.write("sequenceDiagram\n")
            for line in self.func_file_modules:
                f.write("participant  " + line + "\n")
            
            for line in self.output:
                f.write(line + '\n')

            f.write("```\n")
    
    def format_print(self, tab, left, right, direction):
        src = self.func_file_map[left] if left in self.func_file_map else "default"
        dest = self.func_file_map[right] if right in self.func_file_map else "default"
        if src not in self.func_file_modules:
            self.func_file_modules.append(src)
        if dest not in self.func_file_modules:
            self.func_file_modules.append(dest)
        print_prefix = "|-" * tab
        file_prefix = "  " * tab
        if direction == Direction.CALL:
            line = "{} ->>+ {}: {}".format(src, dest, right)
        if direction == Direction.RETURN:
            line = "{} ->>- {}: ret".format(src, dest)
        if direction == Direction.STOP:
            line = "{} ->> {}: {}".format(src, dest, right)
        self.output.append(file_prefix + line)
        print(print_prefix + line)


class FtracePlantUml(Ftrace):
    
    def generate_visual(self):
        filepath = os.path.join(os.path.dirname(os.path.abspath(__file__)), "{}/{}_plantuml.puml".format(self.resources_dirname, self.ftrace_filename))
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("@startuml\n")
            
            for line in self.output:
                f.write(line + '\n')

            f.write("@enduml\n")
    
    def format_print(self, tab, left, right, direction):
        src = self.func_file_map[left] if left in self.func_file_map else "default"
        dest = self.func_file_map[right] if right in self.func_file_map else "default"
        if src not in self.func_file_modules:
            self.func_file_modules.append(src)
        if dest not in self.func_file_modules:
            self.func_file_modules.append(dest)
        print_prefix = "|-" * tab
        file_prefix = "  " * tab
        if direction == Direction.CALL or direction == Direction.STOP:
            line = "\"{}\" -> \"{}\"++: {}".format(src, dest, right)
        if direction == Direction.RETURN:
            line = "\"{}\" --> \"{}\"--: ret".format(src, dest)
        if direction == Direction.STOP:
            line = "\"{}\" -> \"{}\": {}".format(src, dest, right)
        self.output.append(file_prefix + line)
        print(print_prefix + line)


if __name__ == '__main__':
    """
    ftrace_do_sys_open
    ftrace_do_splice_read
    cat_proc_cpuinfo
    """
    for filename in ["cat_proc_pid_stat"]:
        ftrace = FtraceMermaid(filename)
        ftrace.run()