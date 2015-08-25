@vai

Feature: View Application Image

As a land charges caserworker
I want to be able to view an image on a bankruptsy application form
So that I can ensure that details are captured correctly onto the land charges register

Scenario: Using the land charges system
#US005 View Image of Application
Given I am on the view application screen
When I have selected to view specific the application list
When the image of the application is displayed I can click on all available pages
When I click on a page the image it is visible
When I am on a page I can zoom in
Then I am on a page I can zoom out

#US008 Supplying the Debtors name 
Given I am on the debtors name and details screen
When I complete the Forename and Surname details remain visible 
When I click the add name button Alias Forename(s) and Alias Surname is displayed
When I amend a Forename the new details remain visable
Then I amend the Surname of the Alias Surname and the new details remain visible

#US020 Supplying the occupation details
Given I am on the debtors name and details screen 
When I enter an Occupation the details remain visible
Then I click the continue button and the debtors address screen is displayed

#US010 Supplying the debtors address
Given I am on the debtors address screen
When I supply the address details in the address fields they remain visible
When I click the add address button the address is added to the top of the screen
When I supply additional address details 
When I click the add address button the address is added to the top of the screen
Then I click the continue button and the case information screen is displayed

#US007 Supplying class of charge
Given I am on the case information screen
When I first see the class of charge neither PAB or WOB are checked
When I select a Class of Charge of PAB this becomes checked
Then I select a Class of Charge of WOB this becomes checked and PAB becomes unchecked

#US014 AND US015 Supplying the court details
Given I am on the case information screen
When I enter a court name the details remain visible
When I enter a court number and year the details remain visible
Then I click the submit button and the application complete screen is displayed

#US006 and US018 Unique Identifier
Given the Application complete screen is visible
When the Application has been submitted the unique identifier is displayed to the user on the screen
And the Application has been submitted the date is displayed to the user on the screen
Then the user can return to the worklist

