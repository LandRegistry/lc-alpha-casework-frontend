@aai

Feature: amendment application image

As a land charges caseworker
I want to be able to view an image on a amendment application form
So that I can ensure that details are captured correctly onto the land charges register

Scenario: Using the land charges system for amendments
#AM-US001	View Application
Given I have selected to view a specific record on the amendments application list the individual record is displayed
When I am on the retrieve original documents  screen  the accompanying evidence is visible as thumbnails
When I click on an amendment form thumbnail the image is expanded to large image
When I am on a Large image of the amendment form I can zoom in
When I am on a Large image of the amendment form I can zoom out
When I must have a registration number before the continue button can be clicked
Then I can click the amendment screen continue button to go to the next screen

#AM-US002	View Original Application confirm
Given I am on the bankruptcy details screen
When the application details become visible they must be the correct ones for the registration detailed on the previous screen 
When I can click the amendment screen continue button the system will go next screen
Then the next screen will be the amendment confirmation screen

#AM-US002	View Original Application reject
Given I am on the bankruptcy details screen
When the application details become visible they must be the correct ones for the registration detailed on the previous screen 
When I can click the reject button on the amendment screen the system will go next screen
Then the next screen will be the amendment rejection screen

#AM-US003	Amend Details
Given I am on the bankruptcy details worklist screen with amendments still listed
When I must have a different registration number before the continue button can be clicked
When I am on the amend details screen I can click on the amend name button
When the Debtor details screen is displayed I can overtype the details
And click the continue button the new details are stored
When I click the add button for alias name the debtor alias name screen is displayed
When I enter the alias names 
And click the continue button the new details are stored
When I click the add button for alias name the debtor alias name screen is displayed
When I enter the additional alias names 
And click the continue button the new details are stored 
When I select an alias name and click the remove button the name is removed from the screen
When I click on the add button for address the address details screen is displayed
When I enter the address details 
And click the continue button the new details are stored
When I am on the amend details screen I can click on the amend address button
When the address details screen is displayed I can overtype the details
And click the continue button the new details are stored
When I select an address and click the remove button the address is removed from the screen
When I am on the amend details screen I can click on the amend court button
When the court details screen is displayed I can overtype the details
And click the continue button the new details are stored
Then I can click submit button to save all new information


#AM-US005	Unique Identifier
Given the amendment confirmation screen is visible	
When the amendments application has been submitted the unique identifier is displayed to the user on the screen	
Then the user can return to the worklist from the amendment screens

#CR-US010 Amend Indicator
Given the application has been amended 	
When we check the bankruptcy database record there must be a indicator for amended	
Then the indicator must have a value for amended


 