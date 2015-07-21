import argparse
from subprocess import Popen
import math
import time
import os

def start_processes_on_files(scriptpath, indir, triggerfile, files, files_per_process = 5):
    total_process_num = int(math.ceil(len(files) / float(files_per_process)))
    processes = {}
    for p_num in range(0, total_process_num):
        process = Popen([
            scriptpath,
            indir,
            triggerfile,
            "--start-split",
            str(p_num * files_per_process),
            "--splitn",
            str(files_per_process),
            "--pid",
            str(p_num),
            "--no-ui"])
        processes[p_num] = process

    return processes

def wait_for_processes(processes):
    original_process_count = len(processes)
    while len(processes) > 0:
        to_remove = []
        for pid, process in processes.items():
            retcode = process.poll()
            if retcode is None:
                continue
            else:
                to_remove.append(pid)
                break
        for pid in to_remove:
            print "Process {0} finished".format(pid)
            del processes[pid]
        time.sleep(0.5)

def collect_files(original_process_count):
    with open("candidates.ltmp", "w") as f_candidates:
        for pid in range(0, original_process_count):
            with open("candidates{0}.ltmp".format(pid)) as f:
                contents = f.read()
                f_candidates.write(contents)

    with open("events.ltmp", "w") as f_events:
        for pid in range(0, original_process_count):
            with open("events{0}.ltmp".format(pid)) as f:
                contents = f.read()
                f_events.write(contents)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="")
    parser.add_argument("scriptpath")
    parser.add_argument("indir")
    parser.add_argument("triggerfile")
    parser.add_argument("--collect", target = "collect_only", action = "store_true")
    parser.defaults(collect_only = False)

    args = parser.parse_args()

    if not args.collect_only:
        processes = start_processes_on_files(args.scriptpath, args.indir, args.triggerfile, os.listdir(args.indir))
        original_process_count = len(processes)
        wait_for_processes(processes)
    collect_files(original_process_count)

    print "Done"

