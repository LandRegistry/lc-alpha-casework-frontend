@ViewWork

Feature: View work by application type

Scenario: View pab list
Given I have selected to view the main worklist
When I have selected to view specific the application list "pab"
Then I see the pab application list page

Scenario: View work by application type
Given I have selected to view the main worklist
When I have selected to view specific the application list "wob"
Then I see the wob application list page

Scenario: View work by application type
Given I have selected to view the main worklist
When I have selected to view specific the application list "lc_regn"
Then I see the application list page with no waiting apps

Scenario: View work by application type
Given I have selected to view the main worklist
When I have selected to view specific the application list "amend"
Then I see the application list page with no waiting apps

Scenario: View work by application type
Given I have selected to view the main worklist
When I have selected to view specific the application list "cancel"
Then I see the application list page with no waiting apps

Scenario: View work by application type
Given I have selected to view the main worklist
When I have selected to view specific the application list "prt_search"
Then I see the application list page with no waiting apps

Scenario: View work by application type
Given I have selected to view the main worklist
When I have selected to view specific the application list "search"
Then I see the application list page with no waiting apps

Scenario: View work by application type
Given I have selected to view the main worklist
When I have selected to view specific the application list "oc"
Then I see the application list page with no waiting apps