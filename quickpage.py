
from pybrowsercontrolpanel import *
import functools

class RefUpdater:
	def __init__(self):
		self.fn = lambda: None

page_queue = []
current_ref_updater = RefUpdater()


def set_input(*args, **kwargs):
	at_time_of_creation_ref_updater = current_ref_updater
	def dec(fn):
		@functools.wraps(fn)
		def new_fn(self, *args2, **kwargs2):
			output = fn(self, *args2, **kwargs2)
			# we also want to update the output refs whenever this function is called.
			at_time_of_creation_ref_updater.fn()
			return output
		# WE HAVE TO CHANGE THIS LATER TO THE DECORATED VERSION
		# it needs to be undecorated for inspect. change after calling link_input.
		page_queue.append(Input(fn, args, kwargs))

		return new_fn
	return dec


def set_html(*args, **kwargs):
	def dec(fn):
		page_queue.append(Html(fn, args, kwargs))
		return fn
	return dec


def set_output(*args, **kwargs):
	def dec(fn):
		page_queue.append(Output(fn, args, kwargs))
		return fn
	return dec

def after_init(fn):
	page_queue.append(AfterInit(fn))
	return fn

class Input:
	def __init__(self, fn, args, kwargs):
		self.fn = fn
		self.args = args
		self.kwargs = kwargs

class Html:
	def __init__(self, fn, args, kwargs):
		self.fn = fn
		self.args = args
		self.kwargs = kwargs

class Output:
	def __init__(self, fn, args, kwargs):
		self.fn = fn
		self.args = args
		self.kwargs = kwargs


class AfterInit:
	def __init__(self, fn):
		self.fn = fn




# we want that whenever MyPage2 gets instansiated, it returns that class as a subclass of QuickPage. you should be able to call the inherited (original) methods normally.

# you could make a decorator that edits the __init__ variable of the new class to turn it into a page.

def make_quick_page(name=None, path=None):

	# return a class decorator
	def cl_decor(page_class):
		global current_ref_updater, page_queue
		at_time_of_creation_ref_updater = current_ref_updater
		current_ref_updater = RefUpdater()

		fns = page_queue[:]
		page_queue = []

		# edit the init method
		orig_init = page_class.__init__

		@functools.wraps(page_class.__init__)
		def new_init(self, *args, **kwargs):
			nonlocal name, path

			orig_init(self, *args, **kwargs)


			# CREATE THE PAGE =============================

			if (name is None): name = page_class.__name__
			if (path is None): path = name

			self.page = Page(name, path)
			
			self.page.html_template += f"""<!DOCTYPE html>
			<script src="{{{{ url_for('static', filename='page_script_minified.js') }}}}"></script>
			{{% autoescape false %}}
			"""

			for qp_obj in fns:

				if type(qp_obj) is Input:
					bound_fn = qp_obj.fn.__get__(self, self.__class__)
					ref = self.page.link_input(bound_fn, *qp_obj.args, **qp_obj.kwargs)
					# link_output parses the signiture, but this isn't the decorated version
					# we now need to replace the function linked to by the ref so that it calls update_all at the end.
					def new_context(): # to make sure bound_function is fixed in new_fn
						_bound_fn = bound_fn
						def new_fn(*args2, **kwargs2):
							output = _bound_fn(*args2, **kwargs2)
							# we also want to update the output refs whenever this function is called.
							at_time_of_creation_ref_updater.fn()
							return output
						return new_fn
					new_fn = new_context()
					self.page._get_object_of_ref(ref).prargs["function"] = new_fn#.__get__(self, self.__class__)

					self.page.html_template += f'{{{{ref("{ref}")}}}}'

				elif type(qp_obj) is Html:
					html_text = qp_obj.fn(self)  # expect no required args other then self.
					self.page.html_template += str(html_text)

				elif type(qp_obj) is Output:
					ref = self.page.link_output(qp_obj.fn.__get__(self, self.__class__), *qp_obj.args, **qp_obj.kwargs)
					self.page.html_template += f'{{{{ref("{ref}")}}}}'

				elif type(qp_obj) is AfterInit:
					pass

				else:
					raise TypeError("Expecting Input, Html, Output, AfterInit only.")

			self.page.html_template += f"{{% endautoescape %}}"


			for qp_obj in fns:
				if type(qp_obj) is AfterInit:
					qp_obj.fn(self)  # expect no required args other then self.

				
			at_time_of_creation_ref_updater.fn = self.page.update_all

		
		page_class.__init__ = new_init
		
		return page_class
	
	return cl_decor


