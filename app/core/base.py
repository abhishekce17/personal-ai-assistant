from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, List


class CommonGitToolBase(ABC):
    @abstractmethod
    def get_repo_structure(self, repo_name: str) -> Dict[str, Any]:
        """Get the structure of the repository"""
        pass

    # @abstractmethod
    # def list_files_in_repo(self, repo_name: str) -> Dict[str, Any]:
    #     """List all files in the repository"""
    #     pass

    @abstractmethod
    def get_repo_list(self) -> Dict[str, Any]:
        """Get a list of all repositories"""
        pass

    @abstractmethod
    def get_repo_info(self, repo_name: str) -> Dict[str, Any]:
        """Get information about a repository"""
        pass

    @abstractmethod
    def get_file_content(self, repo_name: str, file_path: str) -> Any:
        """Get the content of a file in the repository"""
        pass

    @abstractmethod
    def write_file(
        self,
        repo_name: str,
        file_path: str,
        content: str,
        commit_msg: str = "Agent Updating file via API",
    ) -> Dict[str, Any]:
        """Write a file to the repository"""
        pass

    @abstractmethod
    def create_file(
        self,
        repo_name: str,
        file_path: str,
        content: str,
        commit_msg: str = "Agent Creating file via API",
        branch: str = "main",
    ) -> Dict[str, Any]:
        """Create a new file in the repository"""
        pass

    # @abstractmethod
    # def delete_file(self, repo_name: str, file_path: str) -> Dict[str, Any]:
    #     """Delete a file from the repository"""
    #     pass

    @abstractmethod
    def list_issues(self, repo_name: str) -> List[Dict[str, Any]]:
        """List all issues in the repository"""
        pass

    @abstractmethod
    def create_issue(
        self, repo_name: str, title: str, body: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a new issue in the repository"""
        pass

    @abstractmethod
    def read_issue(self, repo_name: str, issue_number: int) -> Dict[str, Any]:
        """Read an issue from the repository"""
        pass

    @abstractmethod
    def close_issue(
        self, repo_name: str, issue_number: int, close_reason: str
    ) -> Dict[str, Any]:
        """Close an issue in the repository"""
        pass

    # There is no methode to support comment on pr or issue
    # @abstractmethod
    # def comment_on_issue_or_pr(
    #     self, repo_name: str, issue_number: int, pr_number : int,comment: str
    # ) -> Dict[str, Any]:
    #     """Comment on an issue or pull request in the repository"""
    #     pass

    @abstractmethod
    def list_pull_requests(self, repo_name: str) -> List[Dict[str, Any]]:
        """List all pull requests in the repository"""
        pass

    @abstractmethod
    def read_pull_request(self, repo_name: str, pr_number: int) -> Dict[str, Any]:
        """Read a pull request from the repository"""
        pass

    @abstractmethod
    def create_pull_request(
        self,
        repo_name: str,
        title: str,
        body: str,
        head: str,
        base: str,
        issue_number: Optional[int],
    ) -> Dict[str, Any]:
        """Create a new pull request in the repository"""
        pass

    @abstractmethod
    def get_pr_diff(self, repo_name: str, pr_number: int) -> str:
        """Get the diff of a pull request"""
        pass

    @abstractmethod
    def merge_pull_request(self, repo_name: str, pr_number: int) -> Dict[str, Any]:
        """Merge a pull request in the repository"""
        pass

    @abstractmethod
    def close_pull_request(
        self, repo_name: str, pr_number: int, close_reason: str
    ) -> Dict[str, Any]:
        """Close a pull request in the repository"""
        pass

    @abstractmethod
    def role_back_to_commits_sha(
        self, repo_name: str, branch_name: str, commit_sha: str
    ) -> Dict[str, Any]:
        """Revert the repository to a specific commit SHA"""
        pass

    @abstractmethod
    def list_commits_log_oneline(
        self, repo_name: str, branch_name: str, limit: int
    ) -> Dict[str, Any]:
        """List all commits in the branch with one-line log"""

    @abstractmethod
    def create_branch(
        self, repo_name: str, branch_name: str, source_branch: str
    ) -> Dict[str, Any]:
        """Create a new branch in the repository"""
        pass

    @abstractmethod
    def delete_branch(self, repo_name: str, branch_name: str) -> Dict[str, Any]:
        """Delete a branch from the repository"""
        pass

    @abstractmethod
    def list_branches(self, repo_name: str) -> List[Dict[str, Any]]:
        """List all branches in the repository"""
        pass

    @abstractmethod
    def search_code(
        self, repo_name: str, query: str, branch_name: Optional[str]
    ) -> Dict[str, Any]:
        """Search code in the repository using keywords"""
        pass

    # @abstractmethod
    # def search_issues_or_prs(self, repo_name: str, query: str) -> Dict[str, Any]:
    #     """Search issues or pull requests in the repository using keywords"""
    #     pass
