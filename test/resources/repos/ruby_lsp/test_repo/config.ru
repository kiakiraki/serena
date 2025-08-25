require_relative 'main'

class SimpleApp
  def call(env)
    case env['PATH_INFO']
    when '/'
      [200, {'Content-Type' => 'text/plain'}, ['Hello World']]
    when '/api/users'
      users = [User.default_user, User.admin_user]
      [200, {'Content-Type' => 'application/json'}, [users.map(&:to_hash).to_json]]
    else
      [404, {'Content-Type' => 'text/plain'}, ['Not Found']]
    end
  end
end

run SimpleApp.new