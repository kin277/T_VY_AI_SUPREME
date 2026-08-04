import os
import pandas as pd
import matplotlib.pyplot as plt
from github import Github

from langchain_experimental.tools import PythonREPLTool
from langchain_core.tools import tool
from langchain_community.utilities.wolfram_alpha import WolframAlphaAPIWrapper
from langchain_community.tools import WolframAlphaQueryRun
from langchain_community.utilities import ArxivAPIWrapper
from langchain_community.tools import ArxivQueryRun
from langchain_community.utilities import WikipediaAPIWrapper
from langchain_community.tools import WikipediaQueryRun
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_tavily import TavilySearchResults

# 1. Python REPL
python_repl_tool = PythonREPLTool()

# 2. GitHub Search
@tool
def github_search_repos(query: str) -> str:
    """Tìm kiếm repository trên GitHub theo từ khóa query."""
    token = os.getenv("GITHUB_TOKEN", "")
    if not token:
        return "Chưa cấu hình GITHUB_TOKEN trong biến môi trường."
    try:
        g = Github(token)
        repos = g.search_repositories(query=query)
        results = [f"- {repo.full_name}: {repo.html_url}" for repo in repos[:5]]
        return "\n".join(results) if results else "Không tìm thấy repository nào."
    except Exception as e:
        return f"Lỗi GitHub API: {str(e)}"

# 3. Data Analysis
@tool
def analyze_data_file(file_path: str) -> str:
    """Đọc tệp CSV/Excel bằng pandas và trả về tóm tắt dữ liệu."""
    try:
        if file_path.endswith('.csv'):
            df = pd.read_csv(file_path)
        elif file_path.endswith(('.xls', '.xlsx')):
            df = pd.read_excel(file_path)
        else:
            return "Định dạng tệp không hỗ trợ (chỉ nhận .csv, .xls, .xlsx)."
        
        return (
            f"Tệp: {file_path}\n"
            f"Kích thước: {df.shape[0]} hàng, {df.shape[1]} cột\n"
            f"Danh sách cột: {list(df.columns)}\n\n"
            f"Mô tả thống kê:\n{df.describe().to_string()}"
        )
    except Exception as e:
        return f"Lỗi khi đọc tệp dữ liệu: {str(e)}"

# 4. Wolfram Alpha
wolfram_tool = WolframAlphaQueryRun(api_wrapper=WolframAlphaAPIWrapper())

# 5. ArXiv
arxiv_tool = ArxivQueryRun(api_wrapper=ArxivAPIWrapper())

# 6. Wikipedia
wikipedia_tool = WikipediaQueryRun(api_wrapper=WikipediaAPIWrapper())

# 7. DuckDuckGo
duckduckgo_tool = DuckDuckGoSearchRun()

# 8. Tavily
tavily_tool = TavilySearchResults(max_results=3)

# DANH SÁCH TẤT CẢ TOOLS ĐỂ EXPORT
all_tools = [
    python_repl_tool,
    github_search_repos,
    analyze_data_file,
    wolfram_tool,
    arxiv_tool,
    wikipedia_tool,
    duckduckgo_tool,
    tavily_tool
]