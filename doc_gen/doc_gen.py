import requests
import httpx
import asyncio
import base64
import random
import string
import os
import json

file_types = {
        ".txt": "Text",
        ".py": "Python",
        ".jpg": "JPEG Image",
        ".png": "PNG Image",
        ".pdf": "PDF Document",
        ".java": "Java"
    }

def generate_random_string(length):
    characters = string.ascii_letters + string.digits 
    random_string = ''.join(random.choice(characters) for _ in range(length))
    return random_string

async def download_streamed_data(url, input_data, SNORKELL_HEADERS, output_data):
    async with httpx.AsyncClient() as client:
        response_stream = ''
        response = await client.post(url, json=input_data, headers=SNORKELL_HEADERS)

        if response.status_code == 200:
            async for chunk in response.aiter_bytes():
                # Process each chunk of data here
                # In this example, we'll print it
                response_stream = chunk.decode("utf-8")
                print(chunk.decode("utf-8"))  # Assuming UTF-8 encoding
        else:
            print(f"Request failed with status code: {response.status_code}")

        output_data.append(response_stream)

async def improvise_single_file_documentation_commit(OWNER, REPO, GIHUB_HEADERS, SNORKELL_HEADERS, new_branch_name, file_path, file_type):
    # fetch provided file from github
    ##############################################################################################################
    github_file_url = f'https://api.github.com/repos/{OWNER}/{REPO}/contents/{file_path}'
    # print(github_file_url)
    github_file_response = requests.get(github_file_url, headers=GIHUB_HEADERS).json()
    # print(f'github_file_response {json.dumps(github_file_response)}')
    # file_content = base64.b64decode(response['content']).decode('utf-8')
    github_file_content = base64.b64decode(github_file_response['content'])
    github_file_sha = github_file_response['sha']
    # print(f'file_sha {github_file_sha}, file_content {github_file_content}')
    ##############################################################################################################

    # call snorkell document generator 
    ##############################################################################################################
    snorkell_api_response = ""
    snorkell_api_url = "https://production-gateway.snorkell.ai/api/v1/generate/documentation"

    snorkell_api_data = {
        'content': f'{github_file_content}',
        'fileType': f'{file_type}',
    }
    print(f'snorkell_api_data {snorkell_api_data}')

    snorkell_api_response_data =[]
    streaming_tasks = []
    streaming_task = asyncio.create_task(download_streamed_data(snorkell_api_url, snorkell_api_data, SNORKELL_HEADERS, snorkell_api_response_data))
    streaming_tasks.append(streaming_task)
    # await asyncio.run(download_streamed_data(snorkell_api_url, snorkell_api_data, snorkell_api_response_data))
    await asyncio.gather(*streaming_tasks)

    snorkell_api_response = snorkell_api_response_data[0]
    # print(f'snorkell_api_response {snorkell_api_response}')
    snorkell_api_response_encode_byte = base64.b64encode(snorkell_api_response.encode('utf-8'))
    # print(f'snorkell_api_response_encode_byte {snorkell_api_response_encode_byte}')
    snorkell_api_response_encode_string = snorkell_api_response_encode_byte.decode('utf-8')
    # print(f'snorkell_api_response_encode_string {snorkell_api_response_encode_string}')
    ##############################################################################################################

    if new_branch_name is None:
        # get correct sha of from branch
        ##############################################################################################################
        main_branch_url = f'https://api.github.com/repos/{OWNER}/{REPO}/git/matching-refs/heads/{MAIN_BRANCH}'
        main_branch_response = requests.get(main_branch_url, headers=GIHUB_HEADERS).json()
        # print(f'main_branch_response {main_branch_response}')
        main_branch_sha = main_branch_response[0]['object']['sha']
        # print(f'main_branch_sha {main_branch_sha}')
        ##############################################################################################################

        # Create a new branch based on the main branch
        ##############################################################################################################
        randon_varchar = generate_random_string(15)
        new_branch_name = f'auto_documentation_{randon_varchar}'
        # print(f'new_branch_name {new_branch_name}')
        new_branch_url = f'https://api.github.com/repos/{OWNER}/{REPO}/git/refs'
        new_branch_data = {
            'ref': f'refs/heads/{new_branch_name}',
            'sha': main_branch_sha
        }
        new_branch_response = requests.post(new_branch_url, json=new_branch_data, headers=GIHUB_HEADERS).json()
        # print(f'new_branch_response {new_branch_response}')
        ##############################################################################################################

    # Commit generated new doc
    ##############################################################################################################
    git_commit_url = github_file_url
    git_commit_data = {
        'message': f'Documenting file {file_path} of content type {file_type}',
        "content": f'{snorkell_api_response_encode_string}',
        "sha": f'{github_file_sha}',
        "branch": f'{new_branch_name}'
    }
    # print(f'git_commit_data {json.dumps(git_commit_data)}')
    commit_response = requests.put(git_commit_url, json=git_commit_data, headers=GIHUB_HEADERS).json()
    # print(f'commit_response {commit_response}')
    ##############################################################################################################


