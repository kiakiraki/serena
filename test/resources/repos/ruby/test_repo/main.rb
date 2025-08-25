require_relative 'lib/calculator'
require_relative 'lib/models'

class DemoClass
  attr_accessor :value

  def initialize(value)
    @value = value
  end

  def print_value
    puts @value
  end

  def calculate_with_tax(tax_rate = 0.1)
    Calculator.new.add(@value, @value * tax_rate)
  end
end

def helper_function(number = 42)
  demo = DemoClass.new(number)
  result = demo.calculate_with_tax
  demo.print_value
  result
end

# Test ERB-like interpolation
def format_message(name, value)
  "Hello #{name}, your value is #{value}"
end

helper_function