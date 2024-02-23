import os
import requests
import asyncio
import json
import traceback
from pprint import pprint

base_url = f"https://production-gateway.snorkell.ai"
base_url = "https://8455-2401-4900-1f26-31a3-d13d-e5fe-ee8f-f94d.ngrok-free.app/api/v1/health"

async def notify_error(message):
    message = f"GithubClient alert:\n {message}"
    print(message)
    other_vars = {
        "REPO_NAME": os.getenv("REPO_NAME"),
        "ORG_NAME": os.getenv("ORG_NAME"),
        "BRANCH_NAME": os.getenv("BRANCH_NAME"),
    }
    headers = {"Content-type": "application/json"}
    data = {
        "message": message,
        "repo_details": other_vars,
    }
    print("Sending error notification to snorkell ", data)
    url: str = f"{base_url}/api/app/github/report/errors"
    response = requests.post(url, headers=headers, json=data, timeout=600)
    if response.status_code == 200:
        message = response.json()["message"]
        print(message)
    else:
        print(response.status_code)
        


async def initiate_documentation_generation(
    headers: dict, data: dict
) -> bool:
    url: str = f"{base_url}/api/app/azDevops/generate/documentation"
    print("Initiating documentation generation")
    print("URL: ", url)
    response = requests.post(url, headers=headers, json=data, timeout=600)
    if response.status_code == 200:
        message = response.json()["message"]
        print(message)
        return bool(response.json()["valid_request"])
    else:
        raise Exception(
            "Initiating documentation generation failed with status code: ",
            response.status_code,
            " and message: ",
            response.text,
        )


async def check_documentation_generation_status(headers, data):
    url = f"{base_url}/api/app/azDevops/status/documentation"
    count = 0
    while count < 360:
        response = requests.post(url, headers=headers, json=data, timeout=600)
        if response.status_code == 200:
            message = response.json()
            print(message)
            if "COMPLETE" in message.strip().upper():
                print("Documentation generation completed")
                return

            if "FAILED" in message.strip().upper():
                print("Documentation generation failed")
                await notify_error("Documentation generation failed")
                # add alert to slack
                return
        else:
            print(f"Request failed: {response.status_code}")
            print(response.text)
            await notify_error(f"Fetching documentation generation status failed, {response.text}")
            print("Fetching documentation generation status failed")
            # send slack message to server that documentation generation failed
            return
        await asyncio.sleep(2)  # Non-blocking sleep

    print("Documentation generation timed out")


async def main():
    required_env_vars = [
        "PAT_TOKEN",
        "SNORKELL_API_KEY",
        "REPO_NAME",
        "ORG_NAME",
        "BRANCH_NAME",
        "GITHUB_SHA",
        "COMMIT_MSG"
    ]
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    print("Validating the inputs")

    if missing_vars:
        missing_keys = ', '.join(missing_vars)
        await notify_error(f"Missing required environment variables: {missing_keys}\n")
        print("################################################################################")
        print("If the issue still persists, please reach out to us at support@snorkell.ai")
        print("We will immediately help you out.")
        print("################################################################################")
        raise ValueError(
            f"Missing required environment variables: {', '.join(missing_vars)}.\
                \nPlease check the action's documentation['https://docs.snorkell.ai/'] for more information.\
                \nIf you are still facing issues, please reach out to us at - support@snorkell.ai\
                \n We will immediately help you out."
        )

    print("All inputs validated")

    print("Repo Name: ", os.getenv("GITHUB_REPOSITORY"))
    print("Branch Name: ", os.getenv("BRANCH_NAME"))
    print("Commit SHA: ", os.getenv("GITHUB_SHA"))
    print("Commit Message: ", os.getenv("COMMIT_MSG"))
    headers = {
        "api-key": os.getenv("SNORKELL_API_KEY"),  # Replace with your API key
        "Content-Type": "application/json",
    }
    data = {
        "api_token": os.getenv("PAT_TOKEN"),  # Replace with your PAT token
        "git_repo": {
            "repo_name": os.getenv("REPO_NAME"),  # Replace with your repository name
            "org_name": os.getenv("ORG_NAME"),  # Replace with your organization name
        },
        "base_branch": os.getenv("BRANCH_NAME"),  # Replace with your branch name
        "commit_sha": os.getenv("GITHUB_SHA"),  # Replace with your commit SHA
        "commit_message": os.getenv("COMMIT_MSG"),  # Replace with your commit message
    }

    pprint(data)
    try:
        is_valid_request = await initiate_documentation_generation(headers, data)
        if not is_valid_request:
            return
        await check_documentation_generation_status(headers, data)
    except requests.exceptions.Timeout as t:
        print("Request timed out")
        await notify_error("Request TIME_OUT "+traceback.format_exc())
        raise t
    except Exception as e:
        print(f"An error occurred: {e}")
        traceback.print_exc()
        if "Could not validate credentials" in traceback.format_exc():
            print("####################### Invalid credentials issue #############################")
            print("If it still doesn't fix the issue, please follow the below steps:")
            print("1. Copy the API key from the Snorkell dashboard - https://dashboard.snorkell.ai/snorkell-api-keys")
            print("2. Then go to your repository Settings -> Secrets & Variables -> Actions -> New repository secret")
            print("3. Create a new secret with the name SNORKELL_API_KEY")
            print("4. Paste the API key in the value field")
            print("5. Rerun the action")
            print("If the issue still persists, please reach out to us at founders@snorkell.ai")
            print("We will immediately help you out.")
            print("################################################################################")

        await notify_error(f"An error occurred: "+traceback.format_exc())
        raise e


if __name__ == "__main__":
    asyncio.run(main())
