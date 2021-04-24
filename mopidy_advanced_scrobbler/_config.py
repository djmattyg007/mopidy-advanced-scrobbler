import mopidy.config.types as types
import mopidy.config.validators as validators


class Float(types.ConfigValue):
    """Integer value."""

    def __init__(self, minimum=None, maximum=None, choices=None, optional=False):
        self._required = not optional
        self._minimum = minimum
        self._maximum = maximum
        self._choices = choices

    def deserialize(self, value):
        value = types.decode(value)
        validators.validate_required(value, self._required)
        if not value:
            return None
        value = float(value)
        validators.validate_choice(value, self._choices)
        validators.validate_minimum(value, self._minimum)
        validators.validate_maximum(value, self._maximum)
        return value
