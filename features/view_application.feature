@ViewApplication

Feature: View application

Scenario: View pab application
Given I have selected to view the main worklist
When I have selected to view specific the application list "bank_regn"
And I see the bankruptcy application list page
And I select a pab application
Then I see the application details page