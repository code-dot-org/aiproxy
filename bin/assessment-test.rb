#!/usr/bin/env ruby

require 'net/http'
require 'uri'
require 'json'

# This is best done with a better client library than the
# standard one in Ruby, but we wanted this test to work with
# a stock install for the sake of quick testing.

uri = URI('http://localhost:80')
uri.path = '/assessment'

code = File.read('tests/data/u3l13_01.js')
prompt = File.read('tests/data/u3l13.txt')
rubric = File.read('tests/data/u3l13.csv')
example_code = File.read('tests/data/example.js')
example_rubric = File.read('tests/data/example.tsv')
examples = [[example_code, example_rubric]]

form_data = [
  ['model', 'gpt-4-0613'],
  ['code', code],
  ['prompt', prompt],
  ['rubric', rubric],
  ['examples', examples.to_json],
  ['remove-comments', '1'],
  ['num-responses', '3'],
  ['num-passing-labels', '2'],
  ['temperature', '0.2'],
]

request = Net::HTTP::Post.new(uri)
request.set_form form_data, 'multipart/form-data'
response = Net::HTTP.start(uri.hostname, uri.port) do |http|
  http.request(request)
end

puts "Content-Type: #{response.content_type}"
puts response.body
