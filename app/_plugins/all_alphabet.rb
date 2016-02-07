module Jekyll
  module AllAlphabetFilter
    def all_alphabet(input)
      if /^[A-Za-z0-9\s]+$/.match(input)
        "all-alphabet"
      else
        "non-alphabet"
      end
    end
  end
end

Liquid::Template.register_filter(Jekyll::AllAlphabetFilter)
