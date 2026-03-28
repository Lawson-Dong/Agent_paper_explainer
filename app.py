import streamlit as st
from pdf_loader import load_multiple_pdfs
from vector_store import VectorStoreManager
from qa_chain import QAChain
from arxiv_manager import ArxivManager
from overleaf_manager import OverleafManager
from grammarly_manager import GrammarlyManager
from citation_network import CitationNetwork
from config import GRAMMARLY_CLIENT_ID, GRAMMARLY_CLIENT_SECRET, GRAMMARLY_AVAILABLE
import tempfile
import os
import time
import threading
from queue import Queue

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

# Processing status for async PDF processing
if "processing_status" not in st.session_state:
    st.session_state.processing_status = {"progress": 0, "message": "", "eta": 0, "is_processing": False}

def process_pdf_async(file_paths, use_grobid, progress_queue):
    """异步PDF处理函数"""
    try:
        total_files = len(file_paths)
        processed_docs = []

        for i, path in enumerate(file_paths):
            # 更新进度
            progress = (i / total_files) * 100
            progress_queue.put({"progress": progress, "message": f"处理文件 {i+1}/{total_files}: {os.path.basename(path)}"})

            # 模拟处理时间（实际处理中移除）
            time.sleep(0.5)  # 替换为实际处理

            docs = load_multiple_pdfs([path], use_grobid=use_grobid)
            processed_docs.extend(docs)

            # 估算剩余时间
            elapsed = time.time() - start_time
            if i > 0:
                avg_time_per_file = elapsed / (i + 1)
                remaining_files = total_files - i - 1
                eta = avg_time_per_file * remaining_files
                progress_queue.put({"eta": eta})

        progress_queue.put({"progress": 100, "message": "处理完成", "result": processed_docs})

    except Exception as e:
        progress_queue.put({"error": str(e)})

