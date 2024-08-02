import pytest

from lib.assessment.assess import get_example_key_concepts

def test_get_example_key_concepts_from_tsv():
    """ Tests lib.assessment.assess.get_example_key_concepts()
    """

    expected_concepts = [
        'Modularity - Sprites and Sprite Properties',
        'Position and Movement',
        'Optional “Stretch” Feature - Variables'
    ]
    with open('tests/data/example.tsv', 'r') as f:
        example_tsv = f.read()

    actual_concepts = get_example_key_concepts(example_tsv, 'tsv')

    assert set(expected_concepts) == set(actual_concepts)

def test_get_example_key_concepts_from_json():
    """ Tests lib.assessment.assess.get_example_key_concepts()
    """

    expected_concepts = [
        'Modularity - Sprites and Sprite Properties',
        'Position and Movement',
        'Optional “Stretch” Feature - Variables'
    ]
    with open('tests/data/example.json', 'r') as f:
        example_tsv = f.read()

    actual_concepts = get_example_key_concepts(example_tsv, 'json')

    assert set(expected_concepts) == set(actual_concepts)
