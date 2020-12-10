

output = '<span serverref="{{ref}}"></span>'

toggle = '<a href=# serverref="{{ref}}" itemtype="button"><button class="btn btn-default">{{args["title"]}}</button></a><span serverref="{{ref}}" itemtype="value"></span>'

input = '<form serverref="{{ref}}" itemtype="fields">{% for field_title in args["field_titles"] %}<label>{{ field_title }}</label><br><input type="text"><br>{% endfor %}</form><a href=# serverref="{{ref}}" itemtype="button"><button class="btn btn-default">{{args["title"]}}</button></a><span serverref="{{ref}}" itemtype="output"></span>'
