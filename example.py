from pybrowsercontrolpanel import *
from datetime import datetime


class ExamplePage(Page):
	def __init__(self):
		Page.__init__(self, "example", "/")

		self.text_value = ""
		self.current_time = "The current time has not been updated yet"

		# inputs
		current_time_ref = self.link_input(self.get_current_time, title="Get the current time")
		update_time_ref = self.link_input(self.refresh_current_time_for_everyone, title="Update the current time for everyone")
		add_text_ref = self.link_input(self.add_to_text_at_bottom_of_page, title="Add your text", field_titles=["The text you would like to add"])

		# outputs
		self.text_ref = self.link_output(self.update_text_at_bottom_of_page)
		self.current_time_output_ref = self.link_output(self.update_current_time_output)

		# the html template we're using. 
		# this would usually be in a separate file.
		# this variable is a property of the superclass and is filled in using the jinja2 templating engine.
		# it has access to the function ref() which converts the ref into html code using the templates in default_obj_templates.py
		# these templates can be overridden by changing the variables self.default_output_template and self.default_input_template.
		self.html_template = f"""
			<!-- This script must be linked on all pages. -->
			<script src="{{{{ url_for('static', filename='page_script_minified.js') }}}}"></script>

			<!-- We must break out of autoescape because ref creates html elements.
			However, text will always be escaped when output to the browser screen.
			If you want your refs to output non-escaped content, then set escape=False in link_output and link_input.-->
			{{% autoescape false %}}

			<h2>Current Time output</h2>
			{{{{ref("{self.current_time_output_ref}")}}}}
			<h2>Current Time get (just for me)</h2>
			{{{{ref("{current_time_ref}")}}}}
			<h2>Current Time get (for everyone)</h2>
			{{{{ref("{update_time_ref}")}}}}
			<h2>Add text to the section below</h2>
			{{{{ref("{add_text_ref}")}}}}
			<h2>Text displayed to eveyone:</h2>
			{{{{ref("{self.text_ref}")}}}}

			{{% endautoescape %}}
			
			<!-- A buttin with id="refresh" will refresh all output refs -->
			<h2>Refresh output refs (try using this in multiple tabs)</h2>
			<button id="refresh">Refresh</button>

		"""


	#input
	def get_current_time(self):
		# an input with no arguments.
		now = datetime.now()

		# result only visible to the user that send the message (when this function is called from the webpage)
		return now.strftime("%d/%m/%Y %H:%M:%S")
	
	# input
	def refresh_current_time_for_everyone(self):
		# re-use the function defined above
		self.current_time = self.get_current_time()
		# tell pybrowsercontrolpanel to update the output on the screen
		self.update_ref(self.current_time_output_ref)
		return "The current time has been updated"
	
	# output
	def update_current_time_output(self):
		# this is the function that is reffed by self.current_time_output_ref
		# it is called by pybrowsercontrolpanel when the user calls
		# self.update_ref(self.current_time_output_ref)
		return self.current_time

	
	#input
	def add_to_text_at_bottom_of_page(self, text):
		# an input with an argument.

		self.text_value += text + "\n"

		# required so update_text_at_bottom_of_page() is called.
		# the new output will be included in this response
		self.update_ref(self.text_ref)

		# only visible to the request user
		return "Your text has been added."
	
	# output
	def update_text_at_bottom_of_page(self):
		# This is the same over all instances in the browser.
		# These are only updated when self.update_ref() is called,
		# with this output's ref as the argument
		# note output functions should take no arguments (other than self)
		return "Inputs to the section above:\n"+ self.text_value

	

	


if __name__ == "__main__":
	server = Server()
	server.pages.append(ExamplePage())

	# sets up routes and runs a flask app.
	# If you want to get a prepared flask app without running it, use 
	# app = server.prepare_app():
	server.run()