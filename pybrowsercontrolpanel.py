# line 570 (572)

from time import time
from enum import Enum
from contextlib import redirect_stdout

from flask import Flask, redirect, url_for, request, render_template, render_template_string, send_from_directory, Response, session
from flask_login import LoginManager, UserMixin, login_user
from wtforms import Form, PasswordField, StringField, validators
from subprocess import check_output
from glob import glob
from os import path, mkdir, chdir, getcwd
from sys import path as module_path
from time import sleep, time
from jinja2 import Template
from importlib import import_module
from importlib import reload as reload_module
from traceback import format_exc
from html import escape as html_escape
from collections.abc import Iterable
from collections import deque
import json
import threading
import inspect
from pathvalidate import is_valid_filename
import platform

import default_obj_templates

cwd = getcwd()

class Logger:

	class LogMessage:
		def __init__(self, msg, time, number):
			self.msg = msg
			self.time = time
			self.number = number

	def __init__(self, page):
		self.page = page
		self.logs = deque() # doubly linked list
		self.version = 0

	def write(self, msg):

		self.version += 1
		self.logs.appendleft(self.LogMessage(msg, time(), self.version))
		# self.page.update_log()

	def flush():
		pass

	def get_logs_after(self, number):

		output = ""
		# logs stored with newest first
		for log_msg in self.logs:
			if log_msg.number <= number:
				break
			output = log_msg.msg + output

		return output






PageObjectEnum = Enum("PageObjectEnum", "function output file_list toggle input")

