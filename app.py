import streamlit as st
from pdf_loader import load_multiple_pdfs
from vector_store import VectorStoreManager
from qa_chain import QAChain
import tempfile
import os

st.set_page_config(page_title="AI for Physics Paper Q&A", page_icon="📄", layout="wide")

st.title("🤖 AI for Physics Paper Explainer")
st.markdown("Upload PDF papers and have a conversation about their content.")

# Initialize session state
if "vectorstore_manager" not in st.session_state:
    st.session_state.vectorstore_manager = None
if "qa_chain" not in st.session_state:
    st.session_state.qa_chain = None
if "messages" not in st.session_state:
    st.session_state.messages = []
if "pdf_processed" not in st.session_state:
    st.session_state.pdf_processed = False
if "current_role" not in st.session_state:
    st.session_state.current_role = "professor"

# Sidebar for PDF upload
with st.sidebar:
    st.header("📄 Document Upload")

    # File upload
    uploaded_files = st.file_uploader("Upload PDF files", type="pdf", accept_multiple_files=True)

    if uploaded_files:
        if st.button("🔄 Process/Refresh PDFs", type="primary"):
            with st.spinner("Processing PDFs..."):
                # Save uploaded files to temp directory
                temp_dir = tempfile.mkdtemp()
                file_paths = []
                for uploaded_file in uploaded_files:
                    file_path = os.path.join(temp_dir, uploaded_file.name)
                    with open(file_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                    file_paths.append(file_path)

                # Load and split PDFs
                documents = load_multiple_pdfs(file_paths)

                # always rebuild vectorstore for multi-file consistency
                vectorstore_manager = VectorStoreManager()
                vectorstore_manager.create_or_load_vectorstore(documents, reset=True)

                # Create QA chain with current role
                qa_chain = QAChain(vectorstore_manager, st.session_state.current_role)

                # Store in session state
                st.session_state.vectorstore_manager = vectorstore_manager
                st.session_state.qa_chain = qa_chain
                st.session_state.pdf_processed = True
                st.session_state.messages = []

                st.success(f"✅ Processed {len(uploaded_files)} PDF(s) with {len(documents)} chunks.")

    if st.session_state.pdf_processed:
        st.success("📚 Documents ready for Q&A!")

        # Role selector
        st.header("🎭 AI Role")
        role_options = {
            "professor": "👨‍🏫 Professor (学术指导)",
            "reviewer": "👨‍⚖️ Reviewer (审稿人)",
            "student": "👨‍🎓 Student (研究生)"
        }

        selected_role = st.selectbox(
            "Choose AI persona:",
            options=list(role_options.keys()),
            format_func=lambda x: role_options[x],
            index=list(role_options.keys()).index(st.session_state.current_role)
        )

        if selected_role != st.session_state.current_role:
            st.session_state.current_role = selected_role
            if st.session_state.qa_chain:
                st.session_state.qa_chain.set_role(selected_role)
            st.success(f"🎭 Switched to {role_options[selected_role]} role!")

        cols = st.columns(2)
        with cols[0]:
            if st.button("🗑️ Clear Chat History"):
                st.session_state.messages = []
        with cols[1]:
            if st.button("🧹 Clear Documents & Index"):
                # reset all state to allow re-upload
                st.session_state.messages = []
                st.session_state.pdf_processed = False
                st.session_state.qa_chain = None
                st.session_state.vectorstore_manager = None
                # remove persistent data if exists
                from vector_store import VectorStoreManager
                VectorStoreManager().reset_vectorstore()
                st.success("🆕 Documents cleared. Please upload new PDFs.")

# Mode selector
mode = st.sidebar.radio("选择模式", ["问答", "代码生成"], index=0)

if mode == "代码生成":
    st.header("🛠️ 代码生成")
    method_description = st.text_area("根据论文方法描述：", height=220)

    if st.button("生成代码"):
        if not method_description.strip():
            st.warning("请输入方法描述以生成代码。")
        else:
            if st.session_state.qa_chain is None:
                st.warning("请先上传并处理论文，以便引用背景知识（可选）。")
            generated_code = st.session_state.qa_chain.generate_code(method_description) if st.session_state.qa_chain else QAChain(VectorStoreManager(), role=st.session_state.current_role).generate_code(method_description)
            st.session_state.generated_code = generated_code
            st.code(generated_code, language="python")

    if "generated_code" in st.session_state and st.session_state.generated_code:
        st.markdown("### 执行代码（请确保安全）")
        if st.button("执行代码"):
            result = st.session_state.qa_chain.execute_code(st.session_state.generated_code) if st.session_state.qa_chain else QAChain(VectorStoreManager(), role=st.session_state.current_role).execute_code(st.session_state.generated_code)
            if result.get("success"):
                st.success("代码执行成功")
                st.text_area("输出结果：", value=result.get("output", ""), height=160)
            else:
                st.error("代码执行发生错误，请检查代码或环境依赖")
                st.text_area("错误信息：", value=result.get("error", ""), height=160)

else:
    if not st.session_state.pdf_processed:
        st.info("👆 请先在左侧上传并处理PDF文件，然后切换到问答模式。")
    else:
        # Display chat messages
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

                # Show sources if available
                if "sources" in message and message["sources"]:
                    with st.expander("📚 View Sources"):
                        for j, doc in enumerate(message["sources"]):
                            st.markdown(f"**Source {j+1}:** {doc.metadata.get('source', 'Unknown')} (Page {doc.metadata.get('page', 'N/A')})")
                            st.text(doc.page_content[:300] + "..." if len(doc.page_content) > 300 else doc.page_content)

        # Chat input
        if prompt := st.chat_input("Ask a question about the papers..."):
            # Add user message to chat history
            st.session_state.messages.append({"role": "user", "content": prompt})

            # Display user message
            with st.chat_message("user"):
                st.markdown(prompt)

            # Generate response
            with st.chat_message("assistant"):
                with st.spinner("🤔 Thinking..."):
                    result = st.session_state.qa_chain.ask_question(prompt)

                # Display response
                st.markdown(result["answer"])

                # Show sources
                if result["source_documents"]:
                    with st.expander("📚 View Sources"):
                        for j, doc in enumerate(result["source_documents"]):
                            st.markdown(f"**Source {j+1}:** {doc.metadata.get('source', 'Unknown')} (Page {doc.metadata.get('page', 'N/A')})")
                            st.text(doc.page_content[:300] + "..." if len(doc.page_content) > 300 else doc.page_content)

            # Add assistant response to chat history
            st.session_state.messages.append({
                "role": "assistant",
                "content": result["answer"],
                "sources": result["source_documents"]
            })

# Footer
st.markdown("---")
st.markdown("*Powered by LangChain, DeepSeek, and Chroma*")