Given(/^I have selected to view a specific record on the amendments application list the individual record is displayed$/) do
   #$regnote = create_registration
   $regnote = '50011'
  visit('http://localhost:5010')
  maximise_browser
  visit( "http://localhost:5010/get_list?appn=amend" )
    #find(:id,'amend_total').click
    find(:xpath,'html/body/div[1]/div/div/div[3]/div/table/tbody/tr[1]/td[1]').click
                 
end 

When(/^I am on the retrieve original documents  screen  the accompanying evidence is visible as thumbnails$/) do 
 page.should have_xpath('//*[@id="container0"]/img[1]')

end 

When(/^I click on an amendment form thumbnail the image is expanded to large image$/) do 
	find(:id, 'thumbnails').click
	#find(:xpath, '/html/body/form/div/div/div/div[2]/div[1]/div[2]/div/div/div/img[1]').click
end 


When(/^I am on a Large image of the amendment form I can zoom in$/) do 
   if is_gui?
       find(:xpath, '//*[@id="container0"]/img[2]').click
   else
       find(:xpath, '//*[@id="container0"]/img[2]').trigger('click')
   end
  #container0>div
  #all('.zoomcontrols')[0].click
 thing = find(:csspath, '#container0 > div:nth-child(2)')
 expect(thing.text).to eq "2x Magnify"
end 

When(/^I am on a Large image of the amendment form I can zoom out$/) do 
  if is_gui?
    find(:xpath, '//*[@id="container0"]/img[3]').click
  else
    find(:xpath, '//*[@id="container0"]/img[3]').trigger('click')
  end
   
  #container0>div
  #all('.zoomcontrols')[0].click
  #container0 > div:nth-child(2)
   
 thing = find(:csspath, '#container0 > div:nth-child(2)')
  expect(thing.text).to eq "1x Magnify"
end 

When(/^I must have a registration number before the continue button can be clicked$/) do 
   fill_in('reg_no', :with => $regnote)
   sleep(1)
end  

Then(/^I can click the amendment screen continue button to go to the next screen$/) do 
  click_button('continue')
end 

Given(/^I am on the bankruptcy details screen$/) do #amend details screen
  expect(page).to have_content('Amend details')
end 

When(/^the application details become visible they must be the correct ones for the registration detailed on the previous screen$/) do 
 #database check
end 

When(/^I can click the amendment screen continue button the system will go next screen$/) do 
  #no action needed due to screen changes 
end 

Then(/^the next screen will be the amendment confirmation screen$/) do 
   #no action needed due to screen changes 
end 

When(/^I can click the reject button on the amendment screen the system will go next screen$/) do
  click_button('reject')
end

Then(/^the next screen will be the amendment rejection screen$/) do
  expect(page).to have_content('Application Rejected')
  find(:id, 'return_to_worklist').click
end

When(/^I can click the amend button the system will go next screen$/) do
  expect(page).to have_content('Date Received')

end

Given(/^I am on the bankruptcy details worklist screen with amendments still listed$/) do
   #$regnote2 = create_registration
   $regnote2 = '50013'
   find(:xpath,'html/body/div[1]/div/div/div[3]/div/table/tbody/tr[1]/td[1]').click
end

When(/^I must have a different registration number before the continue button can be clicked$/) do
  fill_in('reg_no', :with => $regnote2)
  click_button('continue')
  
end

When(/^I am on the amend details screen I can click on the amend name button$/) do 
  find(:id, 'amend_name').click
end 

When(/^the Debtor details screen is displayed I can overtype the details$/) do 
  fill_in('forenames', :with => 'Nicola')
  fill_in('surname', :with => 'Andrews')
end 

When(/^click the continue button the new details are stored$/) do 
  click_button('continue')
end 

When(/^I click the add button for alias name the debtor alias name screen is displayed$/) do 
  find(:id, 'add_alias').click
end 

When(/^I enter the alias names$/) do 
  fill_in('forenames', :with => 'Sue')
  fill_in('surname', :with => 'Watchman')
end 

When(/^I enter the additional alias names$/) do
   fill_in('forenames', :with => 'Jack')
  fill_in('surname', :with => 'Jones')
end

When(/^I select an alias name and click the remove button the name is removed from the screen$/) do
  find(:id,'remove_alias_1').click
end

When(/^I click on the add button for address the address details screen is displayed$/) do 
  find(:id, 'add_address').click
end 

When(/^I enter the address details$/) do 
  fill_in('address1', :with => '1 long Street')
  fill_in('address2', :with => 'Plymouth')
  fill_in('county', :with => 'DEVON')
  fill_in('postcode', :with => 'PL1 1AB')
end

When(/^I am on the amend details screen I can click on the amend address button$/) do 
  find(:id,'amend_address_1').click 
end 

When(/^the address details screen is displayed I can overtype the details$/) do 
  fill_in('address1', :with => '1 longer changed Street') 
end 

When(/^I select an address and click the remove button the address is removed from the screen$/) do
  find(:id,'remove_address_1').click
end

When(/^I am on the amend details screen I can click on the amend court button$/) do 
 find(:id, 'amend_court').click 
end 

When(/^the court details screen is displayed I can overtype the details$/) do 
  fill_in('court', :with => 'Devon County Court')
  fill_in('ref', :with =>'123 2015')
  
end 


Then(/^I can click submit button to save all new information$/) do 
  find(:id, 'save_changes').click
end 

Given(/^the amendment confirmation screen is visible$/) do
   expect(page).to have_content('Application Complete')
   expect(page).to have_content('Your application reference')
end

When(/^the amendments application has been submitted the unique identifier is displayed to the user on the screen$/) do
  date_format = Date.today.strftime('%d.%m.%Y')
  registereddate = find(:id, 'registereddate').text
  puts(registereddate)
  expect(registereddate).to eq 'Registered on '+ date_format
end

Then(/^the user can return to the worklist from the amendment screens$/) do
    expect(page).to have_content('Application Complete')
    find(:id, 'return_to_worklist').click
end

Given(/^the application has been amended$/) do
   $regnote3 = '50010'
   find(:xpath,'html/body/div[1]/div/div/div[3]/div/table/tbody/tr[1]/td[1]').click
   fill_in('reg_no', :with => $regnote3)
   click_button('continue')
   find(:id, 'save_changes').click
 # step "I am on the bankruptcy details worklist screen with amendments still listed"
  #step "I must have a different registration number before the continue button can be clicked"
  #step "I can click submit button to save all new information"
  step "the user can return to the worklist from the amendment screens"
end

When(/^we check the bankruptcy database record there must be a indicator for amended$/) do
  #pending # Write code here that turns the phrase above into concrete actions
end

Then(/^the indicator must have a value for amended$/) do
  PostgreSQL.connect('landcharges')
  result = PostgreSQL.query("SELECT a.cancelled_by FROM register_details a, register b WHERE b.registration_no=#{$regnote2} AND b.details_id = a.id")
  expect(result.values[0][0]).not_to be_empty
end