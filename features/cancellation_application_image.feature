@cai

Feature: cancellation application image

As a land charges caseworker
I want to be able to view an image on a cancellation application form
So that I can ensure that details are captured correctly onto the land charges register

Scenario: Using the land charges system for cancellations
#CR-US001 View application and evidence
Given I have selected to view a specific record on the cancellation application list the individual record is display
When I am on the request original documents  screen  the accompanying evidence is visible as thumbnails
When I click on a thumbnail the image is expanded to large image
When I am on a Large image I can zoom in
When I am on a Large image I can zoom out
When I must have a registration number value before the continue button can be clicked
Then I can click the continue button to go to the next screen

#CR-US002 View original application(s) completed
Given I am on the Application details screen
When the application details become visible they must be the correct ones for the registration number detailed on the previous screen 
When I can click the continue button the system will go next screen
Then the next screen will be the confirmation screen

#CR-US004 Unique Identifier
Given the  confirmation screen is visible	
When the cancellation application has been submitted the unique identifier is displayed to the user on the screen	
Then the user can return to the worklist

#CR-US002 View original application(s) rejected
Given I have selected to view a specific record on the cancellation application list the individual record is display
When I must have a registration number value before the continue button can be clicked
When I can click the continue button to go to the next screen
When I can click the reject button the system will go next screen
Then the next screen will be the rejection screen

#CR-US006 Cancel Indicator
Given the application has been cancelled 	
When we check the bankruptcy database record there must be a indicator for cancelled	
Then the indicator must have a value for cancelled


