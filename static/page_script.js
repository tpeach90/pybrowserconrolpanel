var reffedElements;
var functionsOnServerObjectArgs;
var objVersions;
var logVersion;



var script = document.createElement('script');
script.src = 'https://code.jquery.com/jquery-3.4.1.min.js';
script.type = 'text/javascript';
document.getElementsByTagName("head")[0].appendChild(script);


window.onload = function() {

	// function outputTo(parent, evaluated) {
	// 	if (evaluated.user_exception != null) {
	// 		setError(parent, evaluated.user_exception);
	// 	} else if (evaluated.error != null) {
	// 		alert(evaluated.error);
	// 		// setError(parent, evaluated.error);
	// 	} else {
	// 		parent.innerHTML = evaluated.value;
	// 	}
	// }

	function outputTo(objOfRef, itemtype, evaluated) {
		if (!objOfRef.pageEls.hasOwnProperty(itemtype)) return;

		if (evaluated.error != null) {
			alert(evaluated.error);
			return;
		}
		if (objOfRef.escape) {
			Object.keys(evaluated).forEach((key, i) => {
				if (key != "update") {
					evaluated[key] = escapeHtml(evaluated[key]);
				}
			});
		}

		objOfRef.pageEls[itemtype].forEach((parent, i) => {
			if (evaluated.user_exception != null) {
				setError(parent, evaluated.user_exception);
			} else {
				parent.innerHTML = evaluated.value;
			}
		});

	}

	function setError(parent, errorText) {
		var error = document.createElement("div");
		error.innerHTML = errorText;
		error.classList.add("error-text");
		parent.innerHTML = "";
		parent.appendChild(error)
	}

	function findInArrayByAttribute(arr, attrName, arrVal){
		for (let i = 0; i < arr.length; i++) {
			if (arr[i][arrName] == arrVal) return arr[i];
		}
		return null;
	}

	// nabbed from stackoverflow
	function escapeHtml(unsafe) {
		return unsafe
			.replace(/&/g, "&amp;")
			.replace(/</g, "&lt;")
			.replace(/>/g, "&gt;")
			.replace(/"/g, "&quot;")
			.replace(/'/g, "&#039;")
			.replace(/ /g, "&nbsp")
			.replace(/\n/g, "<br>");
	}


	// list of all elements with a serverref="..." tag


	// in order to create the event handlers, we need to know what each reffed element is, eg a toggle or an input box. So the json needs to be gotten
	// var reffedElements = {}
	reffedElements = {};

	$.getJSON(window.location.pathname+"?what=json", function(pageData) {
		logVersion = pageData.log.version;
		objVersions = [];
		pageData.objects.forEach((object, i) => {
			reffedElements[object.ref] = {
				kind: object.kind,
				escape: object.escape,
				pageEls: []
			}
			objVersions.push(object.version);
		});


		// function text_output file_list toggle variable input
		for (let item of document.body.getElementsByTagName("*")) {
			var ref = item.getAttribute("serverref");

			if (ref == null) continue;

			if (reffedElements.hasOwnProperty(ref)) {

				var objOfRef = reffedElements[ref];
				var itemtype = item.getAttribute("itemtype");
				if (itemtype == null) itemtype = "null";

				if (!objOfRef.pageEls.hasOwnProperty(itemtype)) {
					objOfRef.pageEls[itemtype] = [item];
				} else {
					objOfRef.pageEls[itemtype].push(item);
				}

				// create events for button presses
				switch (objOfRef.kind) {

					case "function":

						if (itemtype == "button") {
							(function(ref, objOfRef) {
								$(item).bind("click", function() {
									$.post(window.location.pathname, {
										ref: ref,
										action: "button",
										obj_versions: JSON.stringify(objVersions),
										log_version: logVersion
									}, function(stringData, status) {
										var result = JSON.parse(stringData);
										outputTo(objOfRef, "output", result);
										// if (result.value != null) result.value = escapeHtml(result.value);
										// objOfRef.pageEls.output.forEach((outputEl, i) => {
										// 	outputTo(outputEl, result);
										// });

										if (result.update != null) update(result.update);

									});
									return false;
								});
							})(ref, objOfRef);
						}

						break;

					case "toggle":

						if (itemtype == "button") {
							(function(ref, objOfRef) {
								$(item).bind("click", function() {

									// work out the current value being displayed
									var current = objOfRef.pageEls.value[0].innerHTML;
									if (! current in ["true", "false"]) return; // maybe the page isn't refreshed yet - do not yet know what the current toggle value is
									var value;
									if (current == "true"){
										value = false;
									} else value = true;

									$.post(window.location.pathname, {
										ref: ref,
										action: "set",
										value: value,
										obj_versions: JSON.stringify(objVersions),
										log_version: logVersion
									}, function(stringData, status) {

										// still need to run this because there could be an error
										var result = JSON.parse(stringData);
										outputTo(objOfRef, "value", result);
										// if (result.value != null) result.value = escapeHtml(result.value);
										// objOfRef.pageEls.value.forEach((outputEl, i) => {
										// 	outputTo(outputEl, result);
										// });

										if (result.update != null) update(result.update);

									});
									return false;
								});
							})(ref, objOfRef);

						}

						break;



					case "input":

						if (itemtype == "button") {
							(function(ref, objOfRef) {
								$(item).bind("click", function() {
									// get the field data.
									var fieldValues = []
									for (let input of objOfRef.pageEls.fields[0].getElementsByTagName("input")) {
										fieldValues.push(input.value);
									}

									$.post(window.location.pathname, {
										ref: ref,
										action: "button",
										field_values: JSON.stringify(fieldValues),
										obj_versions: JSON.stringify(objVersions),
										log_version: logVersion
									}, function(stringData, status) {

										var result = JSON.parse(stringData);
										outputTo(objOfRef, "output", result);
										// if (result.value != null) result.value = escapeHtml(result.value);
										// objOfRef.pageEls.output.forEach((outputEl, i) => {
										// 	outputTo(outputEl, result);
										// });

										if (result.update != null) update(result.update);

									});
									return false;
								});
							})(ref, objOfRef);
						}

						break;

				}
			}
		}



		// create a function to be called on each object in the ?what=json objects
		// these update the values of text_output, toggle and variable sections (more may be added)
		functionsOnServerObjectArgs = []
		pageData.objects.forEach((serverObj, i) => {
			var objOfRef = reffedElements[serverObj.ref];

			if (objOfRef == null) {
				// the object doesn't appear on the webpage, so do nothing
				functionsOnServerObjectArgs.push(function(evaluated){});
				return;
			}

			switch (serverObj.kind) {

				case "output":
				if (objOfRef.pageEls.null == null) { // (.null means there was no itemtype="..." attribute)
					functionsOnServerObjectArgs.push(function(evaluated){});
					return;
				}
				// (function(elsToOutputTo) {
				// 	functionsOnServerObjectArgs.push(function(_serverObjArgs){
				// 		if (_serverObjArgs.evaluated.value != null) _serverObjArgs.evaluated.value = escapeHtml(_serverObjArgs.evaluated.value);
				// 		elsToOutputTo.forEach((el, i) => {
				// 			outputTo(el, _serverObjArgs.evaluated);
				// 		});
				// 	});
				// })(objOfRef.pageEls.null);
				// return;

				(function(_objOfRef) {
					functionsOnServerObjectArgs.push(function(evaluated){
						outputTo(_objOfRef, "null", evaluated);
					});
				})(objOfRef);
				return;

				case "toggle":
				if (objOfRef.pageEls.value == null) { // (null means there was no itemtype="..." attribute)
					functionsOnServerObjectArgs.push(function(evaluated){});
					return;
				}
				// (function(elsToOutputTo) {
				// 	functionsOnServerObjectArgs.push(function(_serverObjArgs){
				// 		if (_serverObjArgs.evaluated.value != null) _serverObjArgs.evaluated.value = escapeHtml(_serverObjArgs.evaluated.value);
				// 		elsToOutputTo.forEach((el, i) => {
				// 			outputTo(el, _serverObjArgs.evaluated);
				// 		});
				// 	});
				// })(objOfRef.pageEls.value);
				// return;
				(function(_objOfRef) {
					functionsOnServerObjectArgs.push(function(evaluated){
						outputTo(_objOfRef, "value", evaluated);
					});
				})(objOfRef);
				return;

				default:
				functionsOnServerObjectArgs.push(function(evaluated){});
			}


		});

		// fills in the json data (first time only)
		functionsOnServerObjectArgs.forEach((fn, i) => {
			fn(pageData.objects[i].evaluated);
		});

	});


	function update(updateData) {
		updateData.objects.forEach((obj, i) => {
			functionsOnServerObjectArgs[obj.index](obj.evaluated);
			objVersions[obj.index] = obj.version;
		});
		logVersion = updateData.log.version;
		if (updateData.log.updated) {
			console.log(updateData.log.log);
		}
	}

	$("#refresh").bind("click", function() {
		$.getJSON(window.location.pathname+"?what=json", function(pageData) {
			functionsOnServerObjectArgs.forEach((fn, i) => {
				fn(pageData.objects[i].evaluated);
			});
		});
		return false;
	});
	//

}
