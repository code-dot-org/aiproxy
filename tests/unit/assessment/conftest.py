import io
import csv
import json
import random

import pytest


@pytest.fixture
def random_label_generator():
    def gen_random_label():
        return random.choice([
            'Extensive Evidence',
            'Convincing Evidence',
            'Limited Evidence',
            'No Evidence'
        ])

    yield gen_random_label


@pytest.fixture
def code_generator(randomstring):
    """ Creates some example code to use.
    """

    def gen_code():
        return f"""
    function x{randomstring(10)} () {{
        var v{randomstring(10)} = {random.randint(0, 999)};
    }}
    """

    yield gen_code


@pytest.fixture
def code(code_generator):
    yield code_generator()


@pytest.fixture
def prompt():
    """ Creates a generic prompt.
    """

    yield """
You are a teaching assistant for a classroom of kids ages 5 to 15.
You are teaching computer science.
"""

@pytest.fixture
def openai_api_key(randomstring):
    """ Creates a random but reasonable OpenAI API key.
    """

    yield f"sk-{randomstring(48)}"


@pytest.fixture
def rubric(randomstring):
    """ Creates a generic rubric (a CSV string).
    """

    output = io.StringIO()
    writer = csv.writer(output, csv.QUOTE_NONNUMERIC)

    # Header
    writer.writerow(['Key Concept', 'Instructions', 'Extensive Evidence', 'Convincing Evidence', 'Limited Evidence', 'No Evidence'])

    for i in range(0, random.randint(2, 5)):
        key_concept = f"Concept {randomstring(10)}"
        writer.writerow([key_concept, 'no flag', randomstring(20), randomstring(23), randomstring(25), randomstring(15)])

    yield output.getvalue()

@pytest.fixture
def rubric_with_flag(randomstring):
    """ Creates a generic rubric (a CSV string).
    """

    output = io.StringIO()
    writer = csv.writer(output, csv.QUOTE_NONNUMERIC)

    # Header
    writer.writerow(['Key Concept', 'Instructions', 'Extensive Evidence', 'Convincing Evidence', 'Limited Evidence', 'No Evidence'])

    for i in range(0, random.randint(2, 5)):
        key_concept = f"Concept {randomstring(10)}"
        writer.writerow([key_concept, randomstring(20), randomstring(23), randomstring(25), randomstring(15)])
    writer.writerow(['Position - Elements and the Coordinate System', randomstring(20), randomstring(23), randomstring(25), randomstring(15)])

    yield output.getvalue()

@pytest.fixture
def short_rubric(randomstring):
    """ Creates a generic rubric (a CSV string) with a single non-header row.
    """

    output = io.StringIO()
    writer = csv.writer(output, csv.QUOTE_NONNUMERIC)

    # Header
    writer.writerow(['Key Concept', 'Instructions' 'Extensive Evidence', 'Convincing Evidence', 'Limited Evidence', 'No Evidence'])

    # single key concept row
    key_concept = f"Concept {randomstring(10)}"
    writer.writerow([key_concept, 'no flag', randomstring(20), randomstring(23), randomstring(25), randomstring(15)])

    yield output.getvalue()


@pytest.fixture
def example_generator(code, randomstring, random_label_generator):
    """ Creates a random example.
    """

    def gen_example(rubric):
        # Generate the example labels (which are TSV formatted)
        example_rubric = "Key Concept\tObservations\tGrade\tReason\n"

        # Generate a label for each concept
        parsed_rubric = list(csv.DictReader(rubric.splitlines()))
        example_rubric += '\n'.join(
            map(
                lambda key_concept: f'{key_concept}\t{randomstring(10)}\t{random_label_generator()}\t{randomstring(12)}',
                set(x['Key Concept'] for x in parsed_rubric)
            )
        )

        # Return the listing
        return [
            code,
            example_rubric
        ]

    yield gen_example


@pytest.fixture
def examples(example_generator):
    """ Creates a random set of examples to pass into an assessment function.
    """

    def gen_examples(rubric, num_examples=None):
        if num_examples is None:
            num_examples = random.randint(1,  5)

        return list(
            map(
                lambda x: example_generator(rubric),
                range(0, num_examples)
            )
        )
    
    yield gen_examples


