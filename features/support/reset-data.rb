#!/usr/bin/env ruby


def reset_data
    databases = [
        {
            'name' => 'working',
            'app' => 'casework-working',
            'tables' => ['pending_application']
        },
        {
            'name' => 'db2',
            'app' => 'legacy-db',
            'tables' => ['lc_mock', 'keyholders']
        },
        {
            'name' => 'docstore',
            'app' => 'document-api',
            'tables' => ['documents']
        },
        {
            'name' => 'landcharges',
            'app' => 'bankruptcy-registration',
            'tables' => ['party_address', 'address', 'address_detail', 'party_trading', 'party_name_rel', 'party',
                         'migration_status', 'register', 'register_details', 'audit_log', 'search_details', 'request',
                         'ins_bankruptcy_request', 'party_name']
        }
    ]

    databases.each do |db|
        db_name = db['name']
        db['tables'].each do |table|
            `psql -d #{db_name} -c "DELETE FROM #{table};"`
        end
    end

    `rm ~/*.jpeg`

    databases.each do |database|
        database['tables'].reverse.each do |table|
            data_file = "/vagrant/apps/#{database['app']}/data/#{table}.txt"
            command = "\\COPY #{table} FROM #{data_file} DELIMITER '|' CSV"
            `psql -d #{database['name']} -c "#{command};"`
        end

        database['tables'].reverse.each do |table|
            if table != "lc_mock"
                command = "SELECT setval('#{table}_id_seq', (SELECT MAX(id) FROM #{table})+1);"
                `psql -d #{database['name']} -c "#{command};"`
            end
        end
    end

    ['img30_1.jpeg', 'img32_1.jpeg', 'img34_1.jpeg', 'img36_1.jpeg', 'img38_1.jpeg',
    'img31_1.jpeg', 'img33_1.jpeg', 'img35_1.jpeg', 'img37_1.jpeg', 'img39_1.jpeg', 'img40_1.jpeg',
    'img41_1.jpeg', 'img41_2.jpeg', 'img42_1.jpeg', 'img43_1.jpeg', 'img44_1.jpeg', 'img45_1.jpeg'].each do |image|
        `cp /vagrant/apps/document-api/data/#{image} ~/#{image}`
    end
end

if __FILE__ == $0
    reset_data
end