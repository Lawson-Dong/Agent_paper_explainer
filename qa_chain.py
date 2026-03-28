import os
import sys
import traceback
import tempfile
from io import StringIO

try:
    import docker
except ImportError:
    docker = None

from langchain_deepseek import ChatDeepSeek
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from vector_store import VectorStoreManager
from config import DEEPSEEK_API_KEY

# Role prompts for different personas
ROLE_PROMPTS = {
    "professor": """
    你是一位资深的AI for Physics教授，正在指导学生理解这篇论文。用户是你带的博士生或者硕士生。
    你的回答风格：
    - 强调论文的创新点和学术贡献
    - 指出该领域的研究脉络
    - 鼓励学生思考"为什么这个方法有效"
    - 语气循循善诱，像在学术讨论
    """,

    "reviewer": """
    你是一位顶刊审稿人，正在评审这篇论文。用户是论文的作者。
    你的回答风格：
    - 批判性分析方法的优缺点
    - 指出实验设计的严谨性
    - 提出改进建议
    - 语气严谨、客观、专业
    """,

    "student": """
    你是一个正在学习这个领域的研究生，刚刚读完这篇论文。用户是你的师兄或者师姐，你想跟师兄师姐讨论研究方向的问题。
    你的回答风格：
    - 提问式思考，比如"这个方法为什么比之前的好？"
    - 关注实现细节
    - 表达学习中的困惑点
    - 语气谦虚、好学
    """
}