class Page:

	class PageObject:
		#TODO maybe change this so there is only a send_dict? idk it's a bit of a pain having to update the version in two places
		def __init__(self, kind, args_dict, private_args_dict, ref):
			self.kind = kind
			self.args = args_dict
			self.prargs = private_args_dict
			self.ref = ref
			self.evaluated = {}

			# if kind in [PageObjectEnum.output, PageObjectEnum.file_list, PageObjectEnum.toggle]:
			# 	self.args["evaluated"] = self.evaluated

			self.version = 0
			# self.version = 0 # increasing this number makes the browser reload the object (done when Page.update_ref called)
			self.send_dict = {
				"kind": self.kind.name,
				"ref": self.ref,
				"version": 0,
				"args": self.args
			}

	def __init__(self, name, path):
		# self.folder = ""

		if type(name) is not str:
			raise ValueError("name not string")
		if set(name.lower()) > set("qwertyuioplkjhgfdsazxcvbnm1234567890_"):
			raise ValueError("name needs to be only upper/lower case letters, numbers and underscores")

		if path == "" or path[0] != "/":
			path = "/" + path


		self.name = name
		self.path = path

		self.title = ""
		self.description = ""
		self.setup = ""
		self.default_access = True
		self.html_template = ""

		self.default_output_template = default_obj_templates.output
		self.default_toggle_template = default_obj_templates.toggle
		self.default_input_template = default_obj_templates.input

		# no checks on this - might as well just wait for it to crash when the server starts
		# TODO
		self.main_thread_target = None
		self._main_thread = None


		self._page_objects = []
		self._page_object_args = []

		self._checks_on_server_start = []

		self._folders = [] # contains dicts
		self._logger = Logger(self)
		self._json = None

		self._html = None
		self._is_set_up = False


	def _ref_checker(self, ref, default):
		if ref == "":
			if "<" in default:
				raise TypeError("page object requires a ref value (cannot be inferred from a lambda function)")
			ref = default

		if ref in [x.ref for x in self._page_objects]:
			raise ValueError("page reference " + ref + " already exists in the page")

		return ref


	def set_title(self, title):

		if type(title) is not str:
			raise ValueError("title not string")

		self.title = title

	def set_description(self, description):

		if type(description) is not str:
			raise ValueError("description not string")

		self.description = description.replace("\n", "")

	def set_setup(self, setup):

		if type(setup) is not str:
			raise ValueError("setup not string")

		self.setup = setup.replace("\n", "")

	def _page_object_function_director(self, page_obj, prarg_key, function_before_appending=lambda: None):
		# checks if the function is present. also gets the ref, checks for errors, adds the function, adds a check, a lot of stuff tbh
		# returns a decorator, or the orignal function in case if it was called with only the function (so could have been called as a decorator with no args)

		# saves writing this out a bajillion times
		args_dict = page_obj.args
		private_args_dict = page_obj.prargs

		if callable(private_args_dict[prarg_key]):
			page_obj.ref = self._ref_checker(page_obj.ref, private_args_dict[prarg_key].__name__)
			page_obj.send_dict["ref"] = page_obj.ref
			function_before_appending()
			self._page_objects.append(page_obj)
			# could have been called as a decorator with no args - so return original function
			return private_args_dict[prarg_key]
		if private_args_dict[prarg_key] is not None:
			raise TypeError(f"{prarg_key} is not callable")
		# no function but other args specified. check at server launch that the decorator got a function
		info = inspect.getframeinfo(inspect.stack()[2][0])
		def check():
			# check that a function was passed to the decorator on server start
			if private_args_dict[prarg_key] is None:
				raise TypeError(f"{page_obj.kind.name} with no {prarg_key} specified, or not called as a decorator (file {info.filename}, line {info.lineno}, in {info.function})")
			# the decorator checks if it is a valid function when added
		self._checks_on_server_start.append(check)
		def decorator(fn):
			if not callable(fn):
				raise TypeError(f"{repr(fn)} is not a callable {prarg_key}")
			private_args_dict[prarg_key] = fn
			page_obj.ref = self._ref_checker(page_obj.ref, fn.__name__)
			page_obj.send_dict["ref"] = page_obj.ref
			function_before_appending()
			self._page_objects.append(page_obj)
			return fn
		return decorator


	def add_output(self, *args, **kwargs):
		args_dict = args_kwargs_checker(args, kwargs, function=None, title="", ref="", escape=True, access=self.default_access)
		exception = type_checker(args_dict, ref=str, escape=bool, access=bool)
		if exception is not None: raise exception
		prargs_dict = separate_dict(args_dict, ["function"])
		page_obj = self.PageObject(PageObjectEnum.output, args_dict, prargs_dict, args_dict.pop("ref"))
		return self._page_object_function_director(page_obj, "function")


	# TODO maybe remove this
	def add_toggle(self, *args, **kwargs):
		args_dict = args_kwargs_checker(args, kwargs, setter=None, getter=None, title="", ref=None, escape=True, view_access=self.default_access, toggle_access=self.default_access)
		exception = type_checker(args_dict, getter=callable, ref=str, escape=bool, view_access=bool, toggle_access=bool)
		if exception is not None: raise exception
		prargs_dict = separate_dict(args_dict, ["setter", "getter"])
		page_obj = self.PageObject(PageObjectEnum.toggle, args_dict, prargs_dict, args_dict.pop("ref"))
		return self._page_object_function_director(page_obj, "setter")


	def add_input(self, *args, **kwargs):
		args_dict = args_kwargs_checker(args, kwargs, function=None, title="", number_of_arguments=-1, field_titles=[], ref="", escape=True, access=self.default_access)
		exception = type_checker(args_dict, ref=str, field_titles=list_of(str), number_of_arguments=int, escape=bool, access=bool)
		if exception is not None: raise exception
		if args_dict["number_of_arguments"] < -1:
			raise ValueError("the number_of_arguments specified for this function is invalid (leave unspecified / set to -1 to auto-detect)")
		prargs_dict = separate_dict(args_dict, ["function"])
		page_obj = self.PageObject(PageObjectEnum.input, args_dict, prargs_dict, args_dict.pop("ref"))

		def get_field_titles():

			sig = inspect.signature(prargs_dict["function"])
			keys = [str(i) for i in sig.parameters.values()]
			count = 2
			args_name = None
			for i in range(len(keys)-1, -1, -1):
				key = keys[i]
				if key[0] == "*":
					if key[1] != "*":
						args_name = key[2:]
						# *args is specified
					keys.pop(i)
				count -= 1
				if count == 0: break

			# detect number of arguments
			if args_dict["number_of_arguments"] == -1:
				if args_name is not None: # infinite arguments possible
					args_dict["number_of_arguments"] = max([len(keys), len(field_titles)])
				else:
					args_dict["number_of_arguments"] = len(keys)
			else:
				if args_dict["number_of_arguments"] < len(keys):
					raise ValueError(f"key number_of_arguments is less than the minimum of positional arguments for this function ({len(keys)})")
				if args_name is None and args_dict["number_of_arguments"] != len(keys):
					raise ValueError(f"key number_of_arguments is different to the number of positional arguments for this function ({len(keys)}). Maybe just leave this field blank and let me do the work for you if you're not specifying *args :)")

			# trims field_titles to correct number
			args_dict["field_titles"] = args_dict["field_titles"][:args_dict["number_of_arguments"]]

			# add the function field titles if they weren't specified in field_titles=[...]
			for i in range(len(args_dict["field_titles"]), args_dict["number_of_arguments"]):
				if i > len(keys):
					args_dict["field_titles"].append(args_name)
				else:
					args_dict["field_titles"].append(keys[i])

			if args_dict["title"] == "":
				args_dict["title"] = page_obj.ref


		# call with above function to be run just before the page_object is added to the list
		return self._page_object_function_director(page_obj, "function", function_before_appending=get_field_titles)


	def set_default_access(self, access):
		if type(access) is not bool:
			raise TypeError("access must be True (for all) or False (requires login)")
		self.default_access = access


	# def _create_json(self):
	# 	self._json = {
	# 		"objects": [obj.send_dict for obj in self._page_objects],
	# 		"log": {
	# 			"version": 0,
	# 			"log": "",
	# 			"updated": False
	# 		}
	# 	}
	# 	self.update_all()

	def _get_json(self):
		return json.dumps({
			"objects" : [
				{
					"version": obj.version,
					"evaluated": obj.evaluated,
					"kind": obj.kind.name,
					"ref": obj.ref,
					"escape": obj.args["escape"]
				}
				for obj in self._page_objects
			],
			"log": {
				"version": self._logger.version,
				"log": "",
				"updated": False
			}
		})



	def update_all(self):

		for obj in self._page_objects:
			self._update_obj(obj)

		# self.update_log()

	def update_ref(self, ref):
		o = self._get_object_of_ref(ref)
		if o is None:
			raise ValueError(f"ref {ref} not found")
		self._update_obj(o)

	# def update_log(self):
	# 	self._json["log"]["version"] = self._logger.version

	def _get_object_of_ref(self, ref):
		for o in self._page_objects:
			if o.ref == ref:
				return o

	def _update_obj(self, obj):

		old_evaluated = obj.evaluated.copy()

		if obj.kind == PageObjectEnum.output:
			try:
				obj.evaluated = {"value": obj.prargs["function"]()}
			except Exception as e:
				obj.evaluated = {"error": str(e)}

		elif obj.kind == PageObjectEnum.toggle:
			try:
				obj.evaluated = {"value": obj.prargs["getter"]()}
			except Exception as e:
				obj.evaluated = {"error": str(e)}

		elif obj.kind == PageObjectEnum.file_list:
			try:
				files_in_folder = []
				for path in sorted(glob("files/" + proj.name + "/" + obj.args["folder"] + "/*")):

					if platform.system() == "Windows":
						filename = path.split("\\")[-1]
					else:
						filename = path.split("/")[-1]

					files_in_folder.append(filename)

				obj.evaluated = {"value": files_in_folder}
			except Exception as e:
				obj.evaluated = {"error": str(e)}

		else:
			return

		if obj.evaluated != old_evaluated:
			obj.version += 1
			obj.send_dict["version"] = obj.version




		# old_evaluated = None
		# if "evaluated" in obj.args:
		# 	old_evaluated = obj.args["evaluated"].copy()
		#
		# if obj.kind == PageObjectEnum.output:
		# 	try:
		# 		obj.args["evaluated"] = {"value": obj.prargs["function"]()}
		# 	except Exception as e:
		# 		obj.args["evaluated"] = {"error": str(e)}
		#
		# elif obj.kind == PageObjectEnum.toggle:
		# 	try:
		# 		obj.args["evaluated"] = {"value": obj.prargs["getter"]()}
		# 	except Exception as e:
		# 		obj.args["evaluated"] = {"error": str(e)}
		#
		# elif obj.kind == PageObjectEnum.file_list:
		# 	try:
		# 		files_in_folder = []
		# 		for path in sorted(glob("files/" + proj.name + "/" + obj.args["folder"] + "/*")):
		#
		# 			if platform.system() == "Windows":
		# 				filename = path.split("\\")[-1]
		# 			else:
		# 				filename = path.split("/")[-1]
		#
		# 			files_in_folder.append(filename)
		#
		# 		obj.args["evaluated"] = {"value": files_in_folder}
		# 	except Exception as e:
		# 		obj.args["evaluated"] = {"error": str(e)}
		#
		# else:
		# 	return


		# # don't bother updating users if nothing has changed
		# if obj.args["evaluated"] != old_evaluated:
		# 	obj.send_dict["version"] += 1


	def _gather_update_data(self, versions, log_version):

		object_data_to_send = []
		for i in range(0, len(self._page_objects)):
			if self._page_objects[i].send_dict["version"] > versions[i]:
				# objects needs updating
				object_data_to_send.append({
					"index": i,
					"version": self._page_objects[i].version,
					"evaluated": self._page_objects[i].evaluated
				})
				# versions[i] = self._page_objects[i].version
		return {
			"objects": object_data_to_send,
			"log": {
				"version": self._logger.version,
				"log": self._logger.get_logs_after(log_version),
				"updated": self._logger.version > log_version
			}
		}

	def _html_code_of_ref(self, ref, template=None):
		test_result = _exception_from_test(ref, str)
		if test_result is not None:
			raise type(test_result)(f"failed to get ref in html_template of page {self.name} ({self.path}) Reason: {str(test_result)}")

		obj = self._get_object_of_ref(ref)
		if obj is None:
			raise ValueError(f"ref {repr(ref)} not found in page {self.name} ({self.path})")
		pass

		if template is None:
			if obj.kind == PageObjectEnum.output:
				template = self.default_output_template
			elif obj.kind == PageObjectEnum.input:
				template = self.default_input_template
			elif obj.kind == PageObjectEnum.toggle:
				template = self.default_toggle_template

		return render_template_string(template,
			args = obj.args,
			ref = ref
		)

	# route requests for this page to this function - only works when flask server is running due to request.method functions etc
	def get_request_handler(self):
		for check in self._checks_on_server_start:
			check()
		return self._request_handler

	def _request_handler(page):

		if request.method == "GET":

			if "what" in request.args:
				if request.args["what"] == "json":

					return js_rsp(page._get_json())

				# elif request.args["what"] == "update":
				# 	# only send data for objects that have been updated since the browser last updated them
				# 	return js_rsp(json.dumps(page._gather_update_data()))

			return page._html


		# request.form["action"] possibilities:   "input", "set_bool", "function"
		elif request.method == "POST":

			# make sure all incoming values are strings.
			post_args = {key: str(value) for (key, value) in request.form.items()}

			print(post_args)

			if not {"action", "ref"} <= set(post_args.keys()):
				return ' {"request_exception": "Malformed request: requires action and ref"} '

			# what update data should be sent. the function is called *AFTER* the actual operation
			def get_update_data_function():
				if not {"obj_versions", "log_version"} <= set(post_args.keys()):
					return lambda: "obj_versions and log_version not specified"

				try:
					post_args["obj_versions"] = json.loads(post_args["obj_versions"])
				except: pass

				test_result = _exception_from_test(post_args["obj_versions"], (list_of(int), has_length(len(page._page_objects))))
				if test_result is not None: return lambda: "malformed obj_versions array: " + str(test_result)


				try:
					post_args["log_version"] = int(post_args["log_version"])
					return lambda: page._gather_update_data(post_args["obj_versions"], post_args["log_version"]) # <---------- passed tests
				except:
					return lambda: "unable to convert log_version to an integer"

			# update_data is itself a function that is called after stuff
			update_data = get_update_data_function()



			# find the PageObject referenced
			page_obj = None
			for i in page._page_objects:
				if i.ref == post_args["ref"]:
					page_obj = i
					break
			if page_obj is None:
				return ' {"request_exception": "ref not found"} '


			if page_obj.kind == PageObjectEnum.input:
				if post_args["action"] == "button":

					if "field_values" not in post_args:
						return ' {"request_exception": "input button request has no field_values"} '

					try:
						with redirect_stdout(page._logger):
							function_output = page_obj.prargs["function"](*json.loads(post_args["field_values"]))
						return json.dumps({"value": str(function_output), "update": update_data()})
					except Exception as e:
						if isinstance(e, UserException):
							return json.dumps({"user_exception": str(e), "update": update_data()})
						print(format_exc()) # print the error message
						return json.dumps({"error": "An error occurred. You may wish to contact your network administrator."})

				else:
					return ' {"request_exception": "'+post_args["action"]+' is not a valid action"} '

			elif page_obj.kind == PageObjectEnum.function:
				if post_args["action"] == "button":

					try:
						with redirect_stdout(page._logger):
							function_output = page_obj.prargs["function"]()
						return json.dumps({"value": str(function_output), "update": update_data()})
					except Exception as e:
						if isinstance(e, UserException):
							return json.dumps({"user_exception": str(e), "update": update_data()})
						print(format_exc())
						return json.dumps({"error": "An error occurred. You may wish to contact your network administrator."})

				else:
					return ' {"request_exception": "'+post_args["action"]+' is not a valid action"} '

			elif page_obj.kind == PageObjectEnum.toggle:
				if post_args["action"] == "set":

					if "value" not in post_args:
						return ' {"request_exception": "toggle set contains no value" } '

					if post_args["value"] not in ["True", "False", "true", "false", "0", "1"]:
						return ' {"request_exception": "toggle set value not a boolean"} '

					val = post_args["value"] in ["True", "true", "1"]

					try:
						with redirect_stdout(page._logger):
							page_obj.prargs["setter"](val)
						return json.dumps({"value": val, "update": update_data()})
					except Exception as e:
						if isinstance(e, UserException):
							return json.dumps({"user_exception": str(e), "update": update_data()})
						print(format_exc())
						return json.dumps({"error": "An error occurred. You may wish to contact your network administrator."})

				else:
					return ' {"request_exception": "'+post_args["action"]+' is not a valid action"} '




