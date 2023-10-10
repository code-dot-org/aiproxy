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

* **Response**: `application/json`: Data and metadata related to the response. The `data` is the list of key concepts, assessment values, and reasons. The `metadata` is the input to the AI and some usage information. `n` is the number of responses asked for in the input. Example below.

```
{
  "metadata": {
    "time": 39.43,
    "student_id": 1553633,
    "usage": {
      "prompt_tokens": 454,
      "completion_tokens": 1886,
      "total_tokens": 2340
    },
    "request": {
      "model": "gpt4",
      "temperature": 0.2,
      "messages": [ ... ],
      "n": 3
    }
  },
  "data": [
    {
      "Key Concept": "Program Development 2",
      "Observations": "The program uses whitespace  good nami [... snipped for brevity ...]. The code is easily readable.",
      "Grade": "Extensive Evidence",
      "Reason": "The program code effectively uses whitespace, good naming conventions, indentation and comments to make the code easily readable."
    }, {
      "Key Concept": "Algorithms and Control Structures",
      "Observations": "Sprite interactions occur at lines 48-50 (player touches burger), 52 (sw[... snipped for brevity ...]",
      "Grade": "Extensive Evidence",
      "Reason": "The game includes multiple different interactions between sprites, responds to multiple types of user input (e.g. different arrow keys)."
    }
  ]
```

`(GET|POST) /test/assessment`: Issue a test rubric assessment to the AI agent and wait for a response.

* `model`: The model to use. Default: `gpt-4`
* `api-key`: The API key associated with the model. Default: the configured key
* `remove-comments`: When `1`, attempts to strip comments out of the code before assessment. Default: 0
* `num-responses`: The number of times it should ask the AI model. It votes on the final answer. Default: 1
* `num-passing-grades`: The number of grades to consider 'passing'. Defaults: 2 (pass fail)
* `temperature`: The 'temperature' value for ChatGPT LLMs.

* **Response**: `application/json`: A set of data and metadata where `data` is a list of key concepts, assessment values, and reasons. See above.
