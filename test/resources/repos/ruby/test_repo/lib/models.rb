class User
  attr_accessor :name, :email, :age

  def initialize(name, email, age = 18)
    @name = name
    @email = email
    @age = age
  end

  def self.from_hash(hash)
    new(hash[:name] || hash['name'], 
        hash[:email] || hash['email'], 
        hash[:age] || hash['age'])
  end

  def to_hash
    {
      name: @name,
      email: @email,
      age: @age
    }
  end

  def adult?
    @age >= 18
  end

  def greet
    "Hello, I'm #{@name}"
  end

  def full_info
    "#{@name} (#{@email}) - Age: #{@age}"
  end
end

class Product
  attr_accessor :name, :price, :category

  def initialize(name, price, category = 'general')
    @name = name
    @price = price
    @category = category
  end

  def self.from_hash(hash)
    new(hash[:name] || hash['name'], 
        hash[:price] || hash['price'], 
        hash[:category] || hash['category'])
  end

  def to_hash
    {
      name: @name,
      price: @price,
      category: @category
    }
  end

  def discounted_price(discount_rate = 0.1)
    @price * (1 - discount_rate)
  end

  def formatted_price
    "$#{sprintf('%.2f', @price)}"
  end
end

module Validations
  def self.validate_email(email)
    email.include?('@') && email.include?('.')
  end

  def self.validate_age(age)
    age.is_a?(Integer) && age >= 0 && age <= 150
  end

  def self.validate_name(name)
    name.is_a?(String) && name.length > 0
  end
end

class Order
  attr_accessor :id, :customer, :items, :total

  def initialize(id, customer)
    @id = id
    @customer = customer
    @items = []
    @total = 0.0
  end

  def self.from_hash(hash)
    order = new(hash[:id] || hash['id'], 
                hash[:customer] || hash['customer'])
    order.items = hash[:items] || hash['items'] || []
    order.total = hash[:total] || hash['total'] || 0.0
    order
  end

  def add_item(product, quantity = 1)
    @items << { product: product, quantity: quantity }
    @total += product.price * quantity
  end

  def remove_item(product)
    @items.reject! { |item| item[:product] == product }
    recalculate_total
  end

  private

  def recalculate_total
    @total = @items.sum { |item| item[:product].price * item[:quantity] }
  end
end
