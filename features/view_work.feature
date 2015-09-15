@ViewWork

Feature: View work by application type

Scenario: View pab list
Given I have selected to view the main worklist
When I have selected to view specific the application list "bank_regn"
Then I see the bankruptcy application list page
And I see the application totals

Scenario: View land charge registrations
Given I have selected to view the main worklist
When I have selected to view specific the application list "lc_regn"
Then I see the application list page with no waiting apps
And I see the application totals

Scenario: View amendments
Given I have selected to view the main worklist
When I have selected to view specific the application list "amend"
Then I see the amendments application list page
And I see the application totals

Scenario: View cancellations
Given I have selected to view the main worklist
When I have selected to view specific the application list "cancel"
Then I see the cancellations application list page
And I see the application totals

Scenario: View searches
Given I have selected to view the main worklist
When I have selected to view specific the application list "search"
Then I see the searches application list page
And I see the application totals

Scenario: View office copies
Given I have selected to view the main worklist
When I have selected to view specific the application list "oc"
Then I see the OC application list page
And I see the application totals