# Sidebar for PDF upload
with st.sidebar:
    st.header("📄 Document Upload")

    # GROBID option
    use_grobid = st.checkbox("🔬 Use GROBID (Structured PDF Processing)", value=False,
                           help="Use GROBID for better structured extraction of academic papers. Requires Docker.")

    if use_grobid:
        st.info("ℹ️ GROBID will automatically start a local Docker container for PDF processing.")

    # GROBID information link
    st.markdown("[📖 Learn more about GROBID](https://github.com/Lawson-Dong/opensource-academic-site/tree/main/docs/ai/langchain%20AI%20agent%E5%85%A8%E6%A0%88%E5%BC%80%E5%8F%91/%E8%AE%BA%E6%96%87%E5%8A%A9%E6%89%8Bagent%E5%BC%80%E5%8F%91%E6%8C%87%E5%8D%97) - A machine learning library for extracting structured information from academic documents.")

    # File upload
    uploaded_files = st.file_uploader("Upload PDF files", type="pdf", accept_multiple_files=True)

    if uploaded_files:
        if st.button("🔄 Process/Refresh PDFs", type="primary"):
            # 初始化进度状态
            st.session_state.processing_status = {
                "progress": 0, "message": "初始化...", "eta": 0, "is_processing": True
            }

            # 保存文件
            temp_dir = tempfile.mkdtemp()
            file_paths = []
            for uploaded_file in uploaded_files:
                file_path = os.path.join(temp_dir, uploaded_file.name)
                with open(file_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                file_paths.append(file_path)

            # 创建进度队列
            progress_queue = Queue()

            # 启动异步处理线程
            processing_thread = threading.Thread(
                target=process_pdf_async,
                args=(file_paths, use_grobid, progress_queue)
            )
            processing_thread.start()

            # 显示进度条
            progress_bar = st.progress(0)
            status_text = st.empty()
            eta_text = st.empty()

            start_time = time.time()

            while processing_thread.is_alive() or not progress_queue.empty():
                try:
                    status = progress_queue.get(timeout=0.1)

                    if "progress" in status:
                        st.session_state.processing_status["progress"] = status["progress"]
                        progress_bar.progress(int(status["progress"]) // 100)

                    if "message" in status:
                        st.session_state.processing_status["message"] = status["message"]
                        status_text.text(status["message"])

                    if "eta" in status:
                        st.session_state.processing_status["eta"] = status["eta"]
                        if status["eta"] > 0:
                            eta_text.text(f"预计剩余时间: {status['eta']:.1f}秒")

                    if "result" in status:
                        documents = status["result"]
                        # 创建向量存储
                        vectorstore_manager = VectorStoreManager()
                        vectorstore_manager.create_or_load_vectorstore(documents, reset=True)
                        qa_chain = QAChain(vectorstore_manager, st.session_state.current_role)

                        st.session_state.vectorstore_manager = vectorstore_manager
                        st.session_state.qa_chain = qa_chain
                        st.session_state.pdf_processed = True
                        st.session_state.messages = []

                        processing_method = "with GROBID structured extraction" if use_grobid else "with basic text extraction"
                        st.success(f"✅ Processed {len(uploaded_files)} PDF(s) {processing_method} - {len(documents)} chunks created.")
                        break

                    if "error" in status:
                        st.error(f"处理失败: {status['error']}")
                        break

                except:
                    continue

            st.session_state.processing_status["is_processing"] = False

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
mode = st.sidebar.radio("选择模式", ["问答", "代码生成", "论文搜索", "LaTeX生成", "文本检查", "学术网络"], index=0)

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

elif mode == "论文搜索":
    st.header("🔍 arXiv 论文搜索")
    st.markdown("在arXiv上搜索物理论文。感谢arXiv的开放数据接入。")
    
    col1, col2 = st.columns(2)
    with col1:
        search_query = st.text_input("搜索关键词：", placeholder="e.g., quantum computing, neural networks")
    with col2:
        arxiv_category = st.selectbox(
            "物理学分类：",
            ["physics.gen-ph", "physics.app-ph", "physics.cond-mat", "physics.flu-dyn", 
             "physics.optics", "physics.plasm-ph", "physics.ao-ph", "cs.LG"]
        )
    
    max_results = st.slider("最大结果数：", 5, 50, 10)
    
    if st.button("🔎 搜索论文"):
        if not search_query.strip():
            st.warning("请输入搜索关键词")
        else:
            with st.spinner("正在搜索arXiv..."):
                arxiv_manager = ArxivManager()
                papers = arxiv_manager.search_papers(
                    query=search_query,
                    category=arxiv_category,
                    max_results=max_results
                )
                
                if papers:
                    st.success(f"找到 {len(papers)} 篇论文")
                    for idx, paper in enumerate(papers, 1):
                        with st.expander(f"📄 {idx}. {paper['title'][:80]}..."):
                            st.markdown(f"**arXiv ID:** {paper['arxiv_id']}")
                            st.markdown(f"**作者:** {', '.join(paper['authors'][:3])}{'...' if len(paper['authors']) > 3 else ''}")
                            st.markdown(f"**分类:** {paper['categories']}")
                            st.markdown(f"**发布:** {paper['published'][:10]}")
                            st.markdown(f"**摘要:** {paper['summary'][:500]}...")
                            
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.markdown(f"[📖 查看论文](https://{paper['url'].replace('http://', '')})")
                            with col2:
                                st.markdown(f"[📥 下载PDF]({paper['pdf_url']})")
                            with col3:
                                if st.button(f"⬆️ 上传论文 {idx}"):
                                    st.info(f"将论文 '{paper['title'][:50]}' 的链接保存到剪贴板：{paper['pdf_url']}")
                else:
                    st.info(f"未找到与'{search_query}'相关的论文")

elif mode == "LaTeX生成":
    st.header("📝 LaTeX 文档生成")
    st.markdown("使用模板快速生成学术文档并在Overleaf中打开。")
    
    template_type = st.selectbox(
        "选择模板类型：",
        ["学术论文", "研究提案", "Beamer演讲"]
    )
    
    if template_type == "学术论文":
        st.subheader("📚 学术论文模板")
        col1, col2 = st.columns(2)
        with col1:
            paper_title = st.text_input("论文标题：")
        with col2:
            num_authors = st.number_input("作者数量：", min_value=1, max_value=10, value=1)
        
        authors = []
        for i in range(num_authors):
            author = st.text_input(f"作者 {i+1}：", key=f"author_{i}")
            if author:
                authors.append(author)
        
        abstract = st.text_area("摘要：", height=150)
        content = st.text_area("论文内容（可选）：", height=200, placeholder="\\section{content}\n...")
        
        if st.button("🚀 在Overleaf中打开"):
            if not paper_title or not authors or not abstract:
                st.warning("请填写必填字段：标题、作者和摘要")
            else:
                overleaf = OverleafManager()
                latex_doc = overleaf.create_paper_template(
                    title=paper_title,
                    authors=authors,
                    abstract=abstract,
                    content=content
                )
                
                link = overleaf.generate_base64_link(latex_doc)
                st.markdown(f"[✨ 在Overleaf中打开](https://www.overleaf.com/docs?snip_uri=data:application/x-tex;base64,{link.split('base64,')[1]})")
                
                with st.expander("📄 查看LaTeX源代码"):
                    st.code(latex_doc, language="latex")
    
    elif template_type == "研究提案":
        st.subheader("🎯 研究提案模板")
        title = st.text_input("研究标题：")
        researcher = st.text_input("研究人员：")
        background = st.text_area("背景与意义：", height=150)
        objectives = st.text_area("研究目标：", height=150)
        methodology = st.text_area("研究方法：", height=150)
        expected_outcomes = st.text_area("预期成果：", height=150)
        
        if st.button("🚀 在Overleaf中打开"):
            if not all([title, researcher, background, objectives, methodology, expected_outcomes]):
                st.warning("请填写所有必填字段")
            else:
                overleaf = OverleafManager()
                latex_doc = overleaf.create_research_proposal_template(
                    title=title,
                    researcher=researcher,
                    background=background,
                    objectives=objectives,
                    methodology=methodology,
                    expected_outcomes=expected_outcomes
                )
                
                link = overleaf.generate_base64_link(latex_doc)
                st.markdown(f"[✨ 在Overleaf中打开](https://www.overleaf.com/docs?snip_uri=data:application/x-tex;base64,{link.split('base64,')[1]})")
                
                with st.expander("📄 查看LaTeX源代码"):
                    st.code(latex_doc, language="latex")
    
    elif template_type == "Beamer演讲":
        st.subheader("🎤 Beamer演讲模板")
        title = st.text_input("演讲标题：")
        author = st.text_input("演讲者：")
        num_slides = st.number_input("幻灯片数量：", min_value=1, max_value=20, value=3)
        
        slides = []
        for i in range(num_slides):
            st.markdown(f"**幻灯片 {i+1}**")
            slide_title = st.text_input(f"标题 {i+1}：", key=f"slide_title_{i}")
            slide_content = st.text_area(f"内容 {i+1}：", height=100, key=f"slide_content_{i}")
            if slide_title and slide_content:
                slides.append((slide_title, slide_content))
        
        if st.button("🚀 在Overleaf中打开"):
            if not title or not author or not slides:
                st.warning("请填写必填字段")
            else:
                overleaf = OverleafManager()
                latex_doc = overleaf.create_presentation_template(
                    title=title,
                    author=author,
                    content_slides=slides
                )
                
                link = overleaf.generate_base64_link(latex_doc)
                st.markdown(f"[✨ 在Overleaf中打开](https://www.overleaf.com/docs?snip_uri=data:application/x-tex;base64,{link.split('base64,')[1]})")
                
                with st.expander("📄 查看LaTeX源代码"):
                    st.code(latex_doc, language="latex")

elif mode == "文本检查":
    st.header("✍️ 学术文本检查")
    if not GRAMMARLY_AVAILABLE:
        st.warning("⚠️ Grammarly API未配置。请在.env文件中添加GRAMMARLY_CLIENT_ID和GRAMMARLY_CLIENT_SECRET。")
        st.info("获取凭证: https://developer.grammarly.com/")
    else:
        st.markdown("使用Grammarly API检查文本质量和抄袭情况。")
        
        text_input = st.text_area("输入要检查的文本：", height=300, placeholder="粘贴你的论文段落或摘要...")
        
        col1, col2 = st.columns(2)
        with col1:
            check_quality = st.checkbox("✅ 检查写作质量", value=True)
        with col2:
            check_plagiarism = st.checkbox("🔍 检查抄袭", value=False)
        
        if st.button("🔎 检查文本"):
            if not text_input.strip():
                st.warning("请输入要检查的文本")
            else:
                grammarly = GrammarlyManager(GRAMMARLY_CLIENT_ID, GRAMMARLY_CLIENT_SECRET)
                
                if check_quality:
                    with st.spinner("正在检查写作质量..."):
                        score_result = grammarly.get_writing_score(text_input)
                        
                        if score_result:
                            st.subheader("📊 写作质量评分")
                            st.metric("综合评分", f"{score_result.get('overall_score', 0)}/100")
                            
                            if score_result.get('scores'):
                                cols = st.columns(len(score_result['scores']))
                                for i, (metric, value) in enumerate(score_result['scores'].items()):
                                    with cols[i % len(cols)]:
                                        st.metric(metric, f"{value}/100")
                            
                            if score_result.get('feedback'):
                                st.subheader("💡 反馈建议")
                                for feedback in score_result['feedback'][:5]:
                                    st.info(feedback)
                        else:
                            st.error("无法获取评分，请检查API配置")
                
                if check_plagiarism:
                    with st.spinner("正在检查抄袭..."):
                        plagiarism_result = grammarly.check_plagiarism(text_input)
                        
                        if plagiarism_result:
                            st.subheader("🔍 抄袭检测结果")
                            st.metric("抄袭指数", f"{plagiarism_result.get('plagiarism_score', 0)}%")
                            
                            if plagiarism_result.get('matches'):
                                st.warning(f"⚠️ 发现 {len(plagiarism_result['matches'])} 处相似内容")
                                for match in plagiarism_result['matches'][:3]:
                                    st.write(f"- {match}")
                        else:
                            st.error("无法检查抄袭，请检查API配置")

elif mode == "学术网络":
    st.header("📊 学术引用网络")
    st.markdown("可视化论文的引用关系和学术网络。")

    if not st.session_state.pdf_processed:
        st.warning("请先上传并处理PDF文件以构建引用网络。")
    else:
        if st.button("🔄 构建引用网络"):
            with st.spinner("分析引用关系..."):
                from citation_network import CitationNetwork

                # 获取所有文档 - 这里需要修改以获取所有文档
                # 由于向量存储的限制，我们使用相似性搜索获取相关文档
                all_docs = []
                try:
                    # 尝试获取向量存储中的所有文档
                    retriever = st.session_state.vectorstore_manager.vectorstore.as_retriever(search_kwargs={"k": 100})
                    # 这里简化处理，获取一些示例文档
                    sample_docs = st.session_state.qa_chain.vectorstore_manager.similarity_search("physics", k=50)
                    all_docs = sample_docs
                except:
                    st.warning("无法获取完整文档列表，使用当前可用文档")
                    all_docs = []

                network = CitationNetwork()
                paper_title = "当前论文"  # 可以从文档中提取

                graph = network.build_network(all_docs, paper_title)

                # 显示网络统计
                st.subheader("📈 网络统计")
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("节点数量", len(graph.nodes))
                with col2:
                    st.metric("引用数量", len(graph.edges))
                with col3:
                    st.metric("网络密度", ".3f")

                # 可视化
                fig = network.visualize_network()
                st.pyplot(fig)

                # 显示引用列表
                st.subheader("📚 引用列表")
                references = [node for node in graph.nodes() if graph.nodes[node].get("type") == "reference"]
                for ref in references[:10]:
                    st.write(f"• {graph.nodes[ref].get('title', ref)}")

else:  # 问答模式
    if not st.session_state.pdf_processed:
        st.info("👆 请先在左侧上传并处理PDF文件，然后切换到问答模式。")
    else:
        # 智能建议区域
        with st.expander("💡 智能查询建议", expanded=False):
            if st.button("🔄 生成建议"):
                with st.spinner("生成建议中..."):
                    # 获取相关文档作为上下文
                    recent_docs = st.session_state.qa_chain.vectorstore_manager.similarity_search(
                        st.session_state.messages[-1]["content"] if st.session_state.messages else "physics paper",
                        k=3
                    )
                    suggestions = st.session_state.qa_chain.generate_query_suggestions(
                        recent_docs, st.session_state.messages
                    )

                    for i, suggestion in enumerate(suggestions, 1):
                        if st.button(f"💭 {suggestion}", key=f"suggestion_{i}"):
                            st.session_state.pending_question = suggestion

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
        if "pending_question" in st.session_state:
            prompt = st.session_state.pending_question
            del st.session_state.pending_question
        else:
            prompt = st.chat_input("Ask a question about the papers...")

        if prompt:
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
st.markdown("*Powered by LangChain, DeepSeek, Chroma, arXiv, Overleaf, and Grammarly*")