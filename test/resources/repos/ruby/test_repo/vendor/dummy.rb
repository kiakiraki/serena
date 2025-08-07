require './lib.rb'

class DummyClass
  def do_something
    Calculator.new.add(1, 2)
  end
end
