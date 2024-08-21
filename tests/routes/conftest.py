import json
import pytest

@pytest.fixture(autouse=True)
def mock_requests(requests_mock):
    """ Ensure no network request goes out during route tests, here.
    """
    pass

@pytest.fixture
def lesson_11_rubric():
    """ Creates a rubric in CSV format, based on csd3-2023-L11.
    """

    output = """Key Concept,Extensive Evidence,Convincing Evidence,Limited Evidence,No Evidence
Program Development - Program Sequence,You sequenced the program well and and all elements on the screen appear as intended.,Your program may contain a few incorrectly sequenced code resulting in a few elements hidden behind others unintentionally.,"Your program has significant sequencing errors, resulting in many elements unintentionally hidden or overlapping others.","Errors in program sequencing are significant enough to keep the output from resembling the intended scene."
Modularity - Sprites and Sprite Properties,"At least 2 sprites created, each with at least one property updated after creation.","At least 1 sprite created with at least one property updated after creation.","At least 1 sprite created. No properties updated after creation.","No sprites are used in the program."
Position - Elements and the Coordinate System,"At least 2 shapes, 2 sprites, and 2 lines of text are placed correctly on the screen using the coordinate system.","At least 1 shape, 2 sprites, and 1 line of text are placed on the screen using the coordinate system.","A cumulative of at least a total of 3 elements are placed on the screen using the coordinate system (e.g 2 sprites & 1 line of text or 1 sprite, 1 shape, & 1 line of text)","No elements (shapes, sprites, or text) are placed on the screen using the coordinate system."
"""
    yield output

@pytest.fixture
def stub_code():
    yield 'stub-code'

@pytest.fixture
def stub_prompt():
    yield 'stub-prompt'

@pytest.fixture
def claude_model():
    yield 'anthropic.claude-3-5-sonnet-20240620-v1:0'

@pytest.fixture
def bedrock_claude_model(claude_model):
    yield 'bedrock.' + claude_model

@pytest.fixture
def lesson_11_request_data(stub_code, stub_prompt, lesson_11_rubric, bedrock_claude_model):
    rubric = lesson_11_rubric
    request_data = {
        "code": stub_code,
        "prompt": stub_prompt,
        "rubric": rubric,
        "api-key": 'test-api-key',
        "examples": "[]",
        "model": bedrock_claude_model,
        "remove-comments": "1",
        "num-responses": "2",
        "temperature": "0.2",
    }
    yield request_data

@pytest.fixture
def lesson_11_eval():
    yield [
        {
            "Key Concept": "Program Development - Program Sequence",
            "Observations": "The program appears to be well-sequenced, with background set first, sprites created and positioned, sprite properties set, sprites drawn, and text added last.",
            "Evidence": "Lines 1-9: The program sets the background, creates and positions sprites, sets their properties, and draws them in the correct order.\n`background(\"black\");\nvar animalhead_duck1 = createSprite(352, 200);\nvar animalhead_frog_1 = createSprite(46, 200);\nanimalhead_duck1.setAnimation(\"animalhead_duck1\");\nanimalhead_frog_1.setAnimation(\"animalhead_frog_1\");\nanimalhead_frog_1.scale = 0.4;\nanimalhead_duck1.scale = 0.4;\ndrawSprites();`\n\nLines 10-12: Text is added after sprites are drawn.\n`textSize(20);\nfill(\"white\");\ntext(\"Fortnite\", 175, 200);`",
            "Reason": "The program demonstrates a logical sequence of operations. The background is set first, then sprites are created and their properties are set. The drawSprites() function is called to render the sprites, and finally, the text is added. This sequence ensures that all elements appear as intended, with no overlapping or hiding issues. Decision: Extensive Evidence",
            "Grade": "Extensive Evidence"
        },
        {
            "Key Concept": "Modularity - Sprites and Sprite Properties",
            "Observations": "The program creates two sprites and updates properties for both after creation.",
            "Evidence": "Lines 2-3: Two sprites are created.\n`var animalhead_duck1 = createSprite(352, 200);\nvar animalhead_frog_1 = createSprite(46, 200);`\n\nLines 4-7: Properties of both sprites are updated after creation.\n`animalhead_duck1.setAnimation(\"animalhead_duck1\");\nanimalhead_frog_1.setAnimation(\"animalhead_frog_1\");\nanimalhead_frog_1.scale = 0.4;\nanimalhead_duck1.scale = 0.4;`",
            "Reason": "The program creates two distinct sprites: animalhead_duck1 and animalhead_frog_1. For both sprites, it sets the animation and scale properties after creation. This meets the criteria for Extensive Evidence as there are at least 2 sprites created, each with at least one property updated after creation. Decision: Extensive Evidence",
            "Grade": "Extensive Evidence"
        },
        {
            "Key Concept": "Position - Elements and the Coordinate System",
            "Observations": "The program places two sprites and one line of text using the coordinate system. No shapes are created.",
            "Evidence": "Lines 2-3: Two sprites are positioned using coordinates.\n`var animalhead_duck1 = createSprite(352, 200);\nvar animalhead_frog_1 = createSprite(46, 200);`\n\nLine 12: One line of text is positioned using coordinates.\n`text(\"Fortnite\", 175, 200);`",
            "Reason": "The program demonstrates the use of the coordinate system to place elements on the screen. It positions two sprites (animalhead_duck1 and animalhead_frog_1) and one line of text (\"Fortnite\") using x and y coordinates. However, it does not create any shapes using functions like rect, ellipse, circle, quad, or triangle. According to the rubric, for Convincing Evidence, we need at least 1 shape, 2 sprites, and 1 line of text. While the program meets the criteria for sprites and text, it lacks any shapes. Therefore, it falls under the Limited Evidence category. Decision: Limited Evidence",
            "Grade": "Limited Evidence"
        }
    ]

def get_bedrock_claude_response_data(eval_data):
    eval_json = json.dumps(eval_data)
    return {
        "id": "msg_bdrk_01234567890abcdefghijklm",
        "type": "message",
        "role": "assistant",
        "model": "claude-3-5-sonnet-20240620",
        "content": [
            {
                "type": "text",
                "text": eval_json
            }
        ],
        "stop_reason": "end_turn",
        "stop_sequence": None,
        "usage": {
            "input_tokens": 1397,
            "output_tokens": 972
        }
    }

@pytest.fixture
def lesson_11_response_body(lesson_11_eval):
    response_data = get_bedrock_claude_response_data(lesson_11_eval)
    yield json.dumps(response_data)

@pytest.fixture
def lesson_11_response_body_mismatched(lesson_11_eval):
    eval = lesson_11_eval
    eval[0]["Key Concept"] = "Bogus Key Concept"
    response_data = get_bedrock_claude_response_data(eval)
    yield json.dumps(response_data)

@pytest.fixture
def lesson_11_response_body_too_large():
    unparsable_json = '["unparsable JSON"'
    response_data = get_bedrock_claude_response_data(unparsable_json)
    response_data['stop_reason'] = 'max_tokens'
    yield json.dumps(response_data)
