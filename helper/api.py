from config.rapid_api import rapid_api_url, rapid_api_headers
import requests


class APICalls:
    def __init__(self, headers=None, base_url=rapid_api_url):
        if headers is None:
            headers = rapid_api_headers
        self.headers = headers
        self.base_url = base_url

    def get_response(self, url: str, querystring: dict):
        response = requests.get(url, headers=self.headers, params=querystring)
        return response.json()

    def get_predictions(self, fixture):
        data = self.get_response(url=f"{rapid_api_url}/predictions", querystring={"fixture": fixture["fixture"]["id"]})
        if "response" in data:
            return data["response"][0]
        return None

    # Get team ID based on team name
    def get_team_id(self, team_name):
        data = self.get_response(url=f"{rapid_api_url}/teams", querystring={"name": team_name})
        if "response" in data and len(data["response"]) > 0:
            return data["response"][0]["team"]["id"]
        return None
