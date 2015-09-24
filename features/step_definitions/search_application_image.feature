@sai

Feature: search application image

As a land charges caseworker 
I want to be able to view an image of a bankruptcy search request that has been posted to LR
So that I can ensure that the search request details are captured and processed correctly

Scenario: Using the bankruptcy searchs task on the  Land Charges system

#SH-US002 Bankruptcy Search - View Postal Search
Given I am on the bankruptcy searches screen
When I select an application type of Search the application is displayed
#When the image of the search application is displayed I can click on all available pages
#When I click on a page the image it is visible
#When I am on a page I can zoom in
#Then I am on a page I can zoom out

#SH-US003 Bankruptcy Search - Capture Customer Details
Given I am on the bankruptcy search details screen
When I click on the name details tab I can enter six names
When I click on the Customer details tab I can enter the key number Customer Name Customer Address Customer Reference
Then I can click the complete search button

#SH-US018 Full search - View Postal Search
Given I am on the bankruptcy searches screen
When I select an application type of Full Search the application is displayed
When the image of the application is displayed I can click on all available pages
When I click on a page the image it is visible
When I am on a page I can zoom in
Then I am on a page I can zoom out

#SH-US019 - Full Search - Capture Customer Details
Given I am on the bankruptcy search details screen
When I click on the name details tab I can enter six names
When I click on the Customer details tab I can enter the key number Customer Name Customer Address Customer Reference
When I click on the get customer details button the customer name and address fields are populated
When I click on entered details in the address box I can make an amendment
When I click on the search areas tab all counties check box search area  List of Areas to search is displayed
When I check the all counties box I cannot entered details in the search area edit box
When I enter details into the search area edit box I can click on the add area button
When add area button is clicked the search area details are added to the List of areas to search box
When I click on entered details in the list of areas search box I can make an amendment
When I click on the search period tab the search from field is set to 1925
When I click in the search to field I can add the current year
Then I can click the complete search button when the customer address field is complete









