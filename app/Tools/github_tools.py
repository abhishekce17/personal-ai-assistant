from langchain_core.tools import tool
from typing import Optional
import json
from app.services.github_tools_direct import Github_Tools_Direct


def make_tools(PAT: str):
    try:
        github = Github_Tools_Direct(personal_access_token=PAT)

        @tool
        def github_get_repo_structure(repo_name: str) -> str:
            """
            Get the structure of the repository

            Input Param:
                repo_name: Repository name

            Return:
                Structured Response of given repository
            """
            return json.dumps(github.get_repo_structure(repo_name))

        @tool
        def github_get_repo_list() -> str:
            """
            Get a list of all repositories

            Return:
                Dictionary containing status and list of repository names
            """
            return json.dumps(github.get_repo_list())

        @tool
        def github_get_repo_info(repo_name: str) -> str:
            """
            Get information about a repository

            Input Param:
                repo_name: Repository name

            Return:
                Dictionary containing repository information including name, description,
                created/updated dates, language, stars, forks, contributors, and owner
            """
            return json.dumps(github.get_repo_info(repo_name))

        @tool
        def github_get_file_content(repo_name: str, file_path: str) -> str:
            """
            Get the content of a file in the repository

            Input Params:
                repo_name: Repository name
                file_path: Path to the file in the repository

            Return:
                Dictionary containing status and decoded file content
            """
            return json.dumps(github.get_file_content(repo_name, file_path))

        @tool
        def github_write_file(
            repo_name: str,
            file_path: str,
            content: str,
            commit_msg: str = "Agent Updating file via API",
        ) -> str:
            """
            Write/update a file in the repository

            Input Params:
                repo_name: Repository name
                file_path: Path to the file in the repository
                content: New content for the file
                commit_msg: Commit message for the update

            Return:
                Dictionary containing status and updated file information
            """
            return json.dumps(
                github.write_file(repo_name, file_path, content, commit_msg)
            )

        @tool
        def github_create_file(
            repo_name: str,
            file_path: str,
            content: str,
            commit_msg: str = "Agent Creating file via API",
            branch: str = "main",
        ) -> str:
            """
            Create a new file in the repository

            Input Params:
                repo_name: Repository name
                file_path: Path where the file should be created
                content: Content for the new file
                commit_msg: Commit message for the file creation
                branch: Branch where the file should be created

            Return:
                Dictionary containing status and created file information
            """
            return json.dumps(
                github.create_file(repo_name, file_path, content, commit_msg, branch)
            )

        @tool
        def github_list_issues(repo_name: str) -> str:
            """
            List all issues in the repository

            Input Param:
                repo_name: Repository name

            Return:
                Dictionary containing status and list of issues with their details
            """
            return json.dumps(github.list_issues(repo_name))

        @tool
        def github_create_issue(
            repo_name: str, title: str, body: Optional[str] = None
        ) -> str:
            """
            Create a new issue in the repository

            Input Params:
                repo_name: Repository name
                title: Issue title
                body: Issue body/description (optional)

            Return:
                Dictionary containing status and created issue information
            """
            return json.dumps(github.create_issue(repo_name, title, body))

        @tool
        def github_read_issue(repo_name: str, issue_number: int) -> str:
            """
            Read an issue from the repository

            Input Params:
                repo_name: Repository name
                issue_number: Issue number to read

            Return:
                Dictionary containing status and issue details
            """
            return json.dumps(github.read_issue(repo_name, issue_number))

        @tool
        def github_close_issue(
            repo_name: str, issue_number: int, close_reason: str
        ) -> str:
            """
            Close an issue in the repository

            Input Params:
                repo_name: Repository name
                issue_number: Issue number to close
                close_reason: Reason for closing the issue

            Return:
                Dictionary containing status of the close operation
            """
            return json.dumps(github.close_issue(repo_name, issue_number, close_reason))

        @tool
        def github_list_pull_requests(repo_name: str) -> str:
            """
            List all pull requests in the repository

            Input Param:
                repo_name: Repository name

            Return:
                Dictionary containing status and list of pull requests with their details
            """
            return json.dumps(github.list_pull_requests(repo_name))

        @tool
        def github_read_pull_request(repo_name: str, pr_number: int) -> str:
            """
            Read a pull request from the repository

            Input Params:
                repo_name: Repository name
                pr_number: Pull request number to read

            Return:
                Dictionary containing status and pull request details including changed files
            """
            return json.dumps(github.read_pull_request(repo_name, pr_number))

        @tool
        def github_create_pull_request(
            repo_name: str,
            title: str,
            body: str,
            head: str,
            base: str,
            issue_number: Optional[int] = None,
        ) -> str:
            """
            Create a new pull request in the repository

            Input Params:
                repo_name: Repository name
                title: Pull request title
                body: Pull request body/description
                head: Source branch for the pull request
                base: Target branch for the pull request
                issue_number: Optional issue number to link with the PR

            Return:
                Dictionary containing status and created pull request information
            """
            return json.dumps(
                github.create_pull_request(
                    repo_name, title, body, head, base, issue_number
                )
            )

        @tool
        def github_get_pr_diff(repo_name: str, pr_number: int) -> str:
            """
            Get the diff of a pull request

            Input Params:
                repo_name: Repository name
                pr_number: Pull request number

            Return:
                Dictionary containing status and full diff content of the pull request
            """
            return json.dumps(github.get_pr_diff(repo_name, pr_number))

        @tool
        def github_merge_pull_request(repo_name: str, pr_number: int) -> str:
            """
            Merge a pull request in the repository

            Input Params:
                repo_name: Repository name
                pr_number: Pull request number to merge

            Return:
                Dictionary containing status and merge operation result
            """
            return json.dumps(github.merge_pull_request(repo_name, pr_number))

        @tool
        def github_close_pull_request(
            repo_name: str, pr_number: int, close_reason: str
        ) -> str:
            """
            Close a pull request in the repository

            Input Params:
                repo_name: Repository name
                pr_number: Pull request number to close
                close_reason: Reason for closing the pull request

            Return:
                Dictionary containing status of the close operation
            """
            return json.dumps(
                github.close_pull_request(repo_name, pr_number, close_reason)
            )

        @tool
        def github_role_back_to_commits_sha(
            repo_name: str, branch_name: str, commit_sha: str
        ) -> str:
            """
            Revert the repository to a specific commit SHA

            Input Params:
                repo_name: Repository name
                branch_name: Branch name to rollback
                commit_sha: Commit SHA to rollback to

            Return:
                Dictionary containing status and rollback operation result
            """
            return json.dumps(
                github.rollback_to_commit(repo_name, branch_name, commit_sha)
            )

        @tool
        def github_list_commits_log_oneline(
            repo_name: str, branch_name: str = "main", limit: int = 20
        ) -> str:
            """
            List all commits in the branch with one-line log

            Input Params:
                repo_name: Repository name
                branch_name: Branch name to get commits from (default: "main")
                limit: Maximum number of commits to retrieve (default: 20)

            Return:
                Dictionary containing status and list of commits with short SHA, message, author, and date
            """
            return json.dumps(
                github.list_commits_log_oneline(repo_name, branch_name, limit)
            )

        @tool
        def github_create_branch(
            repo_name: str, branch_name: str, source_branch: str = "main"
        ) -> str:
            """
            Create a new branch in the repository

            Input Params:
                repo_name: Repository name
                branch_name: Name for the new branch
                source_branch: Source branch to create from (default: "main")

            Return:
                Dictionary containing status and created branch information
            """
            return json.dumps(
                github.create_branch(repo_name, branch_name, source_branch)
            )

        @tool
        def github_delete_branch(repo_name: str, branch_name: str) -> str:
            """
            Delete a branch from the repository

            Input Params:
                repo_name: Repository name
                branch_name: Branch name to delete

            Return:
                Dictionary containing status of the delete operation
            """
            return json.dumps(github.delete_branch(repo_name, branch_name))

        @tool
        def github_list_branches(repo_name: str) -> str:
            """
            List all branches in the repository

            Input Param:
                repo_name: Repository name

            Return:
                Dictionary containing status and list of branches with their names and protection status
            """
            return json.dumps(github.list_branches(repo_name))

        @tool
        def github_search_code(
            repo_name: str, query: str, branch_name: Optional[str] = None
        ) -> str:
            """
            Search code in the repository using keywords

            Input Params:
                repo_name: Repository name
                query: Search query/keywords
                branch_name: Specific branch to search in (optional, searches all branches if None)

            Return:
                Dictionary containing status and search results with file paths, URLs, and SHAs
            """
            return json.dumps(github.search_code(repo_name, query, branch_name))

        return [
            github_get_repo_structure,
            github_get_repo_list,
            github_get_repo_info,
            github_get_file_content,
            github_write_file,
            github_create_file,
            github_list_issues,
            github_create_issue,
            github_read_issue,
            github_close_issue,
            github_list_pull_requests,
            github_read_pull_request,
            github_create_pull_request,
            github_get_pr_diff,
            github_merge_pull_request,
            github_close_pull_request,
            github_role_back_to_commits_sha,
            github_list_commits_log_oneline,
            github_create_branch,
            github_delete_branch,
            github_list_branches,
            github_search_code,
        ]
    except Exception as e:
        return []