class Server:


	def __init__(self):


		self.pages = []
		# self._homepage_html = None
		self.app = Flask(__name__)

		app = self.app



		# render html pages. needs to be inside an app.<> statement because otherwise render_template doesn't work
		@app.before_first_request
		def render_html_pages():
			print("rendering pages")
			# ip = check_output('hostname -I', shell=True).decode("utf-8")
			ip = "fix this Tom"
			for page in self.pages:
				# page._create_json()

				def ref(ref, template=None):
					return page._html_code_of_ref(ref, template)

				print(f"Filling in HTML template of page {page.name} ({page.path})")
				page._html = render_template_string(page.html_template,
					title = page.title,
					name = page.name,
					description = page.description,
					setup = page.setup,
					page_objects = page._page_objects,
					PageObject = PageObjectEnum,
					ip = ip,
					ref = page._html_code_of_ref #function

				)
			# self._homepage_html = render_template_string('homepage.html',
			# 	pages = self.pages,
			# 	ip = ip
			# )


		# @app.template_filter("wrap")
		# def wrap(list):
		# 	return ['"' + i + '"' for i in list]

		# @app.route("/favicon.ico")
		# def favicon():
		# 	return send_from_directory("static", "images/raspiicon.png")




	def run(self):


		# for page in self.pages:
		# 	if not isinstance(page, Page):
		# 		raise RuntimeError(f"Server.pages contains non-page object: {repr(page)}")
		#
		# 	# update all refs
		# 	page.update_all()
		#
		# 	self.app.route(page.path, methods=["GET", "POST"])(page.get_request_handler())

		app = self.prepare_app(self)

		app.debug = True
		app.run(host="0.0.0.0", port=80, debug=True)

	def prepare_app(self):
		for page in self.pages:
			if not isinstance(page, Page):
				raise RuntimeError(f"Server.pages contains non-page object: {repr(page)}")

			# update all refs
			page.update_all()

			self.app.route(page.path, methods=["GET", "POST"])(page.get_request_handler())

		return self.app




