module Jekyll
    module AllowBibtexFields
      def allowBibtexFields(input)
        allowed_fields = @context.registers[:site].config['allowed_bibtex_fields']
        
        # Keep only lines that match allowed fields
        all_lines = input.lines
        output = all_lines.select do |line|
          allowed_fields.any? { |field| line.match?(/^.*\b#{field}\b *= *\{.*$/) } || 
          line.match?(/^@\w+\{/) ||  # Keep the @article line
          line.match?(/^\s*}\s*$/)    # Keep the closing brace line
        end
  
        # Clean superscripts in author lists
        result = output.join
        result = result.gsub(/^.*\bauthor\b *= *\{.*$\n/) { |line| line.gsub(/[*†‡§¶‖&^]/, '') }
  
        return result
      end
    end
  end
  
  Liquid::Template.register_filter(Jekyll::AllowBibtexFields)