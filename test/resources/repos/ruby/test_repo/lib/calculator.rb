class Calculator
  def initialize
    @precision = 2
  end

  def add(a, b)
    (a + b).round(@precision)
  end

  def subtract(a, b)
    (a - b).round(@precision)
  end

  def multiply(a, b)
    (a * b).round(@precision)
  end

  def divide(a, b)
    raise ArgumentError, "Division by zero" if b == 0
    (a / b.to_f).round(@precision)
  end
end

module MathUtils
  def self.square(n)
    n * n
  end

  def self.cube(n)
    n * n * n
  end

  def self.factorial(n)
    return 1 if n <= 1
    n * factorial(n - 1)
  end
end
