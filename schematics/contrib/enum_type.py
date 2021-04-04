"""Type supporting native Python3 enum. It depends either on Py3.4+ or e.g. enum34.
"""

from enum import Enum

from ..exceptions import ConversionError
from ..translator import _
from ..types import BaseType


class EnumType(BaseType):
    """A field type allowing to use native enums as values.
    Restricts values to enum members and (optionally) enum values.
    `use_values` - if set to True allows do assign enumerated values to the field.

    >>> import enum
    >>> class E(enum.Enum):
    ...    A = 1
    ...    B = 2
    >>> from schematics import Model
    >>> class AModel(Model):
    ...    foo = EnumType(E)
    >>> a = AModel()
    >>> a.foo = E.A
    >>> a.foo.value == 1
    """

    MESSAGES = {
        "convert": _("Couldn't interpret '{0}' as member of {1}."),
    }

    def __init__(self, enum, use_values=False, **kwargs):
        """
        :param enum: Enum class to which restrict values assigned to the field.
        :param use_values: If true, also values of the enum (right-hand side) can be assigned here.
        Other args are passed to superclass.
        """
        self._enum_class = enum
        self._use_values = use_values
        super().__init__(**kwargs)

    def to_native(self, value, context=None):
        if isinstance(value, self._enum_class):
            return value
        by_name = self._find_by_name(value)
        if by_name:
            return by_name
        by_value = self._find_by_value(value)
        if by_value:
            return by_value
        raise ConversionError(self.messages["convert"].format(value, self._enum_class))

    def _find_by_name(self, value):
        if isinstance(value, str):
            try:
                return self._enum_class[value]
            except KeyError:
                pass
        return None

    def _find_by_value(self, value):
        if not self._use_values:
            return None
        for member in self._enum_class:
            if member.value == value:
                return member
        return None

    def to_primitive(self, value, context=None):
        if isinstance(value, Enum):
            if self._use_values:
                return value.value
            return value.name
        return str(value)
