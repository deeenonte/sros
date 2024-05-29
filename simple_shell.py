import os
import shlex
import subprocess
import random
import time
from collections import deque

# Process class for scheduling and memory management
class Process:
    def __init__(self, pid, size):
        self.pid = pid
        self.size = size
        self.pages = []
        self.remaining_time = size  # Added to track remaining execution time

    def __str__(self):
        return f"PID: {self.pid}, Size: {self.size}, Pages: {self.pages}"

# Memory class to represent physical memory and paging
class Memory:
    def __init__(self, size, page_size):
        self.size = size
        self.page_size = page_size
        self.pages = [None] * (size // page_size)

    def allocate(self, process):
        needed_pages = (process.size + self.page_size - 1) // self.page_size
        free_pages = [i for i, page in enumerate(self.pages) if page is None]
        if len(free_pages) < needed_pages:
            print(f"Not enough memory to allocate process {process.pid}")
            return False

        for i in range(needed_pages):
            self.pages[free_pages[i]] = process.pid
            process.pages.append(free_pages[i])
        print(f"Allocated process {process.pid} to memory: {process.pages}")
        return True

    def deallocate(self, pid):
        for i, page in enumerate(self.pages):
            if page == pid:
                self.pages[i] = None
        print(f"Deallocated process {pid} from memory")

    def display_memory(self):
        memory_view = ''.join(['.' if page is None else str(page) for page in self.pages])
        print(f"Memory: {memory_view}")

# MemoryManager class to handle memory operations
class MemoryManager:
    def __init__(self, memory_size, page_size):
        self.memory = Memory(memory_size, page_size)
        self.processes = {}

    def add_process(self, pid, size):
        if pid in self.processes:
            print(f"Process {pid} already exists.")
            return
        new_process = Process(pid, size)
        if self.memory.allocate(new_process):
            self.processes[pid] = new_process

    def remove_process(self, pid):
        if pid not in self.processes:
            print(f"No such process: {pid}")
            return
        self.memory.deallocate(pid)
        del self.processes[pid]

    def display_memory(self):
        self.memory.display_memory()

    def display_processes(self):
        for pid, process in self.processes.items():
            print(process)

# Scheduler class for process scheduling
class Scheduler:
    def __init__(self, processes, quantum=1):
        self.processes = sorted(processes, key=lambda x: x.pid)  # Sort by process ID for simplicity
        self.time = 0
        self.quantum = quantum  # For Round Robin
        self.completed_processes = []
        self.ready_queue = deque()

    def fcfs(self):
        print("Running FCFS Scheduling...")
        while self.processes or self.ready_queue:
            self._add_to_ready_queue()
            if self.ready_queue:
                current_process = self.ready_queue.popleft()
                self.time = max(self.time, current_process.pid)  # Using PID as arrival time for simplicity
                current_process.start_time = self.time
                self.time += current_process.size  # Using size as burst time for simplicity
                current_process.completion_time = self.time
                self.completed_processes.append(current_process)
            else:
                self.time += 1

    def sjn(self):
        print("Running SJN Scheduling...")
        while self.processes or self.ready_queue:
            self._add_to_ready_queue()
            if self.ready_queue:
                current_process = min(self.ready_queue, key=lambda x: x.size)
                self.ready_queue.remove(current_process)
                self.time = max(self.time, current_process.pid)
                current_process.start_time = self.time
                self.time += current_process.size
                current_process.completion_time = self.time
                self.completed_processes.append(current_process)
            else:
                self.time += 1

    def round_robin(self):
        print("Running Round Robin Scheduling...")
        while self.processes or self.ready_queue:
            self._add_to_ready_queue()
            if self.ready_queue:
                current_process = self.ready_queue.popleft()
                self.time = max(self.time, current_process.pid)
                if current_process.start_time is None:
                    current_process.start_time = self.time
                if current_process.remaining_time <= self.quantum:
                    self.time += current_process.remaining_time
                    current_process.remaining_time = 0
                    current_process.completion_time = self.time
                    self.completed_processes.append(current_process)
                else:
                    self.time += self.quantum
                    current_process.remaining_time -= self.quantum
                    self.ready_queue.append(current_process)
            else:
                self.time += 1

    def _add_to_ready_queue(self):
        while self.processes and self.processes[0].pid <= self.time:
            self.ready_queue.append(self.processes.pop(0))

    def print_results(self):
        print("PID\tSize\tStart\tCompletion")
        for process in self.completed_processes:
            print(f"{process.pid}\t{process.size}\t{process.start_time}\t{process.completion_time}")

# Directory and File classes for file system simulation
class File:
    def __init__(self, name, content=''):
        self.name = name
        self.content = content

    def __str__(self):
        return self.name

class Directory:
    def __init__(self, name):
        self.name = name
        self.children = {}

    def add_child(self, child):
        self.children[child.name] = child

    def remove_child(self, name):
        if name in self.children:
            del self.children[name]

    def get_child(self, name):
        return self.children.get(name)

    def list_children(self):
        return self.children.values()

    def __str__(self):
        return self.name

# FileSystem class to handle file system operations
class FileSystem:
    def __init__(self):
        self.root = Directory('/')
        self.current_directory = self.root

    def create_file(self, name, content=''):
        if name in self.current_directory.children:
            print(f"File or directory '{name}' already exists.")
        else:
            new_file = File(name, content)
            self.current_directory.add_child(new_file)

    def create_directory(self, name):
        if name in self.current_directory.children:
            print(f"File or directory '{name}' already exists.")
        else:
            new_dir = Directory(name)
            self.current_directory.add_child(new_dir)

    def delete(self, name):
        if name in self.current_directory.children:
            self.current_directory.remove_child(name)
        else:
            print(f"No such file or directory: '{name}'")

    def change_directory(self, path):
        if path == '/':
            self.current_directory = self.root
        elif path == '..':
            if self.current_directory.name != '/':
                parent_path = self.current_directory.name.rsplit('/', 1)[0]
                self.current_directory = self.root.get_child(parent_path)
        else:
            target = self.current_directory.get_child(path)
            if isinstance(target, Directory):
                self.current_directory = target
            else:
                print(f"'{path}' is not a directory")

    def list_directory(self):
        for child in self.current_directory.list_children():
            print(child)

    def read_file(self, name):
        target = self.current_directory.get_child(name)
        if isinstance(target, File):
            print(target.content)
        else:
            print(f"'{name}' is not a file")

    def write_file(self, name, content):
        target = self.current_directory.get_child(name)
        if isinstance(target, File):
            target.content = content
        else:
            print(f"'{name}' is not a file")

    def print_working_directory(self):
        print(self.current_directory.name)

# New Process class for rock concert themed memory management
class RockProcess:
    def __init__(self, name, size, duration):
        self.name = name
        self.size = size
        self.duration = duration
        self.status = "waiting"

    def run(self):
        self.status = "running"
        print(f"Running process: {self.name} ({self.size}MB)")
        time.sleep(self.duration)
        self.status = "completed"
        print(f"Process {self.name} completed")

# New MemoryManager class for rock concert themed memory management
class RockMemoryManager:
    def __init__(self, capacity):
        self.capacity = capacity
        self.used = 0
        self.memory_map = {}

    def allocate(self, size, process_name):
        if self.used + size <= self.capacity:
            self.used += size
            self.memory_map[process_name] = size
            return True
        return False

    def free(self, process_name):
        size = self.memory_map.pop(process_name, 0)
        self.used -= size

# OSKernel class for managing rock concert themed processes
class OSKernel:
    def __init__(self):
        self.processes = []
        self.memory_manager = RockMemoryManager(1024)  # 1GB of memory
        self.bands = ["Guns and Roses", "AC/DC", "Metallica", "Oasis", "Kiss", "Pantera",
                      "Rolling Stones", "The Doors", "Nirvana", "Limp Bizkit", "Green Day"]

    def create_process(self):
        band = random.choice(self.bands)
        size = random.randint(50, 300)  # Random memory size between 50MB and 300MB
        duration = random.uniform(1, 3)  # Random duration between 1 and 3 seconds
        if self.memory_manager.allocate(size, band):
            process = RockProcess(band, size, duration)
            self.processes.append(process)
            print(f"Process '{band}' created with size {size}MB and will run for {duration:.2f} seconds.")
        else:
            print("Memory allocation failed. Try freeing up memory.")

    def run_processes(self):
        while self.processes:
            for process in list(self.processes):
                if process.status == "waiting":
                    process.run()
                    self.memory_manager.free(process.name)
                    self.processes.remove(process)

# Shell functionality
history = []
fs = FileSystem()
mm = MemoryManager(memory_size=100, page_size=10)
kernel = OSKernel()

def execute_command(command_parts):
    if command_parts[0] == 'cd':
        fs.change_directory(command_parts[1] if len(command_parts) > 1 else '/')
    elif command_parts[0] == 'mkdir':
        fs.create_directory(command_parts[1])
    elif command_parts[0] == 'touch':
        fs.create_file(command_parts[1])
    elif command_parts[0] == 'rm':
        fs.delete(command_parts[1])
    elif command_parts[0] == 'ls':
        fs.list_directory()
    elif command_parts[0] == 'pwd':
        fs.print_working_directory()
    elif command_parts[0] == 'cat':
        fs.read_file(command_parts[1])
    elif command_parts[0] == 'echo':
        content = ' '.join(command_parts[2:])
        fs.write_file(command_parts[1], content)
    elif command_parts[0] == 'history':
        for i, cmd in enumerate(history):
            print(f"{i}: {cmd}")
    elif command_parts[0] == 'fcfs':
        run_scheduler('fcfs')
    elif command_parts[0] == 'sjn':
        run_scheduler('sjn')
    elif command_parts[0] == 'rr':
        quantum = 1
        if len(command_parts) > 1:
            quantum = int(command_parts[1])
        run_scheduler('rr', quantum)
    elif command_parts[0] == 'alloc':
        if len(command_parts) < 3:
            print("Usage: alloc <pid> <size>")
        else:
            pid = int(command_parts[1])
            size = int(command_parts[2])
            mm.add_process(pid, size)
    elif command_parts[0] == 'dealloc':
        if len(command_parts) < 2:
            print("Usage: dealloc <pid>")
        else:
            pid = int(command_parts[1])
            mm.remove_process(pid)
    elif command_parts[0] == 'mem':
        mm.display_memory()
    elif command_parts[0] == 'procs':
        mm.display_processes()
    elif command_parts[0] == 'new':
        kernel.create_process()
    elif command_parts[0] == 'run':
        kernel.run_processes()
    elif command_parts[0] == 'help':
        display_help()
    elif command_parts[0] == 'exit':
        print("Exiting shell...")
        return False
    else:
        print(f"Unknown command: {command_parts[0]}")
    return True

def run_scheduler(algorithm, quantum=1):
    processes = [
        Process(1, 10),
        Process(2, 5),
        Process(3, 2),
        Process(4, 8),
        Process(5, 4)
    ]

    scheduler = Scheduler(processes.copy(), quantum)
    if algorithm == 'fcfs':
        scheduler.fcfs()
    elif algorithm == 'sjn':
        scheduler.sjn()
    elif algorithm == 'rr':
        scheduler.round_robin()

    scheduler.print_results()

def display_help():
    print("""
Available commands:
  cd <directory>       - Change directory
  mkdir <name>         - Create a directory
  touch <name>         - Create a file
  rm <name>            - Remove a file or directory
  ls                   - List directory contents
  pwd                  - Print working directory
  cat <file>           - Read a file
  echo <file> <text>   - Write text to a file
  history              - Show command history
  fcfs                 - Run FCFS scheduling
  sjn                  - Run SJN scheduling
  rr <quantum>         - Run Round Robin scheduling
  alloc <pid> <size>   - Allocate memory to a process
  dealloc <pid>        - Deallocate memory from a process
  mem                  - Display memory usage
  procs                - Display process information
  new                  - Create a new rock concert themed process
  run                  - Run all created processes
  help                 - Display this help message
  exit                 - Exit the shell
""")

def shell():
    while True:
        try:
            command = input("my_shell> ")
        except EOFError:
            break

        history.append(command)
        command_parts = shlex.split(command)
        if not execute_command(command_parts):
            break

if __name__ == "__main__":
    shell()
