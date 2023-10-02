# API

`GET /`: The root serves as a quick status check.

`GET /test`: Will respond with some kind of successful JSON response.

`GET /openai/models`: Will report back information about the available OpenAI models.

`GET /test/openai`: Will issue a small test prompt to OpenAI's ChatGPT.

* `model`: The model to use. Default: `gpt-3.5-turbo`
* `api-key`: The API key associated with the model.

`POST /assessment`: Issue a rubric assessment to the AI agent and wait for a response.

* `model`: The model to use. Default: `gpt-4`
* `api-key`: The API key associated with the model. Default: the configured key
* `code`: The code to assess. Required.
* `prompt`: The system prompt. Required.
* `rubric`: The rubric, as a CSV. Required.
* `remove-comments`: When `1`, attempts to strip comments out of the code before assessment. Default: 0
* `num-responses`: The number of times it should ask the AI model. It votes on the final answer. Default: 1
* `num-passing-grades`: The number of grades to consider 'passing'. Defaults: 2 (pass fail)
* `temperature`: The 'temperature' value for ChatGPT LLMs.

* **Response**: `application/json`: A list of key concepts, assessment values, and reasons. Example below.

```
[{
  "Key Concept": "Program Development 2",
  "Observations": "The program uses whitespace  good nami [... snipped for brevity ...]. The code is easily readable.",
  "Grade": "Extensive Evidence",
  "Reason": "The program code effectively uses whitespace, good naming conventions, indentation and comments to make the code easily readable."
}, {
  "Key Concept": "Algorithms and Control Structures",
  "Observations": "Sprite interactions occur at lines 48-50 (player touches burger), 52 (sw[... snipped for brevity ...]",
  "Grade": "Extensive Evidence",
  "Reason": "The game includes multiple different interactions between sprites, responds to multiple types of user input (e.g. different arrow keys)."
}]
```

`(GET|POST) /test/assessment`: Issue a test rubric assessment to the AI agent and wait for a response.

* `model`: The model to use. Default: `gpt-4`
* `api-key`: The API key associated with the model. Default: the configured key
* `remove-comments`: When `1`, attempts to strip comments out of the code before assessment. Default: 0
* `num-responses`: The number of times it should ask the AI model. It votes on the final answer. Default: 1
* `num-passing-grades`: The number of grades to consider 'passing'. Defaults: 2 (pass fail)
* `temperature`: The 'temperature' value for ChatGPT LLMs.

* **Response**: `application/json`: A list of key concepts, assessment values, and reasons. See above.
