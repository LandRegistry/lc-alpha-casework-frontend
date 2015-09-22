def is_dev_or_demo?
    if ENV.has_key?('ENVIRONMENT') && ENV['ENVIRONMENT'] == 'INTEGRATION'
        false
    else
        true
    end
end
