import requests
import httpx
import asyncio
import base64
import random
import string
import os
import sys
import json

def generate_random_string(length):
    characters = string.ascii_letters + string.digits 
    random_string = ''.join(random.choice(characters) for _ in range(length))
    return random_string

async def download_streamed_data(url, input_data, output_data):
    async with httpx.AsyncClient() as client:
        response_stream = ''
        response = await client.post(url, json=input_data)

        if response.status_code == 200:
            async for chunk in response.aiter_bytes():
                # Process each chunk of data here
                # In this example, we'll print it
                response_stream = chunk.decode("utf-8")
                print(chunk.decode("utf-8"))  # Assuming UTF-8 encoding
        else:
            print(f"Request failed with status code: {response.status_code}")

        output_data.append(response_stream)

if __name__ == "__main__":    
    OWNER = os.getenv("OWNER")
    REPO = os.getenv("REPO")
    github_file_path = os.getenv("GITHUB_FILE_PATH")
    main_branch = os.getenv("MAIN_BRANCH")
    BEARER_TOKEN = os.getenv("BEARER_TOKEN")
    file_type = "python"
    
    print(f'OWNER sys env {OWNER}')
    print(f'OWNER sys arg {sys.argv[1]}')

    HEADERS = {
        'Authorization': f'Bearer {BEARER_TOKEN}',
    }
    # fetch provided file from github
    ##############################################################################################################
    github_file_url = f'https://api.github.com/repos/{OWNER}/{REPO}/contents/{github_file_path}'
    # print(github_file_url)
    github_file_response = requests.get(github_file_url, headers=HEADERS).json()
    print(f'response {json.dumps(github_file_response)}')
    # file_content = base64.b64decode(response['content']).decode('utf-8')
    github_file_content = base64.b64decode(github_file_response['content'])
    github_file_sha = github_file_response['sha']
    # print(f'file_sha {github_file_sha}, file_content {github_file_content}')
    ##############################################################################################################

    # call snorkell document generator 
    ##############################################################################################################
    # api_url = 'https://production-gateway.snorkell.ai/'
    # api_response = requests.post(api_url, json={'file_content': github_file_content})
    # snorkell_api_response = "ZnJvbSBmYXN0YXBpIGltcG9ydCBBUElSb3V0ZXIsIERlcGVuZHMsIFJlcXVlc3QK\naGVsbG8K"

    snorkell_api_response = ""
    snorkell_api_url = "https://production-gateway.snorkell.ai/api/gen-documentation-stream"

    # snorkell_api_url = "https://localhost:8888/api/gen-documentation-stream"

    snorkell_api_data = {
        'content': f'{github_file_content}',
        'fileType': f'{file_type}',
    }
    print(f'snorkell_api_data {snorkell_api_data}')

    snorkell_api_response_data =[]
    asyncio.run(download_streamed_data(snorkell_api_url, snorkell_api_data, snorkell_api_response_data))
    snorkell_api_response = snorkell_api_response_data[0]
    # print(f'snorkell_api_response {snorkell_api_response}')
    snorkell_api_response_encode_byte = base64.b64encode(snorkell_api_response.encode('utf-8'))
    # print(f'snorkell_api_response_encode_byte {snorkell_api_response_encode_byte}')
    snorkell_api_response_encode_string = snorkell_api_response_encode_byte.decode('utf-8')
    print(f'snorkell_api_response_encode_string {snorkell_api_response_encode_string}')
    ##############################################################################################################

    # get correct sha of from branch
    # Create a new branch based on the main branch
    # Commit generated new doc
    # create a new PR
    ##############################################################################################################
    main_branch_url = f'https://api.github.com/repos/{OWNER}/{REPO}/git/matching-refs/heads/{main_branch}'
    main_branch_response = requests.get(main_branch_url, headers=HEADERS).json()
    # print(f'main_branch_response {main_branch_response}')
    main_branch_sha = main_branch_response[0]['object']['sha']
    # print(f'main_branch_sha {main_branch_sha}')
    ##############################################################################################################

    ##############################################################################################################
    randon_varchar = generate_random_string(15)
    new_branch_name = f'auto_documentation_{randon_varchar}'
    # print(f'new_branch_name {new_branch_name}')
    new_branch_url = f'https://api.github.com/repos/{OWNER}/{REPO}/git/refs'
    new_branch_data = {
        'ref': f'refs/heads/{new_branch_name}',
        'sha': main_branch_sha
    }
    new_branch_response = requests.post(new_branch_url, json=new_branch_data, headers=HEADERS).json()
    # print(f'new_branch_response {new_branch_response}')
    ##############################################################################################################

    ##############################################################################################################
    git_commit_url = github_file_url
    git_commit_data = {
        'message': 'Updating file content',
        "content": f'{snorkell_api_response_encode_string}',
        "sha": f'{github_file_sha}',
        "branch": f'{new_branch_name}'
    }
    # print(f'git_commit_data {json.dumps(git_commit_data)}')
    commit_response = requests.put(git_commit_url, json=git_commit_data, headers=HEADERS).json()
    # print(f'commit_response {commit_response}')
    ##############################################################################################################

    ##############################################################################################################
    pr_url = f'https://api.github.com/repos/{OWNER}/{REPO}/pulls'
    pr_data = {
        'title': 'Automated PR',
        'body': 'Automated PR created by script',
        'head': f'{new_branch_name}',
        'base': f'{main_branch}',
    }
    # print(f'pr_data {json.dumps(pr_data)}')
    pr_response = requests.post(pr_url, json=pr_data, headers=HEADERS).json()
    # print(f'pr_response {pr_response}')
    ##############################################################################################################

    # print('Pull Request created')