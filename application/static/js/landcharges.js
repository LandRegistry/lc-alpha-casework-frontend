// Checks a string to see if it in a valid date format
// of (D)D/(M)M/(YY)YY and returns true/false

	function isValidDate(s) {
		// format D(D)/M(M)/(YY)YY
		var dateFormat = /^\d{1,4}[\.|\/|-]\d{1,2}[\.|\/|-]\d{1,4}$/;
	 if (dateFormat.test(s)) {
			// remove any leading zeros from date values
			s = s.replace(/0*(\d*)/gi,"$1");
			var dateArray = s.split(/[\.|\/|-]/);
			// correct month value
			dateArray[1] = dateArray[1]-1;
	 // correct year value
			if (dateArray[2].length<4) {
				// correct year value
				dateArray[2] = (parseInt(dateArray[2]) < 50) ? 2000 + parseInt(dateArray[2]) : 1900 + parseInt(dateArray[2]);
			}
	 var testDate = new Date(dateArray[2], dateArray[1], dateArray[0]);
			if (testDate.getDate()!=dateArray[0] || testDate.getMonth()!=dateArray[1] || testDate.getFullYear()!=dateArray[2]) {
				return false;
			} else {
				return true;
			}
		} else {
			return false;
		}
	}


	function validateDate(obj){
		// loop through all dateEntry fields and check for valid date
		var allOK = true;
		jQuery('.error_text').hide();

		 $('.dateEntry').each(function(i, obj) {
			if (isValidDate(obj.value) == false) {
				jQuery('<p class="error_text"><strong>Invalid date please re-enter</strong></p>').insertBefore(obj);
				allOK = false;
			}
		});

		return allOK;
	}

	 function removeRequired(obj){

		// identify the parent form
		parent_form = jQuery(obj).closest('form');

		// loop through all child elements of the parent form and remove the required attribute to allow application to be
		// stored regardless of what has been entered.

		str = '#' + parent_form.attr("id") + ' *';   // should evaluate to something like this: #form_name *
		jQuery(str).each(function() {
				jQuery(this).removeAttr( "required" );
				jQuery(this).removeAttr( "aria-required" );
			}
		);
	}

	function getApplication(list, id, type){
		// Display loading message over work_list so user knows something is happening
		$('#work-list').block({
			message: '<h2 class="wait-message" >Loading application ....</h2>'
		});
		// Open selected application
		window.location = "/application_start/"+list+"/"+id+"/"+type;
	}
