Given(/^I am on the bankruptcy searches screen$/) do
  $regnote = create_registration
   #$regnote = '50011'
  visit('http://localhost:5010')
  maximise_browser
  visit( "http://localhost:5010/get_list?appn=search" )
    #find(:id,'amend_total').click
 end

When(/^I select an application type of Search the application is displayed$/) do
 # if app type == 'Search'
  
  #then  find(:id, app_type =='Search').click
  # find(:xpath,'html/body/div[1]/div/div/div[3]/div/table/tbody/tr[1]/td[1]').click
  visit( "http://localhost:5010/get_list?appn=search" )
    find(:xpath,".//*[@id='results']/tbody/tr[1]/td[1]/a").click
end

When(/^the image of the search application is displayed I can click on all available pages$/) do
  #find(:xpath, '//*[@id="container0]/img[1]').click
                 
end

Given(/^I am on the bankruptcy search details screen$/) do
  expect(page).to have_content('Bankruptcy Search')
  expect(page).to have_content('Full Name')
  expect(page).to have_content('Complete the debtor')
  expect(page).to have_button('Complete Search')

end

When(/^I click on the name details tab I can enter six names$/) do
  fill_in('fullname0', :with => 'Miss Piggy')
  fill_in('fullname1', :with => 'Gonzo')
  fill_in('fullname2', :with => 'Kermit T Frog')
  fill_in('fullname3', :with => 'Rolfe')
  fill_in('fullname4', :with => 'Animal')
  fill_in('fullname5', :with => 'Beaker')
end

When(/^I click on the Customer details tab I can enter the key number Customer Name Customer Address Customer Reference$/) do
  click_link('Customer Details')
  expect(page).to have_content('Key Number')
  expect(page).to have_content('Customer Name')
  expect(page).to have_content('Customer Address')
  expect(page).to have_content('Customer Reference')
  expect(page).to have_button('Complete Search')
  fill_in('Key Number', :with => '1234567')
  fill_in('customer_ref', :with => '100/102')
end

Then(/^I can click the complete search button$/) do
  click_button('search')
end

When(/^I select an application type of Full Search the application is displayed$/) do
  apptype_search = xpath(//*[@id="results"]/tbody/tr[1]/td[3]).text
  apptype_fullsearch = xpath(//*[@id="results"]/tbody/tr[2]/td[3]).text
 #if app type == 'Search'
  #then  find(:id, app_type =='Search').click
  find(:xpath,'html/body/div[1]/div/div/div[3]/div/table/tbody/tr[1]/td[1]').click
end



When(/^I click on the get customer details button the customer name and address fields are populated$/) do
  pending # Write code here that turns the phrase above into concrete actions
end

When(/^I click on entered details in the address box I can make an amendment$/) do
  pending # Write code here that turns the phrase above into concrete actions
end

When(/^I click on the search areas tab all counties check box search area  List of Areas to search is displayed$/) do
  pending # Write code here that turns the phrase above into concrete actions
end

When(/^I check the all counties box I cannot entered details in the search area edit box$/) do
  pending # Write code here that turns the phrase above into concrete actions
end

When(/^I enter details into the search area edit box I can click on the add area button$/) do
  pending # Write code here that turns the phrase above into concrete actions
end

When(/^add area button is clicked the search area details are added to the List of areas to search box$/) do
  pending # Write code here that turns the phrase above into concrete actions
end

When(/^I click on entered details in the list of areas search box I can make an amendment$/) do
  pending # Write code here that turns the phrase above into concrete actions
end

When(/^I click on the search period tab the search from field is set to (\d+)$/) do |arg1|
  pending # Write code here that turns the phrase above into concrete actions
end

When(/^I click in the search to field I can add the current year$/) do
  pending # Write code here that turns the phrase above into concrete actions
end

Then(/^I can click the complete search button when the customer address field is complete$/) do
  pending # Write code here that turns the phrase above into concrete actions
end