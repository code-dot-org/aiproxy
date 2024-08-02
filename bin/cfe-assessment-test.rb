#!/bin/env ruby

require 'net/http'
require 'uri'
require 'json'

# This is best done with a better client library than the
# standard one in Ruby, but we wanted this test to work with
# a stock install for the sake of quick testing.

uri = URI('http://localhost:80')
uri.path = '/assessment'

params = JSON.parse(File.read('tests/data/cfe_params.json'))
code = File.read('tests/data/cfe_code.js')
prompt = File.read('tests/data/cfe_prompt.txt')
rubric = File.read('tests/data/cfe_rubric.csv')

form_data = [
  ['model', params['model']],
  ['code', code],
  ['prompt', prompt],
  ['rubric', rubric],
  ['remove-comments', params['remove-comments']],
  ['num-responses', params['num-responses']],
  ['num-passing-labels', params['num-passing-grades']],
  ['temperature', params['temperature']],
  ['code-feature-extractor', params['code-feature-extractor'].join(",")]
]
request = Net::HTTP::Post.new(uri)
request.set_form form_data, 'multipart/form-data'
puts request.inspect
response = Net::HTTP.start(uri.hostname, uri.port) do |http|
  http.request(request)
end

puts "Content-Type: #{response.content_type}"
puts response.body
