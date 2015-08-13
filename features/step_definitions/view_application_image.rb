Given(/^I am on the view application screen$/) do 
  visit('http://localhost:5010')
end 

When(/^I have selected to view specific the application list$/) do 
    visit( "http://localhost:5010/get_list?appn=bank_regn" )
    find(:xpath,"html/body/div[1]/div/div/div[3]/div/table/tbody/tr[1]/td[1]/a").click
    
end 

When(/^the image of the application is displayed I can click on all available pages$/) do 
   find(:xpath, "html/body/div[1]/div/div/div[2]/div[1]/div[1]/img[2]").click
   find(:xpath, "html/body/div[1]/div/div/div[2]/div[1]/div[1]/img[3]").click
   find(:xpath, "html/body/div[1]/div/div/div[2]/div[1]/div[1]/img[1]").click 

end 

When(/^I click on a page the image it is visible$/) do
  #find(:xpath, "html/body/div[1]/div/div/div[2]/div[1]/div[1]/img[2]").displayed?
  #page.should have_content("http://localhost:5014/document/9/image/2")  
end

When(/^I am on a page I can zoom in$/) do
  all('.zoomcontrols')[0].click
  thing = find(:xpath, '//*[@id="imageContainer"]/div[1]/div/div')
  expect(thing.text).to eq "2x Magnify"
end

Then(/^I am on a page I can zoom out$/) do
  all('.zoomcontrols')[1].click
  thing = find(:xpath, '//*[@id="imageContainer"]/div[1]/div/div')
  expect(thing.text).to eq "1x Magnify"
end

Given(/^I am on the debtors name and details screen$/) do
  page.has_content?('Debtor name and details')
  puts('screen shows')
end

When(/^I complete the Forename and Surname details remain visible$/) do
    fill_in('forename', :with => 'Nicola')
  fill_in('surname', :with => 'Andrews')
end

When(/^I click the add name button Alias Forename\(s\) and Alias Surname is displayed$/) do
   click_button('Add alias name')
   fill_in('aliasforename0', :with =>'Nichola')
   fill_in('aliassurname0', :with => 'Andrews')
   click_button('Add alias name')
   fill_in('aliasforename1', :with =>'Nicola')
   fill_in('aliassurname1', :with => 'Andrewson')
end

When(/^I amend a Forename the new details remain visable$/) do
  fill_in('forename', :with => 'Nicola Jayne')
end

Then(/^I amend the Surname of the Alias Surname and the new details remain visible$/) do
  fill_in('aliasforename0', :with => 'Nicola')
end

When(/^I enter an Occupation the details remain visible$/) do
  fill_in('occupation', :with => 'civil servant')
end

Then(/^I click the continue button and the debtors address screen is displayed$/) do
  click_button('Continue')
end

Given(/^I am on the debtors address screen$/) do
  page.has_content?('Debtor address')
end

When(/^I supply the address details in the address fields$/) do
  pending # Write code here that turns the phrase above into concrete actions
end

When(/^click the add address button the address is added to the top of the screen$/) do
  pending # Write code here that turns the phrase above into concrete actions
end

When(/^I supply additional address details$/) do
  pending # Write code here that turns the phrase above into concrete actions
end

Then(/^I click the continue button and the case information screen is displayed$/) do
  pending # Write code here that turns the phrase above into concrete actions
end

Given(/^I am on the case information screen$/) do
  page.has_content?('Case information')
end

When(/^I first see the class of charge neither PAB or WOB are checked$/) do
  pending # Write code here that turns the phrase above into concrete actions
end

When(/^I select a Class of Charge of PAB this becomes checked$/) do 
  pending # Write code here that turns the phrase above into concrete actions 
end 

Then(/^I select a Class of Charge of WOB this becomes checked and PAB becomes unchecked$/) do 
  pending # Write code here that turns the phrase above into concrete actions 
end 

When(/^I enter a court name the details remain visible$/) do 
  pending # Write code here that turns the phrase above into concrete actions 
end 

When(/^I enter a court number and year the details remain visible$/) do 
  pending # Write code here that turns the phrase above into concrete actions 
end 

Then(/^I click the continue button and the application complete screen is displayed$/) do 
  pending # Write code here that turns the phrase above into concrete actions 
end 

Given(/^the submit button on the case information page has been clicked$/) do 
  pending # Write code here that turns the phrase above into concrete actions 
end 

When(/^the Application complete screen is visible$/) do 
  pending # Write code here that turns the phrase above into concrete actions 
end 

Then(/^the unique identifier is displayed to the user on the screen$/) do 
  pending # Write code here that turns the phrase above into concrete actions 
end 