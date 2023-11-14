import os
import requests
import asyncio


async def initiate_documentation_generation(
    headers: dict, data: dict
) -> bool:
    url: str = "https://production-gateway.snorkell.ai/api/app/github/generate/documentation"
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
    url = "https://production-gateway.snorkell.ai/api/app/github/generate/documentation/status"
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
                # add alert to slack
                return
        else:
            print(f"Request failed: {response.status_code}")
            print(response.text)
            print("Fetching documentation generation status failed")
            # send slack message to server that documentation generation failed
            return
        await asyncio.sleep(2)  # Non-blocking sleep

    print("Documentation generation timed out")


async def main():
    required_env_vars = [
        "SNORKELL_API_KEY",
        "SNORKELL_CLIENT_ID",
        "GITHUB_REPOSITORY",
        "BRANCH_NAME",
        "GITHUB_SHA",
        "COMMIT_MSG",
    ]
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    print("Validating the inputs")

    if missing_vars:
        raise ValueError(
            f"Missing required environment variables: {', '.join(missing_vars)}"
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
        "installation_id": os.getenv(
            "SNORKELL_CLIENT_ID"
        ),  # Replace with your client ID
        "full_repo_name": os.getenv(
            "GITHUB_REPOSITORY"
        ),  # Replace with your repository name
        "base_branch": os.getenv("BRANCH_NAME"),  # Replace with your branch name
        "commit_sha": os.getenv("GITHUB_SHA"),  # Replace with your commit SHA
        "commit_message": os.getenv("COMMIT_MSG"),  # Replace with your commit message
    }

    try:
        is_valid_request = await initiate_documentation_generation(headers, data)
        if not is_valid_request:
            return
        await check_documentation_generation_status(headers, data)
    except requests.exceptions.Timeout:
        print("Request timed out")
    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    asyncio.run(main())
