import requests
import base64
import json

# Replace these with your GitHub details
GITHUB_ORG = 'your-organization-name'        # Organization name
GITHUB_TOKEN = 'your-personal-access-token'  # GitHub personal access token

# GitHub API URL for listing all repos in the organization
REPOS_API_URL = f'https://api.github.com/orgs/{GITHUB_ORG}/repos'

# Headers to authenticate API requests
headers = {
    'Authorization': f'Bearer {GITHUB_TOKEN}',
    'Accept': 'application/vnd.github.v3+json'
}

# Get all repositories in the organization
def get_all_repositories():
    repos = []
    page = 1
    while True:
        response = requests.get(REPOS_API_URL, headers=headers, params={'page': page, 'per_page': 100})
        if response.status_code == 200:
            repos.extend(response.json())
            if len(response.json()) < 100:
                break
            page += 1
        else:
            print(f"Error fetching repos: {response.status_code}")
            break
    return repos

# Get the list of workflows in the .github/workflows directory of a repo
def get_workflows(repo_name):
    workflows_url = f'https://api.github.com/repos/{GITHUB_ORG}/{repo_name}/contents/.github/workflows/'
    response = requests.get(workflows_url, headers=headers)
    if response.status_code == 200:
        return response.json()  # List of workflow files
    else:
        print(f"Error fetching workflows for {repo_name}: {response.status_code}")
        return None

# Get the content of a workflow file
def get_file_content(repo_name, file_path):
    file_url = f'https://api.github.com/repos/{GITHUB_ORG}/{repo_name}/contents/{file_path}'
    response = requests.get(file_url, headers=headers)
    if response.status_code == 200:
        content = response.json()['content']
        return base64.b64decode(content).decode('utf-8')
    else:
        print(f"Error getting file content for {file_path} in {repo_name}: {response.status_code}")
        return None

# Disable a workflow by commenting out the entire file content
def disable_workflow(repo_name, workflow_file):
    workflow_file_path = workflow_file['path']
    workflow_content = get_file_content(repo_name, workflow_file_path)
    
    if workflow_content:
        # Comment out the entire content
        disabled_content = f"# {workflow_content}"
        update_file(repo_name, workflow_file_path, disabled_content, "Disable workflow")

# Enable a workflow by restoring the original content
def enable_workflow(repo_name, workflow_file):
    workflow_file_path = workflow_file['path']
    workflow_content = get_file_content(repo_name, workflow_file_path)
    
    if workflow_content:
        # Restore the original content
        update_file(repo_name, workflow_file_path, workflow_content, "Enable workflow")

# Update the file in GitHub (either disable or enable workflow)
def update_file(repo_name, file_path, content, commit_message):
    file_url = f'https://api.github.com/repos/{GITHUB_ORG}/{repo_name}/contents/{file_path}'
    file_content = base64.b64encode(content.encode('utf-8')).decode('utf-8')
    
    # Get the file's sha (necessary for update)
    response = requests.get(file_url, headers=headers)
    if response.status_code == 200:
        sha = response.json()['sha']
    else:
        print(f"Error fetching file info for {file_path} in {repo_name}: {response.status_code}")
        return

    # Prepare the request data
    data = {
        'message': commit_message,
        'content': file_content,
        'sha': sha
    }

    # Send the update request
    response = requests.put(file_url, headers=headers, data=json.dumps(data))
    if response.status_code == 200:
        print(f"Workflow {file_path} in {repo_name} has been updated.")
    else:
        print(f"Error updating {file_path} in {repo_name}: {response.status_code} - {response.text}")

# Main function to disable and enable workflows in all repositories of the organization
def main():
    # Fetch all repositories in the organization
    repos = get_all_repositories()
    
    # Iterate through all repositories
    for repo in repos:
        repo_name = repo['name']
        print(f"Processing repository: {repo_name}")
        
        # Fetch workflows in the current repository
        workflows = get_workflows(repo_name)
        if workflows:
            for workflow in workflows:
                if 'workflow' in workflow['name']:  # You can adjust the logic to match specific workflows
                    print(f"Disabling workflow: {workflow['name']} in {repo_name}")
                    disable_workflow(repo_name, workflow)

    # Once workflows are disabled, you can enable them
    # Uncomment below block to enable workflows after disabling
    # for repo in repos:
    #     repo_name = repo['name']
    #     print(f"Re-enabling workflows in repository: {repo_name}")
    #     workflows = get_workflows(repo_name)
    #     if workflows:
    #         for workflow in workflows:
    #             if 'workflow' in workflow['name']:
    #                 print(f"Enabling workflow: {workflow['name']} in {repo_name}")
    #                 enable_workflow(repo_name, workflow)

if __name__ == "__main__":
    main()
