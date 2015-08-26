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
Given I am on the bankruptcy details screen
When the application details become visible they must be the correct ones for the registration detailed on the previous screen 
When I can click the amend button the system will go next screen
When the next screen will be the amendments screen
When I am on the Amend Details screen I must be able to see all debtors details
And all addresses
And court details
When I click on the Add alias the debtor details amendment screen visible
When I enter the new alias details I can then click the next button  to add additional debtors details
When I enter additional alias details I can then click the continue button which returns me to the Amend details screen 
When I click on the Add address the Address details screen becomes visible
When I enter the new address details I can click on the next button to add an additional address
When I enter additional address details I can then click the continue button which returns me to the Amend details screen 
When I click on an previously saved debtors details I am taken to the amend screen which displays all of the saved information
When I overtype the debtor details I can then click on the continue button which returns me to the Amend details screen  
When I click on an previously saved address details I am taken to the amend screen which displays all of the saved information
When I overtype the address details I can then click on the continue button which returns me to the Amend details screen  
When I click on an previously saved court details I am taken to the amend screen which displays all of the saved information
When I overtype the court details I can then click on the continue button which returns me to the Amend details screen  
Then I can click submit button to save all new information

#AM-US005	Unique Identifier
Given the amendment confirmation screen is visible	
When the amendments application has been submitted the unique identifier is displayed to the user on the screen	
Then the user can return to the worklist from the amendment screens




 