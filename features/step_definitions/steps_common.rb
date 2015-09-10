require 'capybara'
require 'capybara/dsl'
require 'capybara/rspec'
require 'rspec'
require 'capybara/cucumber'
require 'net/http'
require 'json'
require 'pg'

Capybara.default_driver = :selenium



def create_registration
    no_alias = '{"key_number":"9056267","application_type":"PA(B)", "document_id":"22", "application_ref":"9763603","date":"2014-11-12","debtor_name":{"forenames":["Lamar","Sigmund"],"surname":"Effertz"},"debtor_alternative_name":[],"gender":"N/A","occupation":"Ship builder","residence":[{"address_lines":["942 Carley Unions","Cullenberg","Dimitrimouth"],"county": "Buckinghamshire", "postcode":"QF47 0HG"}],"residence_withheld":false,"business_address":{"address_lines":["122 Leuschke Creek","Alvaburgh"],"county": "Fife", "postcode":"NO03 1EU"},"date_of_birth":"1974-10-03","investment_property":[]}'
    uri = URI("http://localhost:5004")
    http = Net::HTTP.new(uri.host, uri.port)

    request = Net::HTTP::Post.new("/registration")
    request.body = no_alias
    request["Content-Type"] = "application/json"

    response = http.request(request)
    puts response.body
    data = JSON.parse(response.body)


    data['new_registrations'][0]
end