class QAChain:
    def __init__(self, vectorstore_manager: VectorStoreManager, role: str = "professor"):
        self.vectorstore_manager = vectorstore_manager
        self.role = role
        self.llm = ChatDeepSeek(
            model="deepseek-chat",  # DeepSeek chat model
            api_key=DEEPSEEK_API_KEY,
            temperature=0
        )

        self.chat_history = []  # Simple list to store chat history

        # Create retrieval chain
        template = """Answer the question based only on the following context:
{context}

Question: {question}
"""
        prompt = ChatPromptTemplate.from_template(template)

        self.chain = (
            {"context": self.vectorstore_manager.vectorstore.as_retriever(search_kwargs={"k": 4}), "question": RunnablePassthrough()}
            | prompt
            | self.llm
            | StrOutputParser()
        )

    def set_role(self, role: str):
        """Change the AI role/persona"""
        if role in ROLE_PROMPTS:
            self.role = role
        else:
            raise ValueError(f"Unknown role: {role}. Available roles: {list(ROLE_PROMPTS.keys())}")

    def ask_question(self, question: str) -> dict:
        """
        Ask a question and get the answer with source documents.
        """
        # Get relevant documents
        docs = self.vectorstore_manager.vectorstore.similarity_search(question, k=4)

        # Format context
        context = "\n\n".join([doc.page_content for doc in docs])

        # Add chat history to context
        history_text = "\n".join([f"{msg['role']}: {msg['content']}" for msg in self.chat_history[-6:]])  # Last 3 exchanges
        full_context = f"{history_text}\n\nContext:\n{context}" if history_text else context

        # Get role-specific prompt
        role_prompt = ROLE_PROMPTS.get(self.role, ROLE_PROMPTS["professor"])

        # Create prompt with role instruction, history, and context
        template = f"""{role_prompt}

Answer the question based only on the following context and chat history:
{{context}}

Question: {{question}}

Answer:"""
        prompt = ChatPromptTemplate.from_template(template)

        # Run chain
        chain_input = {"context": full_context, "question": question}
        result = (prompt | self.llm | StrOutputParser()).invoke(chain_input)

        # Update chat history
        self.chat_history.append({"role": "user", "content": question})
        self.chat_history.append({"role": "assistant", "content": result})

        return {
            "answer": result,
            "source_documents": docs
        }

    def generate_query_suggestions(self, context_docs: List[Document], chat_history: List[dict]) -> List[str]:
        """基于上下文和聊天历史生成查询建议"""

        # 提取关键概念
        context_text = "\n".join([doc.page_content[:500] for doc in context_docs[:3]])
        history_text = "\n".join([f"{msg['role']}: {msg['content']}" for msg in chat_history[-4:]])

        prompt = f"""基于以下论文内容和对话历史，生成3-5个相关的学术问题建议：

论文内容摘要：
{context_text[:1000]}

对话历史：
{history_text}

请生成具体的问题建议，帮助用户深入理解论文：
1.
2.
3.
4.
5.

只返回问题列表，不要其他内容。"""

        suggestions = (ChatPromptTemplate.from_template("{prompt}") | self.llm | StrOutputParser()).invoke({"prompt": prompt})

        # 解析建议
        lines = [line.strip() for line in suggestions.split('\n') if line.strip() and line[0].isdigit()]
        return [line.split('. ', 1)[1] if '. ' in line else line for line in lines[:5]]

    def generate_code(self, method_description: str) -> str:
        """Generate executable Python code from a method description."""
        sindy_hint = "\n请特别使用 pysindy 库来实现 SINDy 相关算法。\n" if "sindy" in method_description.lower() else ""

        prompt_text = f"""根据以下论文中的方法描述，生成可运行的Python代码：

{method_description}
{sindy_hint}
要求：
1. 代码要完整，包含必要的import
2. 包含数据生成、模型训练、结果可视化
3. 添加详细的注释
4. 直接可以运行（假设已安装所需库）

只返回代码，不要解释。
"""

        prompt = ChatPromptTemplate.from_template("{instruction}")
        result = (prompt | self.llm | StrOutputParser()).invoke({"instruction": prompt_text})
        return result

    def execute_code(self, code: str) -> dict:
        """Safely execute code and return output or error."""

        if docker:
            # Try Docker sandbox execution first
            with tempfile.TemporaryDirectory() as tmpdir:
                script_path = os.path.join(tmpdir, "code.py")
                with open(script_path, "w", encoding="utf-8") as f:
                    f.write(code)

                client = docker.from_env()
                try:
                    container = client.containers.run(
                        "python:3.12",
                        command=f"python /code.py",
                        mem_limit="256m",
                        nano_cpus=int(0.5 * 1e9),
                        network_disabled=True,
                        read_only=True,
                        pids_limit=100,
                        detach=True,
                        auto_remove=True,
                        volumes={tmpdir: {'bind': '/','mode': 'ro'}}
                    )
                    exit_code = container.wait(timeout=20)
                    logs = container.logs(stdout=True, stderr=True, stream=False).decode("utf-8", errors="ignore")
                    if exit_code.get("StatusCode", 1) == 0:
                        return {"success": True, "output": logs}
                    else:
                        return {"success": False, "error": f"Docker execution failed, exit code {exit_code}. Logs:\n{logs}"}
                except Exception as e:
                    # fallback to local execution if docker is unavailable or fails
                    docker_err = f"Docker execution error: {e}. Falling back to local execution."
                finally:
                    try:
                        for c in client.containers.list(all=True, filters={"ancestor": "python:3.12"}):
                            if c.status != "removed":
                                c.remove(force=True)
                    except Exception:
                        pass
        else:
            docker_err = None

        # Fallback: local Python sandboxed exec
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        sys.stdout = StringIO()
        sys.stderr = StringIO()

        safe_builtins = {
            "__import__": __import__,
            "print": print,
            "range": range,
            "len": len,
            "min": min,
            "max": max,
            "sum": sum,
            "list": list,
            "dict": dict,
            "set": set,
            "tuple": tuple,
            "float": float,
            "int": int,
            "str": str,
            "bool": bool,
            "enumerate": enumerate,
            "zip": zip,
        }

        exec_globals = {"__builtins__": safe_builtins}
        exec_locals = {}

        try:
            exec(code, exec_globals, exec_locals)
            output = sys.stdout.getvalue() + sys.stderr.getvalue()
            if docker_err:
                output = f"{docker_err}\n{output}"
            return {"success": True, "output": output}
        except Exception:
            error_msg = traceback.format_exc()
            if docker_err:
                error_msg = f"{docker_err}\n{error_msg}"
            return {"success": False, "error": error_msg}
        finally:
            sys.stdout = old_stdout
            sys.stderr = old_stderr