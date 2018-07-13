#encoding=utf-8

import time
import os
import subprocess
import threading
import re

from . import jd_utils as utils
from . import jp_database as db

#




def unzip_problem(md5):
	path = db.path_problems + md5 + "/"
	if len(utils.list_dir(path)) != 0:
		return
	utils.mkdir(path)
	zip_name = path + "_problem.zip"
	utils.system("cp", [db.path_files + md5, zip_name])
	utils.system("unzip", ["-o", zip_name, "-d", path], 20)

def unzip_contestant_files(taskid, md5):
	path = db.path_tasks + taskid + "/"
	utils.mkdir(path)
	zip_name = path + "_contestant.zip"
	utils.system("cp", [db.path_files + md5, zip_name])
	utils.system("unzip", ["-o", zip_name, "-d", path], 20)

# Parse the problem configs and compile
def prepare_task(task):
	taskid = task["taskid"]
	path_p = db.path_problems + task["problem_md5"] + "/"
	path_t = db.path_tasks + taskid + "/"
	# TODO support more formats
	conf_content = utils.read_file(path_p + "config.txt").split("\n")
	time_limit_ns = 0
	memory_limit_kb = 0
	for s in conf_content:
		key = s.split(" ")[0]
		value = " ".join(s.split(" ")[1:])
		if key == "time_limit":
			time_limit_ns = utils.parse_int(value)
		if key == "memory_limit":
			memory_limit_kb = utils.parse_int(value)
	language = utils.read_file(path_t + "language.txt").split("\n")[0]
	contestant_filename = "contestant.cpp"
	if language == "C":
		contestant_filename = "contestant.c"
	task["todos"].append({
		"name": "Testcase #1",
		"binary_file": path_t + "contestant.exe",
		"input_file": path_p + "input.txt",
		"answer_file": path_p + "answer.txt",
		"time_limit_ns": time_limit_ns,
		"memory_limit_kb": memory_limit_kb,
	})
	# Compile
	task["status"] = "Compiling"
	task["status_short"] = "COMP"
	cmdstr = " ".join([
		"../judge-duck-tools/compile/compile.exe",
		path_t + contestant_filename,
		path_p + "tasklib.cpp",
		path_t,
		language,
	])
	compile_output = utils.system(
		"bash",
		["-c", "LD_PRELOAD=../judge-duck-libs/libpigeon/libpigeon.so %s" % cmdstr],
		30,
	)
	compile_status = "Compile OK"
	if utils.string_get_line(compile_output, 1) != "Compile success!":
		compile_status = "Compile Error"
	task["details"].append({
		"name": "Compilation",
		"status": compile_status,
		"time_ns": "N/A",
		"mem_kb": "N/A",
		"score": "N/A",
		"detail": compile_output,
	})
	task["status"] = compile_status
	if compile_status != "Compile OK":
		task["status_short"] = "CE"
		task["compilation_result"] = "failed"
		return
	task["status_short"] = "COK"
	task["compilation_result"] = "success"


def jp_compile(task):
	unzip_problem(task["problem_md5"])
	unzip_contestant_files(task["taskid"], task["contestant_md5"])
	prepare_task(task)

def jp_compilation_thread_func():
	while True:
		time.sleep(0.2)
		task = db.do_get_pending_compile_task()
		if task == None:
			continue
		print("Found taskid=%s" % task["taskid"])
		jp_compile(task)



class myThread(threading.Thread):
	def __init__(self, name, func):
		threading.Thread.__init__(self)
		self.name = name
		self.func = func
	def run(self):
		self.func()

def start():
	mythread = myThread("jp_compilation", jp_compilation_thread_func)
	mythread.start()
