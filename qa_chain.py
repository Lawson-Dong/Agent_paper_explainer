import sys
import traceback
from io import StringIO

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
            return {"success": True, "output": output}
        except Exception:
            error_msg = traceback.format_exc()
            return {"success": False, "error": error_msg}
        finally:
            sys.stdout = old_stdout
            sys.stderr = old_stderr