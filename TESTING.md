# Testing

## Unit Tests

The `./tests` directory contains three categories of test:

* `unit`: Unit tests for library functions in the `./lib` path.
* `routes`: Tests routes and their helpers in the `./src` as a unit.
* `accuracy`: Tests accuracy against thresholds by calling OpenAI. Not run by default.

All tests are using [pytest](https://docs.pytest.org/en/7.4.x/).

To run the test suite, you can run: `./bin/test` to build and run the
docker container and invoke pytest. You can pass any arguments to pytest
via the command. For instance, the `-k` argument can filter tests by name:

```
# Run only tests with 'label' in the name:
./bin/test.sh -k label
```

This will run a container without starting the server itself. You can also
just run `pytest` within a running container's shell session by using the
`pytest` command within the `/app` directory in the container:

```
PYTHONPATH=/app pytest
```

## Accuracy Tests

**Running the Accuracy test hits the OpenAI endpoint and is expensive! Only run this test infrequently**

To run the accuracy threshold test, follow directions in `README.md` to set up your local
environment for running the Rubric Tester. You can then run `./bin/test_accuracy.sh` to run
tests locally, including the accuracy threshold test.

You can pass any arguments to pytest with this script. For instance, the `-k` argument can filter tests by name:

```
# Run only tests with 'accuracy' in the name:
./bin/test_accuracy.sh -k accuracy
```

## Scripted

This assumes you have built and are running the container as depicted in the main `README.md`.
In that case, you have a running server on port 5000 (or 80).

You can run the provided Ruby script to issue a request to the server on your native machine.
To do so, if you have some system Ruby installed, you can invoke this command (at the root
of this repository):

```
ruby ./bin/assessment-test.rb
```

This will ping the running server's `/assessment` route building out the appropriate `POST`
request with the test data in the `test` path of the repository.

## Curl

This assumes you have built and are running the container as depicted in the main `README.md`.
In that case, you have a running server on port 5000 (or 80).

You can issue a "test" rubric assessment using hard-coded content that is found in the
`test/data` path by using the `/test/assessment` URL. Here, I'm using `curl` to show
me the headers and send a `POST` to that route (may take 30 to 50 seconds):

```
curl localhost:5000/test/assessment -i --header "Content-Type:multipart/form-data" --form "num-responses=3"
```

This gives me this response:

```
HTTP/1.1 200 OK
Content-Length: 10758
Content-Type: application/json
Date: Tue, 09 Jan 2024 01:23:17 GMT
Server: waitress

{"data":[{"Key Concept":"Program Development 2","Label":"Extensive Evidence","Observations":"The program uses whitespace effectively, has good indentation, and uses good naming conventions. The comments are clear and helpful, making the code easily readable.","Reason":"<b>Votes: [Extensive Evidence, Extensive Evidence, Convincing Evidence]</b><br>The program code effectively uses whitespace, good naming conventions, indentation and comments to make the code easily readable."},{"Key Concept":"Algorithms and Control Structures","Label":"Convincing Evidence","Observations":"Sprite interactions occur at lines 48-49 (displacement) and 44-46 (touching). The program responds to user input at lines 30-32 (up key), 34-37 (left key), and 39-42 (right key).","Reason":"<b>Votes: [Convincing Evidence, Extensive Evidence, Convincing Evidence]</b><br>The game includes at least one type of sprite interaction and responds to user input."},{"Key Concept":"Position and Movement","Label":"Convincing Evidence","Observations":"The program generates movement at lines 23-24 (sword and sword2 sprites), line 28 (player falling), lines 30-32 (player moving up), lines 34-37 (player moving left), and lines 39-42 (player moving right). The movement involves acceleration at lines 28, 30-32, 34-37, and 39-42.","Reason":"<b>Votes: [Convincing Evidence, Extensive Evidence, Convincing Evidence]</b><br>The program includes some complex movement, such as acceleration."},{"Key Concept":"Variables","Label":"Extensive Evidence","Observations":"Variables updated inside the draw loop: Line 28 (player.velocityY), Line 32 (player.velocityY), Line 36 (player.velocityX), Line 40 (player.velocityX), Line 46 (burger.x, burger.y). All these variables affect the user's experience of playing the game.","Reason":"<b>Votes: [Convincing Evidence, Extensive Evidence, Extensive Evidence]</b><br>The game includes multiple variables or sprite properties that are updated during the game and affect the user's experience of playing the game."}],"metadata":{"agent":"openai","request":{"messages":[{"content":"You are a teaching assistant whose job is to assess a student program written in\njavascript based on several Key Concepts. For each Key Concept you will answer by\ngiving the highest grade which accurately describes the student's program:\nExtensive Evidence, Convincing Evidence, Limited Evidence, or No\nEvidence. You will also provide a reason explaining your grade for each\nKey Concept, citing examples from the code to support your decision when possible.\n\nThe student's code should contain a method called `draw()` which will be\nreferred to as the \"draw loop\". Any code outside of the draw loop will be run\nonce, then any code inside the draw loop will be run repeatedly, like this:\n```\n// student's code\n\nwhile (true) {\n  draw();\n}\n```\n\nPlease keep in mind that acceleration occurs when the velocity of a sprite is changed incrementally within the draw loop, such as in these examples:\n* `sprite.velocityX += 0.2;`\n* `sprite.velocityY -= 1;`\n* `foo.velocityX = foo.velocityX + 5;`\n* `foo.velocityY = foo.velocityY - 10;`\n\nThe following examples do not count as acceleration, because they set the velocity to a specific value, rather than changing it incrementally:\n* `sprite.velocityX = 5;`\n* `sprite.velocityY = -10;`\n\nThe following does not count as acceleration, because it sets the velocity to a random value, rather than changing it incrementally:\n* `foo.velocityX = randomNumber(-5, 5);`\n\nThe student's code will access an API defined by Code.org's fork of the p5play\nlibrary. This API contains methods like createSprite(), background(), and drawSprites(),\nas well as sprite properties like x, y, velocityX and velocityY.\n\nIn order to help you evaluate the student's work, you will be given a rubric in\nCSV format. The first column provides the list of Key Concepts to evaluate,\nthe second column, Instructions, tells you what aspects of the code to consider\nwhen choosing a grade. the next four columns describe what it means for a program\nto be classified as each of the four possible grades.\n\nwhen choosing a grade for each Key Concept, please follow the following steps:\n1. follow the instructions in the Instructions column from the rubric to generate observations about the student's program. Include the result to the Observations column in your response.\n2. based on those observations, determine the highest grade which accurately describes the student's program. Write this result to the Grade column in your response.\n3. write a reason for your grade in the Reason column, citing evidence from the Observations column when possible.\n\nplease provide your evaluation formatted as a TSV table including a header row\nwith column names Key Concept, Observations, Grade, and Reason. There should be one\nnon-header row for each Key Concept.\n\nThe student's work should be evaluated based on what they have added beyond the\nstarter code that was provided to them. Here is the starter code:\n```\n// GAME SETUP\n// create player, target, and obstacles\nvar player = createSprite(200, 100);\nplayer.setAnimation(\"fly_bot\");\nplayer.scale = 0.8;\n\n\nfunction draw() {\n  background(\"lightblue\");\n\n  // FALLING\n\n  // LOOPING\n\n\n  // PLAYER CONTROLS\n  // change the y velocity when the user clicks \"up\"\n\n  // decrease the x velocity when user clicks \"left\"\n\n  // increase the x velocity when the user clicks \"right\"\n\n  // SPRITE INTERACTIONS\n  // reset the coin when the player touches it\n\n  // make the obstacles push the player\n\n\n  // DRAW SPRITES\n  drawSprites();\n\n  // GAME OVER\n  if (player.x < -50 || player.x > 450 || player.y < -50 || player.y > 450) {\n    background(\"black\");\n    textSize(50);\n    fill(\"green\");\n    text(\"Game Over!\", 50, 200);\n  }\n\n}\n```\n\n\nRubric:\nKey Concept,Instructions,Extensive Evidence,Convincing Evidence,Limited Evidence,No Evidence\nProgram Development 2,(1) does the program effectively use whitespace? (2) does the program use good naming conventions? (3) does the program have good indentation? (4) does the program have good comments? (5) is the code easily readable?,\"The program code effectively uses whitespace, good naming conventions, indentation and comments to make the code easily readable.\",\"The program code makes use of whitespace, indentation, and comments.\",The program code has few comments and does not consistently use formatting such as whitespace and indentation.,The program code does not contain comments and is difficult to read.\nAlgorithms and Control Structures,\"(1) list the line number of each sprite interaction, and note the type of interaction. (2) list the line number of each place the program responds to user input, and note the type of user input (e.g. which key or mouse event).\",\"The game includes multiple different interactions between sprites, responds to multiple types of user input (e.g. different arrow keys).\",The game includes at least one type of sprite interaction and responds to user input.,\"The game responds to user input through a conditional, but has no sprite interactions.\",The game includes no conditionals.\nPosition and Movement,\"list the line numbers of each place the program generates movement, and note whether the movement involves acceleration, keeping in mind that acceleration is incremental change to velocity (e.g. `sprite.velocityX = sprite.velocityX + 1` or `sprite.velocityY -= 1`).\",\"Complex movement such as acceleration, moving in a curve, or jumping is included in multiple places in the program.\",\"The program includes some complex movement, such as jumping, acceleration, or moving in a curve.\",\"The program does not include complex movement such as jumping, acceleration or moving in a curve. However, the program does include simple independent movement, such as a straight line, rotation or bouncing.\",\"There is no movement in the program, other than direct user control.\"\nVariables,\"(1) list the line number of every place a variable (including sprite properties) is updated inside the draw loop (2) for each variable or sprite property, describe whether it affects the user's experience of playing the game.\",The game includes multiple variables or sprite properties that are updated during the game and affect the user's experience of playing the game.,The game includes at least one variable or sprite property that is updated during the game and affects the user's experience of playing the game.,There is at least one variable or sprite property updated in the program.,\"There are no variables or sprite properties, or they are not updated.\"\n","role":"system"},{"content":"// GAME SETUP\n// create player, target, and obstacles\nvar player = createSprite(200, 100);\nplayer.setAnimation(\"player\");\nplayer.scale = 0.8;\nvar burger = createSprite(randomNumber(0,400),randomNumber(0,400));\nburger.setAnimation(\"burger\");\nburger.scale = 0.2;\nburger.setCollider(\"circle\");\nvar sword = createSprite(-50, randomNumber(0, 400));\nsword.setAnimation(\"sword\");\nsword.scale = 0.5;\nvar sword2 = createSprite(randomNumber(0, 400), -50);\nsword2.setAnimation(\"sword2\");\nsword2.scale = 0.5;\nsword.velocityX = 3;\nsword2.velocityY = 3;\n\n\nfunction draw() {\n  background(\"green\");\n  \n  // FALLING\n  player.velocityY+=0.7;\n  \n  // LOOPING\n    if (sword.x>425){\n      sword.y=-50;\n      sword.x=randomNumber(0, 400);\n    }\n     if (sword2.x>425){\n      sword2.y=-50;\n      sword2.x=randomNumber(0, 400);\n     }\n  \n  // PLAYER CONTROLS\n  // change the y velocity when the user clicks \"up\"\n    if (keyDown(\"up\")) {\n       player.velocityY-=1.5;\n     }\n      \n  // decrease the x velocity when user clicks \"left\"\n      if (keyDown(\"LEFT\")) {\n       player.velocityX-=0.1;\n       \n     }\n  // increase the x velocity when the user clicks \"right\"\n     if (keyDown(\"RIGHT\")) {\n       player.velocityX+=0.1;\n       \n     }\n  // SPRITE INTERACTIONS\n  // reset the coin when the player touches it\n      if (player.isTouching(burger)) {\n        burger.x=randomNumber(0, 400);\n        burger.y=randomNumber(0,400);\n      }\n      \n  // make the obstacles push the player\n  sword.displace(player);\n  sword2.displace(player);\n  // DRAW SPRITES\n  drawSprites();\n  \n  // GAME OVER\n  if (player.x < -50 || player.x > 450 || player.y < -50 || player.y > 450) {\n    background(\"black\");\n    textSize(50);\n    fill(\"blue\");\n    text(\"Game Over!\", 50, 200);\n  }\n  \n}\n","role":"user"}],"model":"gpt-4-0613","n":3,"temperature":0.2},"student_id":"student","time":15.187586307525635,"usage":{"completion_tokens":1045,"prompt_tokens":1897,"total_tokens":2942}}}
```

If you want a cleaner response, ignore printing the headers and use Python as well:

```
curl localhost:5000/test/assessment --header "Content-Type:multipart/form-data" --form "num-responses=3" | python -m json.tool
```
