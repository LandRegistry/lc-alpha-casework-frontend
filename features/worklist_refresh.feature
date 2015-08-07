@WorklistRefresh

Feature: Refresh of the totals of applications

Scenario: Auto update application totals
Given I have selected to view the main worklist
When I can see the total bankruptcy applications
And I have submitted a new PAB
And I have waited 35 seconds
Then I see the totals refresh