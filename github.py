***REMOVED***

***REMOVED***quests

UPDATED_AT = "UPDATED_AT"
# Repository owner and name
owner = "j19930307"
repo = "SNS-Bot"
# Personal access token
token = os.environ["ACCESS_TOKEN"]
# Authentication header
headers = {
    "Authorization": f"token {token}",
    "Accept": "application/vnd.github.v3+json"
}


def get_env_variable(variable_name):
    url = f"https://api.github.com/repos/{owner}/{repo}/actions/variables/{variable_name}"
    response = requests.get(url=url, headers=headers)
    return response


def set_env_variable(variable_name, new_value):
    url = f"https://api.github.com/repos/{owner}/{repo}/actions/variables/{variable_name}"
    data = {
        "name": variable_name,
        "value": new_value
    }
    response = requests.patch(url=url, headers=headers, json=data)
    return response
