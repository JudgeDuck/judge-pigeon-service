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
	utils.system("cp", [db.path_files + md5, zip_name], 100)
	utils.system("unzip", ["-o", zip_name, "-d", path], 600)

def unzip_contestant_files(taskid, md5):
	path = db.path_tasks + taskid + "/"
	utils.mkdir(path)
	zip_name = path + "_contestant.zip"
	utils.system("cp", [db.path_files + md5, zip_name], 100)
	utils.system("unzip", ["-o", zip_name, "-d", path], 100)

def prepare_judgeduck_task(task, path_t, path_p, time_limit_ns, memory_limit_kb):
	task["todos"].append({
		"name": "Testcase #1",
		"binary_file": path_t + "contestant.exe",
		"input_file": path_p + "input.txt",
		"answer_file": path_p + "answer.txt",
		"time_limit_ns": time_limit_ns,
		"memory_limit_kb": memory_limit_kb,
		"max_score": 100,
		"try_cnt": 0,
		"detail_index": 1,
		"preferred_duck_id": 0,
	})

def prepare_uoj_task(task, path_t, path_p, time_limit_ns, memory_limit_kb):
	conf_content = utils.read_file(path_p + "problem.conf").split("\n")
	n_tests = 1
	input_pre = ""
	input_suf = ""
	output_pre = ""
	output_suf = ""
	time_limit_each = {}
	memory_limit_each = {}
	n_subtasks = 0
	subtask_end = {}
	subtask_score = {}
	for s in conf_content:
		key = s.split(" ")[0]
		value = s[len(key)+1:]
		if key == "n_tests":
			n_tests = utils.parse_int(value, 1)
		if key == "time_limit":
			time_limit_ns = utils.parse_int(value, 1) * 1000000000
		if key == "memory_limit":
			memory_limit_kb = utils.parse_int(value, 1) * 1024
		if key == "input_pre":
			input_pre = value
		if key == "input_suf":
			input_suf = value
		if key == "output_pre":
			output_pre = value
		if key == "output_suf":
			output_suf = value
		if key[:len("time_limit_")] == "time_limit_":
			case_id = utils.parse_int(key[len("time_limit_"):], -1)
			time_limit_each[case_id] = utils.parse_int(value, 1) * 1000000000
		if key[:len("memory_limit_")] == "memory_limit_":
			case_id = utils.parse_int(key[len("memory_limit_"):], -1)
			memory_limit_each[case_id] = utils.parse_int(value, 1) * 1024
		if key == "n_subtasks":
			n_subtasks = utils.parse_int(value, 0)
		if key[:len("subtask_end_")] == "subtask_end_":
			subtask_id = utils.parse_int(key[len("subtask_end_"):], -1)
			subtask_end[subtask_id] = utils.parse_int(value, -1)
		if key[:len("subtask_score_")] == "subtask_score_":
			subtask_id = utils.parse_int(key[len("subtask_score_"):], -1)
			subtask_score[subtask_id] = utils.parse_int(value, -1)
	has_valid_subtasks = True
	if n_subtasks == 0:
		has_valid_subtasks = False
	else:
		subtask_end[0] = 0
		tot_score = 0
		for i in range(1, n_subtasks + 1):
			if (not i in subtask_end) or (not i in subtask_score):
				has_valid_subtasks = False
				break
			if subtask_end[i] <= subtask_end[i - 1]:
				has_valid_subtasks = False
				break
			if subtask_end[i] > n_tests:
				has_valid_subtasks = False
				break
			if subtask_score[i] < 0:
				has_valid_subtasks = False
				break
			tot_score += subtask_score[i]
		if tot_score != 100:
			has_valid_subtasks = False
	if has_valid_subtasks:
		for stid in range(1, n_subtasks + 1):
			left = subtask_end[stid - 1] + 1
			right = subtask_end[stid]
			for i in range(left, right + 1):
				tlns = time_limit_each[i] if i in time_limit_each else time_limit_ns
				mlkb = memory_limit_each[i] if i in memory_limit_each else memory_limit_kb
				task["todos"].append({
					"name": "Subtask #%s Testcase #%s" % (stid, i),
					"binary_file": path_t + "contestant.exe",
					"input_file": path_p + "%s%s.%s" % (input_pre, i, input_suf),
					"answer_file": path_p + "%s%s.%s" % (output_pre, i, output_suf),
					"time_limit_ns": tlns,
					"memory_limit_kb": mlkb,
					"max_score": subtask_score[stid],
					"try_cnt": 0,
					"detail_index": i,
					"uoj_subtask_id": stid,
					"preferred_duck_id": i,
				})
	else:
		test_scores = {}
		for i in range(1, n_tests + 1): test_scores[i] = 0
		cur = 0
		for i in range(100):
			cur += 1
			if cur > n_tests: cur = 1
			test_scores[cur] += 1
		for i in range(1, n_tests + 1):
			tlns = time_limit_each[i] if i in time_limit_each else time_limit_ns
			mlkb = memory_limit_each[i] if i in memory_limit_each else memory_limit_kb
			task["todos"].append({
				"name": "Testcase #%s" % i,
				"binary_file": path_t + "contestant.exe",
				"input_file": path_p + "%s%s.%s" % (input_pre, i, input_suf),
				"answer_file": path_p + "%s%s.%s" % (output_pre, i, output_suf),
				"time_limit_ns": tlns,
				"memory_limit_kb": mlkb,
				"max_score": test_scores[i],
				"try_cnt": 0,
				"detail_index": i,
				"uoj_subtask_id": 0,
				"preferred_duck_id": 0,
			})

# Parse the problem configs and compile
def prepare_task(task):
	taskid = task["taskid"]
	path_p = db.path_problems + task["problem_md5"] + "/"
	path_t = db.path_tasks + taskid + "/"
	
	conf_content = utils.read_file(path_p + "config.txt").split("\n")
	time_limit_ns = 0
	memory_limit_kb = 0
	data_type = ""
	
	for s in conf_content:
		key = s.split(" ")[0]
		value = " ".join(s.split(" ")[1:])
		if key == "time_limit":
			time_limit_ns = utils.parse_int(value)
		if key == "memory_limit":
			memory_limit_kb = utils.parse_int(value)
		if key == "data_type":
			data_type = value
	
	language = utils.read_file(path_t + "language.txt").split("\n")[0]
	contestant_filename = "contestant.cpp"
	if language == "C":
		contestant_filename = "contestant.c"
	
	if data_type == "":
		prepare_judgeduck_task(task, path_t, path_p, time_limit_ns, memory_limit_kb)
	elif data_type == "UOJ":
		prepare_uoj_task(task, path_t, path_p, time_limit_ns, memory_limit_kb)
	else:
		task["status"] = "Judge Failed"
		task["status_short"] = ""
		task["compilation_result"] = "failed"
		task["has_completed"] = "true"
		return
	
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
		"detail_index": 0,
	})
	task["status"] = compile_status
	if compile_status != "Compile OK":
		task["status_short"] = "CE"
		task["compilation_result"] = "failed"
		task["has_completed"] = "true"
		return
	task["status_short"] = "COK"
	task["compilation_result"] = "success"


def jp_compile(task):
	#unzip_problem(task["problem_md5"])
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
