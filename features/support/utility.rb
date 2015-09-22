def is_gui?
    if RUBY_PLATFORM =~ /darwin/ # MacOS
        true
    elsif RUBY_PLATFORM =~ /mingw32/ # Windows
        true
    else
        false
    end
end
