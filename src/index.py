import asyncio
import os
import aiohttp

async def initiate_documentation_generation(headers, data):
    url = "https://production-gateway.snorkell.ai/api/app/github/generate/documentation"
    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=data, timeout=600) as response:
            if response.status == 200:
                print(await response.text())
            else:
                print(f"Request failed: {response.status}")
                print(await response.text())

async def check_documentation_generation_status(headers, data):
    url = "https://production-gateway.snorkell.ai/api/app/github/generate/documentation/status"
    async with aiohttp.ClientSession() as session:
        old_status = ""
        count = 0
        while True:
            async with session.post(url, headers=headers, json=data, timeout=600) as response:
                if response.status == 200:
                    message = await response.text()
                    if message != old_status:
                        print(message)
                        old_status = message
                        count = 0
                    
                    count += 1
                    if count > 180: # 15 minutes
                        print("Documentation generation timed out")
                        return
                    if message == "COMPLETED":
                        print("Documentation generation completed")
                        return
                else:
                    print(f"Request failed: {response.status}")
                    print(await response.text())
                    print("Fetching documentation generation status failed")
                    # send slack message to server that documentation generation failed
                    return
            await asyncio.sleep(5)

async def main():

    headers = {
        'api-key': os.getenv('SNORKELL_API_KEY'),  # Replace with your API key
        'Content-Type': 'application/json'
    }
    data = {
        "installation_id": os.getenv('SNORKELL_CLIENT_ID'),  # Replace with your client ID
        "full_repo_name": os.getenv('GITHUB_REPOSITORY'),   # Replace with your repository name
        "base_branch": os.getenv('BRANCH_NAME'),            # Replace with your branch name
        "commit_sha": os.getenv('GITHUB_SHA'),              # Replace with your commit SHA
        "commit_message": os.getenv('COMMIT_MSG')   # Replace with your commit message
    }
    
    try:
        await initiate_documentation_generation(headers, data)
        await check_documentation_generation_status(headers, data)
    except asyncio.TimeoutError:
        print("Request timed out")
    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":    
    asyncio.run(main())
        