class UserException(Exception):
	pass


def args_kwargs_checker(arguments, kwarguments, **defaults):

	if len(arguments) > len(defaults):
		raise TypeError(str(len(defaults)) + "total arguments required but " + str(len(arguments)) + " args given")

	# for each argument in args, check to see if it is not in kwargs
	repeats = set(list(defaults.keys())[:len(arguments)]).intersection(kwarguments.keys())
	if len(repeats) != 0:
		raise TypeError("arguments specified as both args and kwargs: " + ", ".join(repeats))


	# add args to kwargs
	kwarguments = dict({list(defaults.keys())[i] : arguments[i] for i in range(0, len(arguments))}, **kwarguments)
	# fill blank arguments with default values
	kwarguments = dict(defaults, **kwarguments)

	return kwarguments


def type_checker(to_check_dict, **tests):

	for (key, test) in tests.items():
		test_result = _exception_from_test(to_check_dict[key], test)
		if test_result is not None:
			return type(test_result)(f"key {repr(key)}: {str(test_result)}")


def _exception_from_test(value, test):
	if isinstance(test, Iterable):
		for t in test:
			result = _exception_from_test(value, t)
			if result is not None:
				return result

	elif type(test) is type:
		if type(value) is not test:
			return TypeError("item " + repr(value) + " not of type " + test.__name__)

	elif callable(test):
		test_result = test(value)
		# test is a boolean function
		if type(test_result) is bool:
			if not test_result:
				return ValueError("item " + repr(value) + " fails test " + repr(test.__name__))
		# testing is a function that returns an exception / None
		else:
			return test_result

	return None


def separate_dict(args_dict, keys_to_remove):
	separated = {}
	for key in keys_to_remove:
		separated[key] = args_dict.pop(key)
	return separated

def js_rsp(js):
	return Response(
		response=js,
		status=200,
		mimetype="application/json"
	)

# returns a function that validates each item in a list
def list_of(test):
	def checker(list_to_validate):
		if not isinstance(list_to_validate, list):
			return TypeError("item not list")
		for item in list_to_validate:
			e = _exception_from_test(item, test)
			if e is not None:
				return e
	return checker

def has_length(length):
	def checker(itterable_to_validate):
		if not len(itterable_to_validate) == length:
			return TypeError(f"list needs length {len}, not {len(itterable_to_validate)}")
	return checker


if __name__ == "__main__":
	# TODO add a sample server
	pass

