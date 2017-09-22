
# (c) Copyright 2015, 2016 Hewlett Packard Enterprise Development LP
# (c) Copyright 2017 SUSE LLC
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
#


from contextlib import contextmanager
import datetime

from swiftlm.utils.values import Severity
from swiftlm.utils.utility import timestamp


def get_base_dimensions():
    # Can add region etc if needed here.
    return {
        'service': 'object-storage'
    }


class MetricData(object):
    """Metric data container."""
    def __init__(self, name, messages, dimensions=None, msgkeys={}):
        # We do this so modules can use __name__ as a quick default
        # for the response name and cloning the response does not change it.
        if name.startswith('swiftlm.'):
            self.name = name
        else:
            self.name = 'swiftlm.' + name

        if dimensions is None:
            self.dimensions = get_base_dimensions()
        else:
            self.dimensions = dimensions
        self.msgkeys = msgkeys

        self.messages = messages
        self.timestamp()

        self._message = ''
        self.__value = None

    @classmethod
    def single(cls, name, value, message='', dimensions=None, msgkeys={}):
        # Quick creation of a MetricData for things that are unrelated
        # to the main checks. e.g
        #
        # m = MetricData.single('this.other.thing',
        #                       Severity.fail,
        #                       'Something went wrong with {thing}',
        #                       {'thing': thing_var})
        # Message and dimensions are optional.
        m = cls(name, {'msg': message}, dimensions=dimensions, msgkeys=msgkeys)
        m.message = 'msg'
        m.value = value
        return m

    @property
    def value(self):
        return self.__value

    @value.setter
    def value(self, val):
        # If value is a Severity enum and it has an entry in the messages dict
        # and message isnt already set we set them both.
        # This makes the common case of OK, WARN and FAIL easy.
        if (isinstance(val, Severity) and
                val.name in self.messages and self.message == ''):
            self.message = val.name
        self.__value = val

    @property
    def message(self):
        return self._message

    @message.setter
    def message(self, val):
        self._message = self.messages[val]

        # We want to error where we actually cause it. If the message
        # requires dimension values we havent provided, __str__, __repr__ and
        # metric can fail in the future.
        try:
            str(self)
        except KeyError as e:
            raise ValueError('Cannot use message: "{}" it requires a dimension'
                             ' or msgkeys value you have'
                             ' not provided: "{}"'.format(val, e))

    def timestamp(self):
        self._timestamp = timestamp()

    @contextmanager
    def duration(self):
        """Context manager to set duration and timestamp."""
        start = timestamp()
        yield
        self._timestamp = end = timestamp()
        if isinstance(end, datetime.timedelta):
            self['duration'] = (end - start).total_seconds()
        else:
            self['duration'] = str(end - start)

    def child(self, name=None, dimensions=None, msgkeys={}):
        d = self.dimensions.copy()
        if dimensions is not None:
            d.update(dimensions)
        mk = self.msgkeys.copy()
        mk.update(msgkeys)

        n = self.name
        if name is not None:
            n += '.' + name

        return MetricData(n, self.messages, d, msgkeys=mk)

    def metric(self):
        """Construct the metric dictionary"""
        metric = {
            'metric': self.name,
            'value': self.value,
            'dimensions': self.dimensions,
            'timestamp': self._timestamp,
        }

        msg = str(self)
        if msg != '':
            # Key and value must be under 2048 characters.
            # This is the maximum length of message allowed by the
            # Monasca API (2048), minus the three dots of the ellipsis (2045),
            # minus a possible end of line character (2044), minus an
            # arbitrarily chosen 128 characters to allow for the prepended
            # text of the string "<check> failed with " and some buffer (1916).
            # The error string is likely a stack trace, the end of which is
            # typically the most interesting.
            if len(msg) > 1919:
                msg = '...' + msg[-1916:]
            metric['value_meta'] = {'msg': msg}

        return metric

    def __setitem__(self, key, val):
        self.dimensions[key] = str(val)

    def __getitem__(self, key):
        return self.dimensions[key]

    def __delitem__(self, key):
        del self.dimensions[key]

    def __contains__(self, key):
        try:
            self.dimensions[key]
            return True
        except KeyError:
            return False

    def msgkey(self, key, value):
        self.msgkeys[key] = value

    def __eq__(self, other):
        if type(self) == type(other):
            return self.metric() == other.metric()
        else:
            return False

    def __str__(self):
        fkeys = self.dimensions.copy()
        fkeys.update(self.msgkeys)
        return self.message.format(**fkeys)

    def __repr__(self):
        return '{}({})'.format(
            self.__class__.__name__,
            str(self.metric())
        )


CheckFailure = MetricData.single(
    'check.failure', Severity.fail,
    '{check} failed with: {error}',
    dimensions={'check': 'NA', 'error': 'NA', 'component': 'swiftlm-scan'}
)
