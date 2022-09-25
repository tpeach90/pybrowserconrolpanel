
import pybrowsercontrolpanel, quickpage

from random import random
from datetime import datetime


@quickpage.make_quick_page(path="/")
class Homepage:

	def __init__(self):
		self.counter = 0

	@quickpage.after_init
	def init_2(self):
		# Now you have access to self.page
		self.page.html_template += "<br><br>This text was added using an @after_init function!"
	
	@quickpage.set_html()
	def top_text(self):
		return """<h1>Example Page</h1>
		<p><a href="?what=json">Click here</a> to view the JSON for this page. <a href="second_page">Click here</a> to go to another page</p>
		<h2>Increase or decrease the counter</h2>"""

	@quickpage.set_input()
	def increase_counter(self):
		self.counter += 1
		return ""
	
	@quickpage.set_input()
	def increase_counter_by_amount(self, amount):
		try:
			self.counter += int(amount)
		except ValueError:
			return "Please enter an integer number"
		else:
			return ""

	@quickpage.set_html()
	def bottom_text(self):
		return "<p>The current amount is "
	
	@quickpage.set_output()
	def get_counter(self) -> int: # all outputs are converted to string within pbcp
		# if running the function produces the same result as before, then the new output is not sent to the user.
		return self.counter
	
	@quickpage.set_html()
	def bottom_text(self):
		return "</p>"


	
	@quickpage.set_html()
	def custom_msg_text(self):
		return "<h2>Enter some details to get a custom message</h2>"
	
	@quickpage.set_input(title="Generate custom message", field_titles=["First name/given name", "Last name/surname", "Age", "City"])
	def custom_msg(self, first_name, last_name, age, city):
		return f"Hello {first_name} {last_name}, you are {age} years old and live in {city}!"



	@quickpage.set_html()
	def random_image_text(self):
		return "<h2>This image updates every time a button is pressed.</h2>"

	@quickpage.set_output(escape=False)
	def random_image(self):
		# set_output(escape=False) should be used for HTML that updates.
		# set_html is only called once when the program first starts.

		# this function adds a random number to the end of the image so pybrowsercontrolpanel resends the data
		# and so that the browser reloads it.
		return '<img src="https://picsum.photos/200?' + str(random()) + '">'


@quickpage.make_quick_page(path="/second_page")
class SecondPage:
	def __init__(self, time):
		self.time_of_creation = time
	
	@quickpage.set_html()
	def txt(self):
		return f"This is a second page. It page was created at {str(self.time_of_creation)}. <a href=\"/\">Back</a>"



if __name__ == "__main__":

	homepage = Homepage()
	second_page = SecondPage(datetime.now().strftime("%H:%M:%S"))

	server = pybrowsercontrolpanel.Server()
	server.pages.extend([homepage.page, second_page.page])

	# sets up routes and runs a flask app.
	# If you want to get a prepared flask app without running it, use
	# app = server.prepare_app():
	server.run()


	
	
