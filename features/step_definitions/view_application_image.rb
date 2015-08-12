Given(/^I am on the view application screen$/) do 
  visit('http://localhost:5010')
end 

When(/^I have selected to view specific the application list$/) do 
    visit( "http://localhost:5010/get_list?appn=bank_regn" )
    find(:xpath,"html/body/div[1]/div/div/div[3]/div/table/tbody/tr[1]/td[1]/a").click
    
end 

When(/^the image of the application is displayed I can click on all available pages$/) do 
   find(:xpath, "html/body/div[1]/div/div/div[2]/div[1]/div[1]/img[2]").click
   sleep(5)
   find(:xpath, "html/body/div[1]/div/div/div[2]/div[1]/div[1]/img[3]").click
   sleep(5)
   find(:xpath, "html/body/div[1]/div/div/div[2]/div[1]/div[1]/img[1]").click 
   sleep(10)
end 

When(/^I click on a page the image it is visible$/) do
  #find(:xpath, "html/body/div[1]/div/div/div[2]/div[1]/div[1]/img[2]").displayed?
  #page.should have_content("http://localhost:5014/document/9/image/2")  
end

When(/^the image is initially displayed it starts a (\d+)x magnify$/) do |arg1|
  pending # Write code here that turns the phrase above into concrete actions
end

When(/^I am on a page I can zoom in$/) do
  find(:xpath, "html/body/div[1]/div/div/div[2]/div[1]/div[2]/div/div[2]/div/img[2]").click    
  puts('zoom in')
end

Then(/^I am on a page I can zoom out$/) do
  find(:xpath, "html/body/div[1]/div/div/div[2]/div[1]/div[2]/div/div[2]/div/img[3]").click
  puts('zoom out')
end

Given(/^I am on the debtors name and details screen$/) do
  page.has_content?('Debtor name and details')
  puts('screen shows')
end

When(/^I complete the Forename and Surname details remain visible$/) do
  puts('heloo')
  sleep(20)
  puts('hello')
  find(:xpath, "html/body/div[1]/div/div/div[2]/div[1]/div[1]/img[3]").click
  puts('good')
  find(:xpath, "html/body/div[1]/div/div/div[2]/div[2]/form/div[1]/input").clear
  find(:xpath, "html/body/div[1]/div/div/div[2]/div[2]/form/div[1]/input").send_keys "nicola"
  find(:id, "surname").clear
  find(:id, "surname").send_keys "andrews"
end

When(/^I click the add name button Alias Forename\(s\) and Alias Surname is displayed$/) do
  pending # Write code here that turns the phrase above into concrete actions
end

When(/^I amend a Forename the new details remain visable$/) do
  pending # Write code here that turns the phrase above into concrete actions
end

Then(/^I amend the Surname of the Alias Surname and the new details remain visible$/) do
  pending # Write code here that turns the phrase above into concrete actions
end

When(/^I enter an Occupation the details remain visible$/) do
  pending # Write code here that turns the phrase above into concrete actions
end

Then(/^I click the continue button and the debtors address screen is displayed$/) do
  pending # Write code here that turns the phrase above into concrete actions
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