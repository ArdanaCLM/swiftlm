#!/usr/bin/python

# (c) Copyright 2015,2016 Hewlett Packard Enterprise Development LP
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

import logging
from time import sleep, time
import datetime
import requests
import json


logger = logging.getLogger('swiftlm-jmoncli')
logger.addHandler(logging.NullHandler())


def _import_keystone_client(auth_version):
    try:
        if auth_version == 3:
            from keystoneclient.v3 import client as ksclient
        else:
            from keystoneclient.v2_0 import client as ksclient
        from keystoneclient import exceptions
        # prevent keystoneclient warning us that it has no log handlers
        logger = logging.getLogger("swiftclient")
        return ksclient, exceptions
    except ImportError as err:
        raise Exception('Import error: %s' % err)


def get_auth_keystone(auth_url, user, key, os_options, **kwargs):
    """
    Authenticate against a keystone server.

    We are using the keystoneclient library for authentication.
    """

    insecure = kwargs.get('insecure', False)
    timeout = kwargs.get('timeout', None)
    auth_version = 2
    if auth_url.endswith('/v3'):
        auth_version = 3
    debug = logger.isEnabledFor(logging.DEBUG) and True or False

    ksclient, exceptions = _import_keystone_client(auth_version)

    try:
        _ksclient = ksclient.Client(
            username=user,
            password=key,
            tenant_name=os_options.get('tenant_name'),
            tenant_id=os_options.get('tenant_id'),
            user_id=os_options.get('user_id'),
            user_domain_name=os_options.get('user_domain_name'),
            user_domain_id=os_options.get('user_domain_id'),
            project_name=os_options.get('project_name'),
            project_id=os_options.get('project_id'),
            project_domain_name=os_options.get('project_domain_name'),
            project_domain_id=os_options.get('project_domain_id'),
            debug=debug,
            cacert=kwargs.get('cacert'),
            auth_url=auth_url, insecure=insecure, timeout=timeout)
    except exceptions.Unauthorized:
        msg = 'Unauthorized. Check username, password and project name/id.'
        raise JahmonClientException(msg)
    except exceptions.AuthorizationFailure as err:
        raise JahmonClientException('Authorization Failure. %s' % err)
    service_type = os_options.get('service_type') or 'monitoring'
    endpoint_type = os_options.get('endpoint_type') or 'internalURL'
    try:
        endpoint = _ksclient.service_catalog.url_for(
            attr='region',
            filter_value=os_options.get('region_name', None),
            service_type=service_type,
            endpoint_type=endpoint_type)
    except exceptions.EndpointNotFound:
        raise JahmonClientException('Endpoint not found')
    return endpoint, _ksclient.auth_token


class JahmonClientException(Exception):
    """
    Raised for Monasca API error responses

    If the error relates to a REST API operation, http_status
    contains the HTTP error code. Otherwise, the value of
    http_status is 0.
    """
    def __init__(self, msg, http_status=0):
        Exception.__init__(self, msg)
        self.msg = msg
        self.http_status = http_status


def json_response(request):
    try:
        return json.loads(request.text)
    except Exception:
        raise JahmonClientException('Invalid JSON in response body')


def raise_error(request, exc):
    """
    Attempt to pull error from the HTTP response; otherwise throw original
    """
    if isinstance(exc, JahmonClientException):
        raise exc
    status_code = None
    text = ''
    try:
        status_code = request.status_code
        text = request.text
    except Exception:
        pass
    if status_code:
        raise JahmonClientException('HTTP Code: %s ; Body:%s' % (status_code,
                                                                 text))
    else:
        raise exc


