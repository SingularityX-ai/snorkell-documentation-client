
# Snorkell DocGen Client

## Description

The "Snorkell DocGen Client" GitHub Action is designed to automate the creation of documentation pull requests for recent merges into the main branch. This action interacts with the Snorkell service to generate and commit documentation changes directly to your repository.

## Usage

To use this action in your workflow, add the following step to your `.github/workflows` YAML file:

```yaml
- name: Generate Documentation
  uses: snorkell.ai/snorkell-docgen-client@v1.0.0
  with:
    client_id: ${{ secrets.SNORKELL_CLIENT_ID }}
    api_key: ${{ secrets.SNORKELL_API_KEY }}
    branch_name: 'main'
```

### Inputs

- `client_id`: Your client ID for Snorkell. (Required)
- `api_key`: API Key for Snorkell. (Required)
- `branch_name`: Base Branch for the PR. (Required)

## How it Works

1. **Set up Python**: The action sets up a Python environment.
2. **Download Script and Install Dependencies**: It downloads the necessary script and installs dependencies.
3. **Prepare Commit Message**: Formats the commit message for the pull request.
4. **Run Script**: Executes the script to generate and commit the documentation.

### Script Behavior

- The script initiates documentation generation with the Snorkell service.
- It checks the status of documentation generation and prints updates.
- Handles exceptions and timeouts gracefully.