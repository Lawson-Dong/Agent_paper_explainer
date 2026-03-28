# AI for Physics Paper Explainer

A comprehensive Streamlit-based Q&A system for physics and AI papers with advanced academic workflow features.

## ✨ New Features (v2.0)

### 🚀 Async PDF Processing
- **Progress Bars**: Real-time processing progress for large PDF files
- **No UI Freezing**: Asynchronous processing prevents interface lockup
- **ETA Display**: Estimated time remaining for processing completion

### 🧠 Smart Query Suggestions
- **Context-Aware**: AI-generated question suggestions based on paper content
- **Conversation History**: Suggestions adapt to your discussion context
- **One-Click Adoption**: Click suggestions to instantly ask questions

### 📊 Academic Citation Networks
- **Citation Visualization**: Interactive network graphs of paper references
- **Reference Analysis**: Automatic extraction and mapping of citations
- **Network Statistics**: Node/edge counts and relationship density metrics

## Features

- Upload single or multiple PDF papers
- **GROBID Integration**: Local Docker-based GROBID server for structured PDF extraction
- Automatic PDF parsing and chunking optimized for physics content
- Vector embeddings using local models (no API key needed)
- Chroma vector database for storage and retrieval
- **Conversational chat interface** like DeepSeek - continuous Q&A with chat history
- Display source documents for answers with expandable details
- Sidebar for document management and chat controls
- **Code Generation**: AI-powered Python code generation from paper methods
- **Role-based AI**: Professor, Reviewer, and Student personas
- **Secure Code Execution**: Docker sandboxed code execution with resource limits
- **arXiv Integration**: Search and discover physics papers
- **Overleaf Integration**: Generate LaTeX documents and open in Overleaf
- **Grammarly Integration**: Text quality checking and plagiarism detection

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

### Basic Q&A Workflow
1. Upload PDF files using the sidebar file uploader.
2. **Optional**: Enable "🔬 Use GROBID" checkbox for structured academic paper processing (requires Docker).
3. Click "🔄 Process PDFs" to parse and index the documents.
4. Once documents are ready, use the chat input at the bottom to ask questions.
5. Continue the conversation naturally - the chat history is maintained.

### New Features Usage

#### Async PDF Processing
- Upload large PDF files without worrying about UI freezing
- Watch real-time progress bars and estimated completion time
- Processing happens in background threads for smooth user experience

#### Smart Query Suggestions
1. After uploading documents, expand the "💡 智能查询建议" section
2. Click "🔄 生成建议" to get AI-generated question suggestions
3. Click any suggestion to instantly populate the chat input
4. Suggestions are based on your conversation history and paper content

#### Academic Citation Networks
1. Switch to "学术网络" mode in the sidebar
2. Click "🔄 构建引用网络" to analyze citation relationships
3. View interactive network visualization
4. See network statistics and reference lists
5. Explore citation connections between papers

### Advanced Features

#### Code Generation Mode
- Switch to "代码生成" mode
- Describe a method from the paper in natural language
- AI generates executable Python code with comments
- **Secure Execution**: Run code in Docker sandbox with resource limits

#### Academic Integrations
- **arXiv Search**: Discover physics papers by keywords and categories
- **LaTeX Generation**: Create academic documents and open in Overleaf
- **Text Checking**: Grammarly-powered quality and plagiarism analysis

#### AI Personas
Choose from three expert personas:
- 👨‍🏫 **Professor**: Academic guidance and research context
- 👨‍⚖️ **Reviewer**: Critical analysis and improvement suggestions
- 👨‍🎓 **Student**: Learning-focused explanations and questions
6. Click "📚 View Sources" under any response to see relevant document excerpts.
7. Use "🗑️ Clear Chat History" in the sidebar to start a new conversation.
8. Switch to "Code Generation" mode to generate Python code from paper methods.
9. Choose different AI roles (Professor/Reviewer/Student) for varied interaction styles.

## Project Structure

- `app.py`: Streamlit main interface with GROBID integration
- `pdf_loader.py`: PDF loading with GROBID and basic text processing
- `grobid_manager.py`: Local GROBID server management via Docker
- `vector_store.py`: Vector database management
- `qa_chain.py`: Q&A chain building with code generation and execution
- `config.py`: API configuration
- `requirements.txt`: Dependencies

## Notes

- The application uses LangChain 0.1+ API, which may show deprecation warnings with Python 3.14+
- Chat functionality uses DeepSeek API - make sure to set a valid DeepSeek API key in the `.env` file
- Embeddings use local FakeEmbeddings for testing (no API key needed, but limited functionality)
- PDFs are processed and stored in a local Chroma database in the `chroma_db_hf` directory
- **GROBID Integration**: Uses Docker to run a local GROBID server for structured PDF processing
- GROBID provides better extraction of titles, authors, abstracts, and section structure from academic papers
- Code execution uses Docker sandboxing with resource limits for security



### 2026-03-28 - GROBID Integration Implementation
- Issues resolved
  - Added grobid-client-python, docker, lxml, requests dependencies.
  - Created grobid_manager.py for local Docker-based GROBID server management.
  - Modified pdf_loader.py with GROBID integration and fallback to basic loading.
  - Updated app.py with GROBID checkbox option in sidebar.
- Implemented
  - Local GROBID server auto-start/stop via Docker container.
  - Structured PDF extraction: titles, authors, abstracts, sections, references.
  - TEI XML parsing for better document chunking.
  - Graceful fallback when GROBID unavailable.
- New tech
  - Docker container management for GROBID server.
  - lxml for TEI XML parsing.
  - grobid-client-python for API integration.
- Open issues
  - GROBID server startup time (~2 minutes), may need user patience.
  - Docker dependency required for GROBID features.
  - TEI parsing may need refinement for complex document structures.
