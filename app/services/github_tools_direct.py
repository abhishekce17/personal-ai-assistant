from app.core.base import CommonGitToolBase
import github
import requests
from typing import Any, Dict, Optional, List


class Github_Tools_Direct(CommonGitToolBase):
    # class Github_Tools_Direct:  # Only for testing purpose
    def __init__(self, personal_access_token: str = None):
        auth = github.Auth.Token(personal_access_token)
        self.github = github.Github(auth=auth)
        try:
            self.user = self.github.get_user()
            self.repos = self.user.get_repos()
        except github.GithubException as e:
            raise ValueError(f"Invalid GitHub PAT: {e.data.get('message', str(e))}")

    def get_repo_list(self) -> Dict[str, Any]:
        try:
            if not self.repos:
                return {"status": 404, "message": "No repositories found"}
            return {"status": 200, "data": [repo.name for repo in self.repos]}
        except Exception as e:
            return {"status": 500, "message": str(e)}

    def get_file_content(self, repo_name, file_path):
        try:
            repo = self._get_repo_instance(repo_name)
            file = repo.get_contents(file_path)
            return {"status": 200, "data": file.decoded_content.decode("utf-8")}
        except Exception as e:
            return {"status": getattr(e, "status", 500), "message": str(e)}

    def get_repo_structure(self, repo_name, directory_path=""):
        try:
            repo = self._get_repo_instance(repo_name)
            structure = self._get_repo_structure(repo=repo, path=directory_path)
            return {"status": 200, "data": structure}
        except Exception as e:
            return {"status": getattr(e, "status", 500), "message": str(e)}

    # def list_files_in_repo(self, repo_name):
    #     try:
    #         repo = self._get_repo_instance(repo_name)
    #         return {
    #             "status": 200,
    #             "data": [
    #                 file.path for file in repo.get_contents("") if file.type == "file"
    #             ],
    #         }
    #     except Exception as e:
    #         return {"status": getattr(e, "status", 500), "message": str(e)}

    def get_repo_info(self, repo_name):
        try:
            repo = self._get_repo_instance(repo_name)
            return {
                "status": 200,
                "data": {
                    "name": repo.name,
                    "description": repo.description,
                    "created_at": repo.created_at.isoformat(),
                    "updated_at": repo.updated_at.isoformat(),
                    "language": repo.language,
                    "stars": repo.stargazers_count,
                    "forks": repo.forks_count,
                    "contributors": repo.get_contributors().totalCount,
                    "owner": repo.owner.login,
                },
            }
        except Exception as e:
            return {"status": getattr(e, "status", 500), "message": str(e)}

    def write_file(
        self,
        repo_name: str,
        file_path: str,
        content: str,
        commit_msg: str = "Agent Updating file via API",
    ) -> Dict[str, Any]:
        try:
            repo = self._get_repo_instance(repo_name)
            try:
                existing_file = repo.get_contents(file_path)
                updated_file = repo.update_file(
                    existing_file.path,
                    commit_msg,
                    content,
                    existing_file.sha,
                )
                return {"status": 200, "file": updated_file}
            except github.GithubException as e:
                return {"status": e.status, "message": str(e)}
        except Exception as e:
            return {"status": getattr(e, "status", 500), "message": str(e)}

    def create_file(
        self,
        repo_name: str,
        file_path: str,
        content: str,
        commit_msg: str = "Agent Creating file via API",
        branch: str = "main",
    ) -> Dict[str, Any]:
        try:
            repo = self._get_repo_instance(repo_name)
            if repo.name == repo_name:
                try:
                    try:
                        repo.get_contents(file_path)
                        return {"status": 400, "message": "File already exists"}
                    except github.GithubException as e:
                        new_file = repo.create_file(
                            file_path, commit_msg, content, branch
                        )
                        return {
                            "status": 200,
                            "file": new_file,
                        }
                except github.GithubException as e:
                    return {"status": e.status, "message": str(e)}
            return {
                "status": getattr(e, "status", 500),
                "message": "Repository not found",
            }
        except Exception as e:
            return {"status": getattr(e, "status", 500), "message": str(e)}

    def list_issues(self, repo_name: str):
        try:
            repo = self._get_repo_instance(repo_name)
            issues = repo.get_issues(state="all")
            return {
                "status": 200,
                "data": [
                    {
                        "id": issue.id,
                        "number": issue.number,
                        "title": issue.title,
                        "body": issue.body,
                        "state": issue.state,
                        "created_at": issue.created_at.isoformat(),
                        "updated_at": issue.updated_at.isoformat(),
                        "user": issue.user.login,
                    }
                    for issue in issues
                ],
            }
        except Exception as e:
            return {"status": getattr(e, "status", 500), "message": str(e)}

    def create_issue(
        self, repo_name: str, title: str, body: Any = None
    ) -> Dict[str, Any]:
        try:
            repo = self._get_repo_instance(repo_name)
            new_issue = repo.create_issue(title=title, body=body)
            return {
                "status": 200,
                "issue": {
                    "id": new_issue.id,
                    "number": new_issue.number,
                    "title": new_issue.title,
                    "body": new_issue.body,
                    "state": new_issue.state,
                    "created_at": new_issue.created_at.isoformat(),
                    "updated_at": new_issue.updated_at.isoformat(),
                    "user": new_issue.user.login,
                },
            }
        except Exception as e:
            return {"status": getattr(e, "status", 500), "message": str(e)}

    def read_issue(self, repo_name: str, issue_number: int) -> Dict[str, Any]:
        try:
            repo = self._get_repo_instance(repo_name)
            issue = repo.get_issue(issue_number)
            return {
                "status": 200,
                "issue": {
                    "id": issue.id,
                    "number": issue.number,
                    "title": issue.title,
                    "body": issue.body,
                    "state": issue.state,
                    "created_at": issue.created_at.isoformat(),
                    "updated_at": issue.updated_at.isoformat(),
                    "user": issue.user.login,
                },
            }
        except Exception as e:
            return {"status": getattr(e, "status", 500), "message": str(e)}

    def close_issue(
        self, repo_name: str, issue_number: int, close_reason: str
    ) -> Dict[str, Any]:
        try:
            repo = self._get_repo_instance(repo_name)
            issue = repo.get_issue(issue_number)
            if issue.state == "closed":
                return {"status": 400, "message": "Issue already closed"}
            issue.edit(state="closed", close_reason=close_reason)
            return {"status": 200}
        except Exception as e:
            return {"status": getattr(e, "status", 500), "message": str(e)}

    # There is no methode to support comment on pr or issue
    # def comment_on_issue_or_pr(self, repo_name: str, issue_number: int, pr_number : int, comment: str) -> Dict[str, Any]:
    #     for repo in self.repos:
    #         if repo.name == repo_name:
    #             try:
    #                 if pr_number:
    #                     repo.comment_on_pr(pr_number, comment)
    #                 if issue_number:
    #                     repo.comment_on_issue(issue_number, comment)
    #                 return {"status": 200}
    #             except github.GithubException as e:
    #                 return {"status": getattr(e, "status", 500), "message": str(e)}
    #     return {"status": getattr(e, "status", 500), "message": "Repository not found"}

    def list_pull_requests(self, repo_name: str) -> Dict[str, Any]:
        try:
            repo = self._get_repo_instance(repo_name)
            pull_requests = repo.get_pulls()
            return {
                "status": 200,
                "pull_requests": [
                    {
                        "id": pr.id,
                        "number": pr.number,
                        "title": pr.title,
                        "body": pr.body,
                        "state": pr.state,
                        "created_at": pr.created_at.isoformat(),
                        "updated_at": pr.updated_at.isoformat(),
                        "user": pr.user.login,
                    }
                    for pr in pull_requests
                ],
            }
        except Exception as e:
            return {"status": getattr(e, "status", 500), "message": str(e)}

    def read_pull_request(self, repo_name: str, pr_number: int) -> Dict[str, Any]:
        try:
            repo = self._get_repo_instance(repo_name)
            pr = repo.get_pull(pr_number)
            if pr is None:
                return {"status": 404, "message": "Pull request not found"}
            files = []
            for f in pr.get_files():
                files.append(
                    {
                        "filename": f.filename,
                        "status": f.status,
                        "additions": f.additions,
                        "deletions": f.deletions,
                        "changes": f.changes,
                        "patch": f.patch,  # small diff snippet for this file
                    }
                )

            return {
                "status": 200,
                "pull_request": {
                    "id": pr.id,
                    "number": pr.number,
                    "title": pr.title,
                    "body": pr.body,
                    "state": pr.state,
                    "created_at": pr.created_at.isoformat(),
                    "updated_at": pr.updated_at.isoformat(),
                    "user": pr.user.login,
                    "files": files,  # ✅ include changed files
                },
            }
        except Exception as e:
            return {"status": getattr(e, "status", 500), "message": str(e)}

    def get_pr_diff(self, repo_name: str, pr_number: int) -> Dict[str, Any]:
        try:
            repo = self._get_repo_instance(repo_name)
            pr = repo.get_pull(pr_number)

            # GitHub API requires Accept header for raw diff
            headers = {"Accept": "application/vnd.github.v3.diff"}
            response = requests.get(pr.url, headers=headers)

            if response.status_code == 200:
                return {
                    "status": 200,
                    "diff": response.text,  # full diff content here
                }
            else:
                return {
                    "status": getattr(e, "status", 500),
                    "message": f"Failed to fetch diff (HTTP {response.status_code})",
                }
        except Exception as e:
            return {"status": getattr(e, "status", 500), "message": str(e)}

    def create_pull_request(
        self,
        repo_name: str,
        title: str,
        body: str,
        head: str,
        base: str,
        issue_number: int = None,
    ) -> Dict[str, Any]:
        try:
            try:
                repo = self._get_repo_instance(repo_name)
                issue = None
                if issue_number:
                    issue = repo.get_issue(number=issue_number)
                    body = (
                        body + f"\n\nLinked to issue #{issue_number}: {issue.html_url}"
                    )
                new_pr = repo.create_pull(title=title, body=body, head=head, base=base)
                return {
                    "status": 200,
                    "pull_request": {
                        "id": new_pr.id,
                        "number": new_pr.number,
                        "title": new_pr.title,
                        "body": new_pr.body,
                        "state": new_pr.state,
                        "created_at": new_pr.created_at.isoformat(),
                        "updated_at": new_pr.updated_at.isoformat(),
                        "user": new_pr.user.login,
                    },
                }
            except github.GithubException as e:
                return {"status": e.status, "message": str(e)}
        except Exception as e:
            return {"status": getattr(e, "status", 500), "message": str(e)}

    def merge_pull_request(self, repo_name: str, pr_number: int) -> Dict[str, Any]:
        try:
            repo = self._get_repo_instance(repo_name)
            pr = repo.get_pull(pr_number)
            if pr.is_merged():
                return {
                    "status": getattr(e, "status", 500),
                    "message": "Pull request already merged",
                }
            elif pr.mergeable is False:
                return {
                    "status": getattr(e, "status", 500),
                    "message": "Pull request has merge conflicts",
                }
            merge_result = pr.merge(
                delete_branch=False,
            )
            if merge_result.merged:
                return {
                    "status": 200,
                    "message": f"Pull request #{pr_number} merged successfully",
                }
            else:
                return {
                    "status": getattr(e, "status", 500),
                    "message": f"Failed to merge pull request: {merge_result.message}",
                }
        except Exception as e:
            return {"status": getattr(e, "status", 500), "message": str(e)}

    def close_pull_request(
        self, repo_name: str, pr_number: int, close_reason: str
    ) -> Dict[str, Any]:
        try:
            repo = self._get_repo_instance(repo_name)
            pr = repo.get_pull(pr_number)
            pr.edit(state="closed", body=close_reason)
            return {
                "status": 200,
                "message": f"Pull request #{pr_number} closed successfully",
            }
        except Exception as e:
            return {"status": getattr(e, "status", 500), "message": str(e)}

    def rollback_to_commit(
        self, repo_name: str, branch_name: str, commit_sha: str
    ) -> Dict[str, Any]:
        try:
            repo = self._get_repo_instance(repo_name)
            ref = repo.get_git_ref(f"heads/{branch_name}")
            ref.edit(commit_sha, force=True)  # ⚠️ force=True is required
            return {
                "status": 200,
                "message": f"Branch '{branch_name}' reset to commit {commit_sha}",
            }
        except Exception as e:
            return {"status": getattr(e, "status", 500), "message": str(e)}

    def list_commits_log_oneline(
        self, repo_name: str, branch_name: str = "main", limit: int = 20
    ) -> Dict[str, Any]:
        try:
            repo = self._get_repo_instance(repo_name)
            commits = repo.get_commits(sha=branch_name)[
                :limit
            ]  # limit to avoid huge responses
            return {
                "status": 200,
                "commits": [
                    {
                        "sha": commit.sha[:7],  # short SHA like `git log --oneline`
                        "message": commit.commit.message.split("\n")[0],
                        "author": (
                            commit.commit.author.name
                            if commit.commit.author
                            else "Unknown"
                        ),
                        "date": (
                            commit.commit.author.date.isoformat()
                            if commit.commit.author
                            else None
                        ),
                    }
                    for commit in commits
                ],
            }
        except Exception as e:
            return {"status": getattr(e, "status", 500), "message": str(e)}

    # def get_commit(self, repo_name, commit_sha):
    #     raise NotImplementedError

    def create_branch(
        self, repo_name: str, branch_name: str, source_branch: str = "main"
    ) -> Dict[str, Any]:
        try:
            repo = self._get_repo_instance(repo_name)
            # Get source branch reference
            source_ref = repo.get_git_ref(f"heads/{source_branch}")
            source_sha = source_ref.object.sha

            # Create new branch ref
            repo.create_git_ref(ref=f"refs/heads/{branch_name}", sha=source_sha)

            return {
                "status": 200,
                "message": f"Branch '{branch_name}' created from '{source_branch}' by Agent",
                "source_sha": source_sha,
            }
        except Exception as e:
            return {"status": getattr(e, "status", 500), "message": str(e)}

    def delete_branch(self, repo_name: str, branch_name: str) -> Dict[str, Any]:
        try:
            repo = self._get_repo_instance(repo_name)
            ref = repo.get_git_ref(f"heads/{branch_name}")
            ref.delete()  # 🚀 deletes the branch
            return {
                "status": 200,
                "message": f"Branch '{branch_name}' deleted successfully",
            }
        except Exception as e:
            return {"status": getattr(e, "status", 500), "message": str(e)}

    def list_branches(self, repo_name: str) -> Dict[str, Any]:
        try:
            repo = self._get_repo_instance(repo_name)
            branches = repo.get_branches()
            return {
                "status": 200,
                "branches": [
                    {"name": branch.name, "protected": branch.protected}
                    for branch in branches
                ],
            }
        except Exception as e:
            return {"status": getattr(e, "status", 500), "message": str(e)}

    def search_code(
        self, repo_name: str, query: str, branch_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Search code in a repository using keywords.
        If branch_name is None, searches all branches.
        """
        try:
            repo = self._get_repo_instance(repo_name)
            branches = (
                [branch_name] if branch_name else [b.name for b in repo.get_branches()]
            )
            all_results = []

            for branch in branches:
                search_query = f"{query} repo:{repo.full_name} ref:{branch}"
                results = self.github.search_code(search_query)
                for item in results:
                    all_results.append(
                        {
                            "branch": branch,
                            "path": item.path,
                            "repository": item.repository.full_name,
                            "url": item.html_url,
                            "sha": item.sha,
                        }
                    )

            return {"status": 200, "results": all_results}
        except Exception as e:
            return {"status": getattr(e, "status", 500), "message": str(e)}

    def _get_repo_instance(self, repo_name: str):
        if not self.repos:
            raise Exception("No Repository Found")
        for repo in self.repos:
            if repo.name == repo_name:
                return repo
        raise Exception("Repository Not Found")

    def _get_repo_structure(self, repo: any, path=""):
        contents = repo.get_contents(path)
        structure = {}
        for content in contents:
            if content.type == "dir":
                structure[content.name] = self._get_repo_structure(repo, content.path)
            else:
                structure[content.name] = "file"
        return structure

    # def search_issues_or_prs(self, repo_name, query):
    #     raise NotImplementedError


# Example usage:
# github_tools = Github_Tools_Direct()
# repo_list = github_tools.get_repo_list() --------------- working
# repo_structure = github_tools.get_repo_structure(
#     "CodeXCoder", directory_path="src/app/account"
# ) --------------- working
# get_file_content = github_tools.get_file_content(
#     repo_name="CodeXCoder", file_path="src/app/account/account-setting/page.jsx"
# ) -------------- working

# list_files = github_tools.list_files_in_repo("CodeXCoder") #not useful

# repo_info = github_tools.get_repo_info("CodeXCoder") ------------     working

# written_file = github_tools.write_file(
#     repo_name="CodeXCoder",
#     file_path="src/app/account/account-setting/page.jsx",
#     content="Updated by Agent",
# ) ----------------- working but replacing whole file content

# rolled_back = github_tools.rollback_to_commit(
#     repo_name="CodeXCoder",
#     branch_name="main",
#     commit_sha="3bbd6fd6974d532e5de30c89eb5112d813ef6c3c",
# ) ------------------- working

# created_file = github_tools.create_file(
#     repo_name="CodeXCoder",
#     file_path="src/app/account/account-setting/agent_created_file_#3.txt",
#     content="Created by Agent",
#     commit_msg="Agent Creating file via API this file",
#     branch="test/llm_testing",
# )  # ------------------- working

# created_issue = github_tools.create_issue(
#     repo_name="CodeXCoder",
#     title="Issue created by Agent",
#     body="This issue was created automatically by an agent for testing.",
# )  # ------------------- working

# list_issues = github_tools.list_issues("CodeXCoder") ------------------- working

# closed_issue = github_tools.close_issue(
#     repo_name="CodeXCoder",
#     issue_number=1,
#     close_reason="Closing this issue as it was created for testing purposes.",
# ) ------------------- working

# list_commit_logs = github_tools.list_commits_log_oneline(
#     repo_name="CodeXCoder",
# ) ----------------- working

# create_branch = github_tools.create_branch(
#     repo_name="CodeXCoder", branch_name="test/llm_testing#2", source_branch="main"
# ) ---------------- - working

# list_branches = github_tools.list_branches("CodeXCoder")  # ---------------- working

# deleted_branch = github_tools.delete_branch(
#     repo_name="CodeXCoder", branch_name="test/llm_testing#2"
# )  --------------- working

# created_pr = github_tools.create_pull_request(
#     repo_name="CodeXCoder",
#     title="Test PR from Agent",
#     body="This PR was created by an agent for testing purposes.",
#     head="test/llm_testing",
#     base="main",
# )  # ---------------- working

# list_pr = github_tools.list_pull_requests("CodeXCoder")  # ---------------- working

# read_pr = github_tools.read_pull_request(
#     "CodeXCoder", pr_number=2
# )  # ---------------- working

# merge_pr = github_tools.merge_pull_request(
#     repo_name="CodeXCoder", pr_number=2
# )  # ---------------- working

# close_pr = github_tools.close_pull_request(
#     repo_name="CodeXCoder", pr_number=3, close_reason="Closing this PR for testing."
# )  # ---------------- working

# print(json.dumps(repo_list, indent=4))
# print(json.dumps(repo_structure, indent=4))
# print(get_file_content)
# print(list_files)
# print(json.dumps(repo_info, indent=4))
# print(written_file)
# print(rolled_back)
# print(created_file)
# print(list_issues)
# print(closed_issue)
# print(list_commit_logs)
# print(create_branch)
# print(list_branches)
# print(deleted_branch)
# print(created_pr)
# print(list_pr)
# print(json.dumps(read_pr, indent=4))
# print(merge_pr)
# print(close_pr)
