Given(/^I have selected to view the main worklist$/) do
  visit( 'http://localhost:5010')
end

#When   I have selected to view specific the application list "pab"
When(/^I have selected to view specific the application list "(.*)"$/) do |type|
    visit( "http://localhost:5010/get_list?appn=#{type}" )
end

Then (/^I see the pab application list page$/) do
    page.should have_content("PA Bankruptcy Registrations")
    page.should have_content("21 September 2014")
end

