#!/usr/bin/env python

import subprocess
import boto3
import json

# check aws access
try:
    result = subprocess.run('aws sts get-caller-identity', shell=True, check=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    print(f"AWS access configured: {result.stdout}")
except subprocess.CalledProcessError as e:
    print(f"AWS access not configured: {e} {e.stderr}Please see README.md and make sure you ran `gem install aws-google` and `bin/aws_access`")
    exit(1)

bedrock = boto3.client(service_name='bedrock-runtime')

body = json.dumps({
    "prompt": "\n\nHuman:explain black holes to 8th graders\n\nAssistant:",
    "max_gen_len": 128,
    "temperature": 0.1,
    "top_p": 0.9,
})

modelId = 'meta.llama2-13b-chat-v1'
accept = 'application/json'
contentType = 'application/json'

response = bedrock.invoke_model(body=body, modelId=modelId, accept=accept, contentType=contentType)

response_body = json.loads(response.get('body').read())

print(response_body.get('generation'))
