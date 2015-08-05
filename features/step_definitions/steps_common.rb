require 'capybara'
require 'capybara/dsl'
require 'capybara/rspec'
require 'rspec'
require 'capybara/cucumber'
require 'net/http'
require 'json'
require 'pg'

Capybara.default_driver = :selenium