class JahmonConnection(object):
    """
    Monasca API interface

    Provides an interface to the Monasca API. You create a connection
    object and then use this object to perform operations.

    Example:

        conn = JahmonConnection(auth_url='https://key-vip:35357/v2.0',
            username='myname', password='secret',
            project_id='123456789123456', region='region1')
        try:
            metrics = conn.get_metrics(process.pid_count,
                                       dimensions={'process_name':
                                                   'monasca-notification'})
            for metric in metrics:
                items = conn.get_measurements(metric, -10, 0)
                for item in items:
                    print('%s %s: %s' % (item.get('timestamp',
                                        item.get('dimensions'),
                                        item.get('value'))
        except JahmonClientException as err:
            print 'Got %s code; reason: %s' % (err.http_status, err)

    Exception Handling:

    If you get errors from the API, the JahmonConnection object raises
    a JahmonClientException. However, other errors can result in other
    exceptions. We suggest you catch all exceptions and check for
    the http_status attribute. If it exists, the error came from the
    Monasca service itself. Otherwise, the error came from elsewhere.

    The JahmonConnection object automatically retries operations to handle
    temporary downtime or glitches in the Identity or Monasca service. There
    is little point in re-trying an operation yourself within seconds
    of getting an exception -- wait at least 60 seconds before retrying.
    There is no need to create a new JahmonConnection object before
    retrying -- you can use the same JahmonConnection object for the
    lifetime of the program. You only need a new object if the credentials
    change.
    """

    def __init__(self, auth_url=None, username=None, password=None,
                 user_id=None, project_id=None, region_name=None,
                 user_domain_id=None, user_domain_name=None, project_name=None,
                 project_domain_name=None, project_domain_id=None,
                 jahmon_url=None, jahmon_token=None,
                 timeout=2.0):
        """
        Create a connection object

        To perform an operation that requires an authentication token,
        you must create the connection using the auth_url. If you know
        the Monasca endpoint and and have an authentication token, specify
        the jahmon_url and jahmon_token directly.

        With auth_url, the credentials (username, password, project_id and
        region_name) are required. The credentials are not used until
        you perform an operation. If you need to check them, perform
        an operation (such as get_versions()). Tokens are
        automatically renewed.
        """
        if not (auth_url or jahmon_url):
            raise JahmonClientException('Must specify auth_url or jahmon_url')
        if auth_url and jahmon_url:
            raise JahmonClientException(
                'Cannot specify both auth_url and jahmon_url')
        if auth_url:
            if not (project_id or project_name):
                raise JahmonClientException('Must specify project_id/name'
                                            ' and (optionally) region_name')
            if not ((username or user_id) and password):
                raise JahmonClientException('Must specify username and '
                                            ' password')
        if jahmon_token and not jahmon_url:
            raise JahmonClientException('Must specify jahmon_url with'
                                        ' jahmon_token')
        self.auth_url = auth_url
        self.username = username
        self.password = password
        self.os_options = {}
        self.os_options['project_id'] = project_id
        self.os_options['region_name'] = region_name
        self.os_options['user_id'] = user_id
        self.os_options['project_name'] = project_name
        self.os_options['project_domain_name'] = project_domain_name
        self.os_options['project_domain_id'] = project_domain_id
        self.os_options['user_domain_name'] = user_domain_name
        self.os_options['user_domain_id'] = user_domain_id
        self.retries = 2
        self.url, self.token = (jahmon_url, jahmon_token)
        self.status_code = 0
        self.timeout = timeout
        self.auth_attempts = 0
        self.attempts = 0

    def _get_auth(self):
        """
        Get endpoint and token values from the identity service
        """
        try:
            (url, token) = get_auth_keystone(self.auth_url,
                                             self.username,
                                             self.password,
                                             self.os_options)
        except JahmonClientException as err:
            raise JahmonClientException('Cannot get token: %s' % err,
                                        http_status=401)
        return (url, token)

    def _get_url_token(self):
        """
        Get endpoint and token to use with an operation

        Caches endpoint and token to reduce cost of authenticating.
        """
        if self.url:
            return (self.url, self.token)
        self.auth_attempts = 0
        while True:
            self.auth_attempts += 1
            try:
                self.url, self.token = self._get_auth()
                return (self.url, self.token)
            except JahmonClientException as err:
                if self.auth_attempts > self.retries:
                    self.url, self.token = (None, None)
                    raise
                sleep(1.0)
        return (self.url, self.token)

    @classmethod
    def _timestamp(self):
        """
        Return time rounded to one minute ago in milliseconds
        """
        now = time()
        return int(now/60)*60*1000

    @classmethod
    def utctime(cls, dt=None):
        """
        Get  ISO 8601 combined date and time format in UTC

        :param dt: Optional time or offset. If not specified, returns time
                   now. Otherwise, any of the following may be used:
                   - Integer offset. Examples, -1, 0, 2. This is added to the
                     minutes of the current time.
                   - String offset. Examples '-1', '0', '2'. This is added to
                     the minutes of the current time.
                   - A string formatted as %Y/%m/%dT%H:%M:%S.%fZ
                   - A datetime.datetime object
        """
        if isinstance(dt, int) or isinstance(dt, float):
            dt = str(dt)
        if not dt:
            rt = datetime.datetime.utcnow()
        elif isinstance(dt, str) and ':' not in dt:
            rt = datetime.datetime.utcnow()
            rt = datetime.datetime(rt.year, rt.month, rt.day, rt.hour,
                                   rt.minute, rt.second, 0)
            rt += datetime.timedelta(seconds=int(float(dt)*60))
        elif isinstance(dt, str):
            rt = datetime.datetime.strptime(dt, '%Y-%m-%dT%H:%M:%S.%fZ')
        else:
            rt = datetime.datetime(dt.year, dt.month, dt.day, dt.hour,
                                   dt.minute, dt.second, 0)
        return rt.strftime('%Y-%m-%dT%H:%M:%S.%fZ')

    def get_versions(self):
        """
        GET API versions

        :returns: object loaded with the JSON response from the API
        """
        self.attempts = 0
        while True:
            self.attempts += 1
            try:
                request = None
                url, token = self._get_url_token()
                bits = url.split('/')
                url = bits[0] + '//' + bits[2]
                headers = {'x-auth-token': token, 'content-length': str(0),
                           'accept': 'application/json'}
                request = requests.get(url, headers=headers,
                                       timeout=self.timeout)
                self.status_code = request.status_code
                request.raise_for_status()
                return json_response(request)
            except Exception as err:
                if self.attempts > self.retries:
                    raise_error(request, err)
                self.url, self.token = (None, None)
                sleep(0.5)

    def get_metrics(self, metric_name=None, dimensions={}, for_project=None,
                    offset=None):
        """
        Gets metrics

        The metrics are returned from a generator. Pagination is automatically
        handled so the metric list is unlimited. Nevertheless, the offset
        argument may be used.

        :param metric_name: A metric name. Optional
        :param dimensions: Dimensions (dictionary) Optional
        :param for_project: See Monasca API. Optional
        :param offset: Optional offset.
        :returns: An iterator. Each item is a dictionary with the
                  following keys:
                  - name
                  - dimensions
                  - id
        """
        response = self.get_metrics_api(metric_name, dimensions=dimensions,
                                        for_project=for_project, offset=offset)
        metrics = self._parse_metrics_response(response)
        for metric in metrics:
            yield metric
        while metrics:
            if not metrics:
                break
            end_metric = metrics[-1]
            offset = end_metric.get('id')
            response = self.get_metrics_api(metric_name,
                                            dimensions=dimensions,
                                            for_project=for_project,
                                            offset=offset)
            metrics = self._parse_metrics_response(response)
            for metric in metrics:
                yield metric

    def _parse_metrics_response(self, response):
        results = []
        elements = response.get('elements')
        for element in elements:
            results.append(element)
        return results

    def get_metrics_api(self, metric_name=None, dimensions={},
                        for_project=None, offset=None, limit=None):
        """
        Thin wrapper around the GET /metrics

        :param metric_name: Metric name. Optional
        :param dimensions: Dimensions. Optional
        :param for_project: See Monasca API
        :param offset: Offset to start from. Optional
        :param limit: Limits number of metrics returned.
        :returns: object loaded with the JSON response from the API
        """
        self.attempts = 0
        while True:
            self.attempts += 1
            try:
                request = None
                url, token = self._get_url_token()
                url += '/metrics'
                headers = {'x-auth-token': token, 'content-length': str(0),
                           'accept': 'application/json'}
                params = {}
                if metric_name:
                    params['name'] = metric_name
                if for_project:
                    params['tenant_id'] = for_project
                if dimensions:
                    key_vals = []
                    for key in dimensions.keys():
                        key_vals.append(key + ':' + dimensions[key])
                    key_values = ','.join(key_vals)
                    params['dimensions'] = key_values
                if offset:
                    params['offset'] = offset
                if limit:
                    params['limit'] = limit
                request = requests.get(url, params=params, headers=headers,
                                       timeout=self.timeout)
                self.status_code = request.status_code
                request.raise_for_status()
                return json_response(request)
            except Exception as err:
                if self.attempts > self.retries:
                    raise_error(request, err)
                self.url, self.token = (None, None)
                sleep(0.5)

    def get_measurements(self, metric, start_time, end_time,
                         for_project=None, offset=None,
                         merge_metrics=False, count=None):
        """
        Get measurements for a given metric

        This function returns a list of measurement objects given an metric
        object. It handles pagination.The results are returned by a
        generator so an unlimited number of measurements can be retrieved.

        The start and end times can be expressed in different ways. See
        the utctime() description.

        Unlike the GET /metrics/measurements API, if metrics are merged,
        each returned item contains the dimensions of the request -- not {}.

        :param metric: a metric object. This is a dict, with the following
                       keys:
                           - name (metric name)
                           - dimensions (dictionary)
        :param start_time: Oldest measurement to get
        :param end_time: Most recent measurement to ge
        :param for_project: See Monasca API. Optional
        :param offset: Offset. Optional.
        :param merge_metrics: If the specified name/dimensions match multiple
                              dimensions, merge the results.
        :returns: An iterator. Each item is a dictionary containing the
                               following keys:
                               - name (string)
                               - dimensions (dictionary)
                               - value (string)
                               - timestamp (string)
                               - value_meta (dictionary)
                               - id (string)
        """
        start_time = self.utctime(start_time)
        end_time = self.utctime(end_time)
        dimensions = metric.get('dimensions')
        response = self.get_measurements_api(metric.get('name'),
                                             start_time, end_time,
                                             dimensions=dimensions,
                                             for_project=for_project,
                                             merge_metrics=merge_metrics,
                                             offset=offset)
        measurements = self._parse_measurements_response(response,
                                                         dimensions,
                                                         count)
        for measurement in measurements:
            yield measurement
        while measurements:
            if not measurements:
                break
            end_measurement = measurements[-1]
            offset = end_measurement.get('timestamp')
            response = self.get_measurements_api(metric.get('name'),
                                                 start_time, end_time,
                                                 dimensions=dimensions,
                                                 for_project=for_project,
                                                 merge_metrics=merge_metrics,
                                                 offset=offset)
            measurements = self._parse_measurements_response(response,
                                                             dimensions,
                                                             count)
            for measurement in measurements:
                yield measurement

    def _parse_measurements_response(self, response, metric_dimensions,
                                     count):
        results = []
        elements = response.get('elements')
        for element in elements:
            if element.get('dimensions') == {}:
                dimensions = metric_dimensions
            else:
                dimensions = element.get('dimensions')
            measurements = element.get('measurements')
            id = element.get('id')
            name = element.get('name')
            columns = element.get('columns')
            col_keys = {}
            for index, key in enumerate(columns):
                col_keys[key] = index
            if count:
                measurements_of_interest = measurements[-count:]
            else:
                measurements_of_interest = measurements
            for measurement in measurements_of_interest:
                result = {'dimensions': dimensions,
                          'value': measurement[col_keys.get('value')],
                          'timestamp': measurement[col_keys.get('timestamp')],
                          'value_meta': measurement[col_keys.get(
                              'value_meta')],
                          'id': id,
                          'name': name}
                results.append(result)
        return results

    def get_measurements_api(self, metric_name, start_time, end_time,
                             dimensions={}, for_project=None,
                             merge_metrics=False, offset=None):
        """
        Thin wrapper for GET /metrics/measurements

        The start and end times can be expressed in different ways. See
        the utctime() description.

        :param metric_name: Metric name. Required.
        :param start_time: Start time
        :param end_time: End time
        :param dimensions: Dimensions. Optional
        :param for_project: See Monasca API
        :param merge_metrics: See Monasca PI
        :param offset: Offset.
        :returns: object loaded with the JSON response from the API
        """
        self.attempts = 0
        while True:
            self.attempts += 1
            try:
                request = None
                url, token = self._get_url_token()
                url += '/metrics/measurements'
                headers = {'x-auth-token': token, 'content-length': str(0),
                           'accept': 'application/json'}
                params = {}
                if metric_name:
                    params['name'] = metric_name
                if for_project:
                    params['tenant_id'] = for_project
                if dimensions:
                    key_vals = []
                    for key in dimensions.keys():
                        key_vals.append(key + ':' + dimensions[key])
                    key_values = ','.join(key_vals)
                    params['dimensions'] = key_values
                params['start_time'] = self.utctime(start_time)
                params['end_time'] = self.utctime(end_time)
                params['merge_metrics'] = merge_metrics
                if offset:
                    params['offset'] = offset
                request = requests.get(url, params=params, headers=headers,
                                       timeout=self.timeout)
                self.status_code = request.status_code
                request.raise_for_status()
                return json_response(request)
            except Exception as err:
                if self.attempts > self.retries:
                    raise_error(request, err)
                self.url, self.token = (None, None)
                sleep(0.5)

    def post_metric(self, metric_name, value, dimensions={},
                    value_meta=None, timestamp=None,
                    for_project=None):
        """

        :param metric_name: The metric name. Required
        :param value: The value (int, float or string). Required
        :param dimensions: Dimensions (dictionary). Optional.
        :param value_meta: Value meta (dictionary). Optional
        :param timestamp: Timestamp. If omitted, posted as current time.,
        :param for_project: See Monasca API
        :returns: Nothing. Raises exception if there is a problem
        """
        timestamp = timestamp or self._timestamp()
        self.attempts = 0
        while True:
            self.attempts += 1
            try:
                request = None
                url, token = self._get_url_token()
                url += '/metrics'
                headers = {}
                if token:
                    headers['x-auth-token'] = token
                headers['content-type'] = 'application/json'
                params = {}
                if for_project:
                    params['tenant_id'] = for_project
                payload = {'name': metric_name,
                           'dimensions': dimensions,
                           'timestamp': int(timestamp-1),
                           'value': float(value)}
                if value_meta:
                    payload['value_meta'] = value_meta
                request = requests.post(url, params=params, headers=headers,
                                        timeout=self.timeout,
                                        data=json.dumps(payload))
                self.status_code = request.status_code
                request.raise_for_status()
                return
            except Exception as err:
                if self.attempts > self.retries:
                    raise_error(request, err)
                self.url, self.token = (None, None)
                sleep(0.5)