@pytest.fixture
def llm_model(randomstring):
    """ Creates a resonable looking llm_model tag.
    """

    yield f"gpt-{randomstring(10)}"


@pytest.fixture
def num_responses():
    """ Creates a valid num_responses value.
    """

    yield random.randint(2, 3)


@pytest.fixture
def temperature():
    """ Creates a valid temperature value.
    """
    
    yield random.random()


@pytest.fixture
def remove_comments():
    """ Creates a valid remove_comments value.
    """

    yield random.randint(1, 2) == 1


@pytest.fixture
def response_type():
    """ Creates a valid response_type value.
    """

    yield 'json'

@pytest.fixture
def student_id():
    """ Returns a reasonable student user id.
    """

    yield str(random.randint(100000, 999999))


@pytest.fixture
def openai_gpt_response(randomstring):
    """ Returns a function that will craft a GPT response for the given rubric.

    This function can, then, generate a GPT response based on a given rubric. It
    can mimic a variety of common failure cases.
    """

    def gen_gpt_response(rubric=None, num_responses=3, disagreements=0, output_type="tsv"):
        # Get the boiler plate one
        gpt_response = json.loads(open('tests/data/gpt_response.json', 'r').read())

        # Update to have the rubric items for the rubric
        gpt_response['choices'] = []

        # Get key concepts from rubric
        parsed_rubric = list(csv.DictReader(rubric.splitlines()))
        key_concepts = set(x['Key Concept'] for x in parsed_rubric)

        assigned_labels = {}
        for key_concept in key_concepts:
            assigned_labels[key_concept] = random.choice([
                'Extensive Evidence',
                'Convincing Evidence',
                'Limited Evidence',
                'No Evidence'
            ])

        disagreements_left = disagreements
        for i in range(0, num_responses):
            choice_data = []
            for key_concept in key_concepts:
                label = assigned_labels[key_concept]

                # Add a disagreement, if requested
                if disagreements_left != 0:
                    label = random.choice(list(set([
                        'Extensive Evidence',
                        'Convincing Evidence',
                        'Limited Evidence',
                        'No Evidence'
                    ]) - set([label])))
                    disagreements_left -= 1

                choice_data.append(gen_rubric_row_data(key_concept, label))

            if output_type == 'json':
                content = json.dumps(choice_data, indent=4)
            else:
                content = gen_tabular_response(choice_data, output_type)

            gpt_response['choices'].append({
                'index': i,
                'message': {
                    'role': 'assistant',
                    'content': content
                },
                'finish_reason': 'stop',
            })

        return gpt_response

    def gen_rubric_row_data(key_concept, label):
        return {
            'Key Concept': key_concept,
            'Observations': randomstring(10),
            'Grade': label,
            'Reason': f"stub-reason-{randomstring(10)}"
        }

    def gen_tabular_response(choice_data, output_type):
        delimiter = '\t'

        if output_type == 'markdown':
            delimiter = ' | '

        if output_type == 'csv':
            delimiter = ','

        content = gen_tabular_response_header(delimiter)
        for row_data in choice_data:
            content += gen_tabular_response_row(row_data, delimiter)
        return content

    def gen_tabular_response_header(delimiter='\t'):
        return f"Key Concept{delimiter}Observations{delimiter}Grade{delimiter}Reason\n"

    def gen_tabular_response_row(data, delimiter='\t'):
        return f"{data['Key Concept']}{delimiter}{data['Observations']}{delimiter}{data['Grade']}{delimiter}{data['Reason']}\n"

    return gen_gpt_response

@pytest.fixture
def context_length_message():
    return "This model's maximum context length is 8192 tokens. However, your messages resulted in 9145 tokens. Please reduce the length of the messages."

@pytest.fixture
def openai_response_too_large(context_length_message):
    """ Returns a GPT response indicating the model's context length was exceeded.
    """

    response_data = {
        "error": {
            "message": context_length_message,
            "type": "invalid_request_error",
            "param": "messages",
            "code": "context_length_exceeded"
        }
    }
    # return json.dumps(response_data)
    return response_data
