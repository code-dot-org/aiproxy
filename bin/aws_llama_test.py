#!/usr/bin/env python

import boto3
import json
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
