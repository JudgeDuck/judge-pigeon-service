#encoding=utf-8

import time
import os
import subprocess
import threading
import re

from . import jd_utils as utils
from . import jp_database as db


def jp_duck_thread_func(self):
	while True:
		time.sleep(0.1)
		if not self.has_task:
			continue
		self.has_result = False
		print("%s: found task with TL %s, ML %s" %
			(self.args["name"], self.args["time_ns"], self.args["mem_kb"])
		)
		run_output = utils.system(
			"../judge-duck-tools/run/run.exe",
			[
				self.ip,
				"%s" % self.local_port,
				self.args["input_file"],
				self.args["answer_file"],
				self.args["binary_file"],
				"%s" % self.args["time_ns"],
				"%s" % self.args["mem_kb"],
			],
			30,
		)
		arr = run_output.split("\n")
		has_correct_answer = False
		has_run_finished = False
		time_ms = None
		mem_kb = None
		verdict = "Judge Failed"
		status = ""
		score = 0
		for s in arr:
			if s == "Correct Answer":
				has_correct_answer = True
			if s[:len("verdict = ")] == "verdict = ":
				verdict = s[len("verdict = "):]
			if s == "verdict = Run Finished":
				has_run_finished = True
			if s.find("time_ms = ") != -1:
				time_ms = utils.parse_float(s[len("time_ms = "):], None)
			if s.find("mem_kb = ") != -1:
				mem_kb = utils.parse_int(s[len("mem_kb = "):], None)
		if has_run_finished:
			if has_correct_answer:
				status = "Accepted"
				score = self.args["max_score"]
			else:
				status = "Wrong Answer"
		else:
			status = verdict
		time_ns = None
		if time_ms != None:
			time_ns = int(time_ms * 1e6)
		self.result = {
			"name": self.args["name"],
			"status": status,
			"time_ns": time_ns,
			"mem_kb": mem_kb,
			"detail": run_output,
			"score": score,
		}
		self.has_result = True
		self.has_task = False



class Duck(threading.Thread):
	def __init__(self, name, func, ip, local_port):
		threading.Thread.__init__(self)
		self.name = name
		self.func = func
		self.ip = ip
		self.local_port = local_port
		self.has_task = False
		self.has_result = False
	def run(self):
		self.func(self)

def start_duck(name, ip, local_port):
	duck = Duck(name, jp_duck_thread_func, ip, local_port)
	duck.start()
	return duck
