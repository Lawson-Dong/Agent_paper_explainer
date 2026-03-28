# AI for Physics Paper Explainer

A Streamlit-based Q&A system for physics and AI papers using LangChain, Chroma, and OpenAI.

## Features

- Upload single or multiple PDF papers
- Automatic PDF parsing and chunking optimized for physics content
- Vector embeddings using local models (no API key needed)
- Chroma vector database for storage and retrieval
- **Conversational chat interface** like DeepSeek - continuous Q&A with chat history
- Display source documents for answers with expandable details
- Sidebar for document management and chat controls

## Setup

1. Clone or navigate to the project directory.

2. Install dependencies:
   ```bash
   uv sync
   ```
   or
   ```bash
   pip install -r requirements.txt
   ```

3. Create a `.env` file in the root directory and add your DeepSeek API key:
   ```
   DEEPSEEK_API_KEY=your_deepseek_api_key_here
   ```

4. Run the application:
   ```bash
   streamlit run app.py
   ```

5. Open your browser to the provided URL (usually http://localhost:8501).

## Usage

1. Upload PDF files using the sidebar file uploader.
2. Click "🔄 Process PDFs" to parse and index the documents.
3. Once documents are ready, use the chat input at the bottom to ask questions.
4. Continue the conversation naturally - the chat history is maintained.
5. Click "📚 View Sources" under any response to see relevant document excerpts.
6. Use "🗑️ Clear Chat History" in the sidebar to start a new conversation.

## Project Structure

- `app.py`: Streamlit main interface
- `pdf_loader.py`: PDF loading and chunking logic
- `vector_store.py`: Vector database management
- `qa_chain.py`: Q&A chain building
- `config.py`: API configuration
- `requirements.txt`: Dependencies

## Notes

- The application uses LangChain 0.1+ API, which may show deprecation warnings with Python 3.14+
- Chat functionality uses DeepSeek API - make sure to set a valid DeepSeek API key in the `.env` file
- Embeddings use local FakeEmbeddings for testing (no API key needed, but limited functionality)
- PDFs are processed and stored in a local Chroma database in the `chroma_db_hf` directory
- `qa_chain.py`: Q&A chain building
- `config.py`: API configuration
- `requirements.txt`: Dependencies

## ������־����Ŀ׷�ݣ�

### 2026-03-28 16:00 - ��ʼ������ȶ�����֤
- ���������
  - ȷ�� app.py �﷨�͵��룺py_compile �ɹ���
  - ȷ�� Streamlit + ���⻷�����ã�.venv\\Scripts\\activate �� import streamlit �ɹ���
  - ��� st.experimental_rerun ������⣬��Ϊ��״̬���ã���ǰ�汾�޸�API����
  - DeepSeek API ���ԣ�test_deepseek.py chat �ɹ���embeddings 404��API/Key���⣩��
- ʵ�ֵĹ���
  - �����ʴ� + ���ĵ��ϴ�/�ؽ�����������
  - ��ɫ�л���professor/reviewer/student + QAChain.set_role��
  - ����� UI����ɫѡ��/�����ʷ/����ĵ���
- ����ջ
  - Python 3.14��Streamlit��LangChain��DeepSeek��Chroma��pypdf��FakeEmbeddings��
- δ���
  - DeepSeek Embeddings 404���ⲿ���������⣬��в�̶ȣ��С�
  - execute_code ��safe_builtins���룬��δ����/�������룬��в�̶ȣ��ߡ�

### 2026-03-28 16:10 - �������ɹ���ʵ��
- ���������
  - ����ģʽ�л����ʴ�/�������ɡ�
  - QAChain.generate_code: prompt Ԥ�裬SINDy �ؼ��ִ��� pysindy �Ƽ���
  ## Debug Log (Project Traceback)

### 2026-03-28 - Initial review and stability verification
- Issues resolved
  - Verified app.py syntax and import using py_compile. 
  - Confirmed Streamlit works in .venv and import streamlit succeeds. 
  - Fixed st.experimental_rerun dependency by using state reset logic for this Streamlit version. 
  - DeepSeek API check: chat route works, embeddings route returns 404 (API/Key or service issue).
- Implemented
  - Core QA + multi-document upload and vector index rebuild. 
  - Role switching (professor/reviewer/student) via QAChain.set_role. 
  - Sidebar controls for role select, clear history, clear documents.
- Tech stack
  - Python 3.14, Streamlit, LangChain, DeepSeek, Chroma, pypdf, FakeEmbeddings.
- Open issues
  - DeepSeek embeddings 404 remains (external dependency risk, severity medium).
  - execute_code uses safe_builtins only; no process/container sandbox yet (severity high).

### 2026-03-28 - Code generation feature implementation
- Issues resolved
  - Added mode switch: QA vs code generation. 
  - QAChain.generate_code: fixed prompt with SINDy detection and pysindy recommendation. 
  - QAChain.execute_code: captures stdout/stderr and returns structured success/failure.
- Implemented
  - UI: code input and generated code display. 
  - Execution button with output or error display.
- New tech
  - Python exec + io.StringIO + traceback + safe_builtins sandbox.
- Open issues
  - execute_code has no process isolation (infinite loops/privilege risk, severity high). 
  - No automatic extraction from paper method section yet (functionality gap, severity low).

### 2026-03-28 - Final check and tests
- Issues resolved
  - py_compile passes. 
  - python -c  import app passes. 
  - test_chat.py passes; test_app.py hits NoneType.as_retriever (vectorstore init state issue).
- Completed
  - Role switch, QA, code generation, and execution flows implemented.
- Open issues
  - test_deepseek.py embeddings 404 persists (needs API key/network check, severity medium).
  - Need robust execution isolation (Docker/process recommended).

