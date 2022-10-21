# -*- coding: utf-8 -*-

from schemv.common import PY2
from schemv.models import Model
from schemv.types import StringType
from schemv.extensions.model_help_text_mixin import help_text_metadata, ModelHelpTextMixin


def get_helptest_model():
    class Person(Model, ModelHelpTextMixin):
        """
        This model describes a person.

        Multiline string here.
        """
        name = StringType(
            required=True,
            metadata=help_text_metadata('Name', 'A Persons name', 'Joe Stummer')
        )
    return Person


def test_help_text_metadata():
    kwargs = {
        'label': 'label',
        'description': 'description',
        'example': 'example',
    }
    assert kwargs == help_text_metadata(**kwargs)


expected_helptext = """This model describes a person.

Multiline string here.
    name (Name)
        Example: Joe Stummer
        A Persons name"""


def test_get_helptext():
    helptext = get_helptest_model().get_helptext()
    assert helptext == expected_helptext


expected_example_usage = """Person({
    'name': Joe Stummer,
})"""


def test_get_example_usage():
    example_usage = get_helptest_model().get_example_usage()
    assert example_usage == expected_example_usage


expected_parameter_descriptions = """:param %s name: A Persons name""" % ('unicode' if PY2 else 'str')


def test_get_parameter_descriptions():
    parameter_descriptions = get_helptest_model().get_parameter_descriptions()
    assert parameter_descriptions == expected_parameter_descriptions


expected_api_docstring = '''"""
This model describes a person.

Multiline string here.

Example:

    Person({
        'name': Joe Stummer,
    })


:param %s name: A Persons name
"""''' % ('unicode' if PY2 else 'str')


def test_get_api_docstring():
    api_docstring = get_helptest_model().get_api_docstring()
    assert api_docstring == expected_api_docstring
