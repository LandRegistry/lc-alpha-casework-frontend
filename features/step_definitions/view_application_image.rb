Given(/^I am on the view application screen$/) do 
  visit('http://localhost:5010')
end 

When(/^I have selected to view specific the application list$/) do 
    visit( "http://localhost:5010/get_list?appn=bank_regn" )
    find(:xpath,"html/body/div[1]/div/div/div[3]/div/table/tbody/tr[1]/td[1]/a").click
    
end 

When(/^the image of the application is displayed I can click on all available pages$/) do 
    find(:id, "thumbnail_2").click
    find(:id, "thumbnail_3").click
    find(:id, "thumbnail_1").click 
end 

When(/^I am on a page I can zoom out$/) do 
  find(:xpath, "//img[@title='Zoom Out']").click
end 

Then(/^I am on a page I can zoom in$/) do
    find(:xpath, "//img[@title='Zoom In']").click
    
end 

