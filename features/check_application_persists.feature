@CheckPersists

Feature: Check application persists

Scenario: Check application persists
Given I have selected to view the main worklist
When I have selected to view specific the application list "bank_regn"
And I see the bankruptcy application list page
And I select a pab application
And I see the application details page
And I close browser
And I have waited 5 seconds
And I open a new browser instance
And I have selected to view the main worklist
And I have selected to view specific the application list "bank_regn"
Then I see the bankruptcy application list page


