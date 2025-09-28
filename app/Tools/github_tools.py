# from langchain_community.agent_toolkits.github.toolkit import GitHubToolkit
# from langchain_community.utilities.github import GitHubAPIWrapper
# from dotenv import load_dotenv
# import os

# load_dotenv()

# GITHUB_APP_ID = os.getenv("GITHUB_APP_ID")
# GITHUB_APP_CLIENT_ID = os.getenv("GITHUB_APP_CLIENT_ID")
# GITHUB_APP_CLIENT_SECRET = os.getenv("GITHUB_APP_CLIENT_SECRET")
# GITHUB_PERSONAL_ACCESS_TOKEN = os.getenv("GITHUB_PERSONAL_ACCESS_TOKEN")
# GITHUB_APP_PRIVATE_KEY_PATH = os.getenv("GITHUB_APP_PRIVATE_KEY_PATH")
# GITHUB_APP_PRIVATE_KEY = None

# if GITHUB_APP_PRIVATE_KEY_PATH and os.path.exists(GITHUB_APP_PRIVATE_KEY_PATH):
#     with open(GITHUB_APP_PRIVATE_KEY_PATH, "r") as f:
#         GITHUB_APP_PRIVATE_KEY = f.read()

# # Try Personal Access Token first, fallback to GitHub App
# try:
#     if GITHUB_PERSONAL_ACCESS_TOKEN:
#         github = GitHubAPIWrapper(
#             github_repository="abhishekce17/orvio",
#             github_personal_access_token=GITHUB_PERSONAL_ACCESS_TOKEN,
#         )
#         print("Using Personal Access Token authentication")
#     else:
#         raise ValueError("No personal access token")
# except Exception as e:
#     print(f"Personal Access Token failed: {e}")
#     print("Trying GitHub App authentication...")
#     github = GitHubAPIWrapper(
#         github_repository="abhishekce17/orvio",
#         github_app_id=GITHUB_APP_ID,
#         github_app_private_key=GITHUB_APP_PRIVATE_KEY,
#     )
# toolkit = GitHubToolkit.from_github_api_wrapper(github)

# tools = toolkit.get_tools()

# for tool in tools:
#     print(tool.name)
#     if tool.name == "Read File":
#         print(tool.description)
#         result = tool.run(tool_input="lib/main.dart")
#         print("Result of running the tool:")
#         print(result)


# LangChain GitHub Toolkit seems to have issues with GitHub App authentication. The above code tries to use a Personal Access Token first, and falls back to GitHub App if that fails. If both methods fail, it will raise an error.
