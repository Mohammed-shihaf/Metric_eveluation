from __future__ import print_function

class IntegrationEndpoint(object):
    def __init__(self, name, base_url):
        self.name = name
        self.base_url = base_url
        self.last_status = 'idle'
        self.retry_count = 0

    def mark_success(self):
        self.last_status = 'ok'
        self.retry_count = 0

    def mark_failure(self, reason):
        self.last_status = 'error:%s' % reason
        self.retry_count += 1

    def should_retry(self, limit=3):
        return self.retry_count < limit


class IntegrationHub(object):
    def __init__(self):
        self._endpoints = {}

    def register(self, endpoint):
        self._endpoints[endpoint.name] = endpoint

    def get(self, name):
        return self._endpoints.get(name)

    def healthy_count(self):
        return sum(1 for ep in self._endpoints.values() if ep.last_status == 'ok')

    def list_names(self):
        return sorted(self._endpoints.keys())
