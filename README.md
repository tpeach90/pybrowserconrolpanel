# pybrowsercontrolpanel

Create a web browser interface for a Python program. The pages display the same information on all browser sessions. See [example.py](example.py) for all functionality.

Quickpage uses decorators to call pybrowsercontrolpanel methods.

## Page
Create a new page using `mypage = pybrowsercontrolpanel.Page(name, path)`.

## Inputs
Use `my_input_ref = mypage.link_input(function)` to link a function to a page. Keyword options can be passed to `link_input` to change the title and field titles (see example).

Add the form to the HTML by adding `f"{{{{ref({my_input_ref})}}}}` to `mypage.html_template`. This is expanded with jinja2 to the input template set in `mypage.default_input_template` (see default_obj_templates.py for the general format). Note that jinja2 is run twice in total - first to replace the above with the default template and second to fill in that template.

## Outputs
Similarly, use `my_output_ref = mypage.link_output(function)` to register an output, and add to the HTML in the same way as before. The output template is found in mypage.default_output_template.

To update the value of an output, use `mypage.update_ref(my_output_ref)`. 

## Starting the server
```
server = pybrowsercontrolpanel.Server()
server.pages.append(mypage)
server.run()
```
In order to just get the prepared flask app without launching it, use `server.prepare_app()`

In order to get the endpoint function for a Page, use `mypage.get_request_handler()`.

# quickpage

Easier syntax with pages created by decorating classes. See [example2_quickpage.py](example2_quickpage.py).