async def improvise_pr_with_documentation():
    GIT_OWNER_REPO = os.getenv("GIT_REPO")
    MAIN_BRANCH = os.getenv("MAIN_BRANCH")
    GIHUB_BEARER_TOKEN = os.getenv("GIHUB_BEARER_TOKEN")
    SNORKELL_BEARER_TOKEN = os.getenv("SNORKELL_BEARER_TOKEN")

    GIT_OWNER_REPO_PARTS = GIT_OWNER_REPO.split('/')    
    OWNER = GIT_OWNER_REPO_PARTS[0]
    REPO = GIT_OWNER_REPO_PARTS[1]
    
    GIHUB_HEADERS = {
        'Authorization': f'Bearer {GIHUB_BEARER_TOKEN}',
    }

    SNORKELL_HEADERS = {
        'Authorization': f'Bearer {GIHUB_BEARER_TOKEN}',
    }

    github_files = []

    # fetch latest commit to main branch
    ##############################################################################################################
    github_latest_commit_url = f'https://api.github.com/repos/{OWNER}/{REPO}/commits/{MAIN_BRANCH}'
    print(f'github_latest_commit_url {github_latest_commit_url}')
    github_latest_commit_response = requests.get(github_latest_commit_url, headers=GIHUB_HEADERS).json()
    print(f'github_latest_commit_response {json.dumps(github_latest_commit_response)}')
    github_latest_commit_files = github_latest_commit_response['files']
    # print(f'github_latest_commit_files {json.dumps(github_latest_commit_files)}')

    for github_latest_commit_file in github_latest_commit_files:

        github_latest_commit_file_name  = github_latest_commit_file['filename']
        # print(f"github_latest_commit_file_name {github_latest_commit_file_name}")
        
        github_latest_commit_file_extension = github_latest_commit_file_name.split('.')[-1]

        github_latest_commit_file_type = file_types.get("." + github_latest_commit_file_extension, "Unknown")
        # print(f"github_latest_commit_file_type {github_latest_commit_file_type}")

        github_files.append((github_latest_commit_file_name,github_latest_commit_file_type))
        

    # # get correct sha of from branch
    # ##############################################################################################################
    # main_branch_url = f'https://api.github.com/repos/{OWNER}/{REPO}/git/matching-refs/heads/{MAIN_BRANCH}'
    # main_branch_response = requests.get(main_branch_url, headers=GIHUB_HEADERS).json()
    # # print(f'main_branch_response {main_branch_response}')
    # main_branch_sha = main_branch_response[0]['object']['sha']
    # # print(f'main_branch_sha {main_branch_sha}')
    # ##############################################################################################################

    # # Create a new branch based on the main branch
    # ##############################################################################################################
    # randon_varchar = generate_random_string(15)
    # new_branch_name = f'auto_documentation_{randon_varchar}'
    # # print(f'new_branch_name {new_branch_name}')
    # new_branch_url = f'https://api.github.com/repos/{OWNER}/{REPO}/git/refs'
    # new_branch_data = {
    #     'ref': f'refs/heads/{new_branch_name}',
    #     'sha': main_branch_sha
    # }
    # new_branch_response = requests.post(new_branch_url, json=new_branch_data, headers=GIHUB_HEADERS).json()
    # # print(f'new_branch_response {new_branch_response}')
    # ##############################################################################################################

    ##############################################################################################################
    improvise_files_tasks = []
    new_branch_name = None
    for file in github_files:
        # print(f"file_path{file[0]} file_type {file[1]}")
        file_path = file[0]
        file_type = file[1]
        improvise_files_task = asyncio.create_task(improvise_single_file_documentation_commit(OWNER,REPO,GIHUB_HEADERS,SNORKELL_HEADERS,new_branch_name,file_path,file_type))
        improvise_files_tasks.append(improvise_files_task)
    
    await asyncio.gather(*improvise_files_tasks)
    ##############################################################################################################
    
    # create a new PR
    ##############################################################################################################
    pr_url = f'https://api.github.com/repos/{OWNER}/{REPO}/pulls'
    pr_data = {
        'title': 'AI generated Documentation',
        'body': 'Automated PR of AI generated Documentation',
        'head': f'{new_branch_name}',
        'base': f'{MAIN_BRANCH}',
    }
    # print(f'pr_data {json.dumps(pr_data)}')
    pr_response = requests.post(pr_url, json=pr_data, headers=GIHUB_HEADERS).json()
    # print(f'pr_response {pr_response}')
    ##############################################################################################################


if __name__ == "__main__":    
    asyncio.run(improvise_pr_with_documentation())