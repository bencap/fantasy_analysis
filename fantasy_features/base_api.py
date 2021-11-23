import requests


class BaseApi():
    def _call(self, url, params=None):
        """Calls the api url requested and returns the json result"""
        result_json_string = requests.get(url, params)
        try:
            result_json_string.raise_for_status()
        except requests.exceptions.HTTPError as e:
            return e

        result = result_json_string.json()
        return result
