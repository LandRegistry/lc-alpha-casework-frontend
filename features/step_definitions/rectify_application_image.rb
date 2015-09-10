Given(/^I am on the Bankruptcy Rectification document request screen$/) do
  $regnote = create_registration
  visit('http://localhost:5010')
  page.driver.browser.manage.window.maximize
  find(:id, 'Tasks').click
  find(:id, 'Rectify').click
end

When(/^I enter a registration number$/) do
  fill_in('reg_no', :with => $regnote)
end

Then(/^click on the continue button the screen displayed will shown the correct application details$/) do
    fill_in('reg_no', :with => $regnote)
    click_button('continue')
end

Given(/^I am on the Rectify screen$/) do
  #page.has_content?('Bankruptcy Rectification')
end

When(/^I click on the different thumbnails the editable details are displayed below$/) do
  pending # Write code here that turns the phrase above into concrete actions
end

When(/^I can overtype any detail that needs to be amended$/) do 
  pending # Write code here that turns the phrase above into concrete actions 
end 

When(/^there is more that one alias name$/) do 
  pending # Write code here that turns the phrase above into concrete actions 
end 

Then(/^all alias details will need to be updated to reflect the stored changes$/) do 
  pending # Write code here that turns the phrase above into concrete actions 
end 

When(/^I overtype the original details$/) do 
  pending # Write code here that turns the phrase above into concrete actions 
end 

Then(/^I can see both the original and the new details on the same screen$/) do 
  pending # Write code here that turns the phrase above into concrete actions 
end 

When(/^I click on the Submit button$/) do 
  pending # Write code here that turns the phrase above into concrete actions 
end 

Then(/^the application complete screen is displayed with the original unique identifier displayed$/) do 
  pending # Write code here that turns the phrase above into concrete actions 
end 

When(/^the rectification to the application has been submitted the amended unique identifier is displayed to the user on the screen$/) do 
  pending # Write code here that turns the phrase above into concrete actions 
end 