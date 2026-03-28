import networkx as nx
import matplotlib.pyplot as plt
from typing import List, Dict, Tuple
import re
from langchain_core.documents import Document

class CitationNetwork:
    def __init__(self):
        self.graph = nx.DiGraph()

    def extract_citations_from_text(self, text: str) -> List[str]:
        """从文本中提取引用"""
        # 匹配常见的引用格式
        patterns = [
            r'\[(\d+(?:,\s*\d+)*)\]',  # [1], [1,2,3]
            r'\((\d+(?:,\s*\d+)*)\)',  # (1), (1,2,3)
            r'(\d+(?:,\s*\d+)*)',      # 纯数字
        ]

        citations = []
        for pattern in patterns:
            matches = re.findall(pattern, text)
            citations.extend(matches)

        return list(set(citations))

    def build_network(self, documents: List[Document], paper_title: str = "Main Paper") -> nx.DiGraph:
        """构建引用网络"""
        self.graph.add_node(paper_title, type="main", size=1000)

        for doc in documents:
            if doc.metadata.get("type") == "references":
                # 解析参考文献
                refs = doc.page_content.replace("References: ", "").split("\n")
                for ref in refs[:20]:  # 限制数量
                    if ref.strip():
                        ref_id = f"Ref_{len(self.graph.nodes)}"
                        self.graph.add_node(ref_id, type="reference", title=ref[:100], size=300)
                        self.graph.add_edge(paper_title, ref_id, weight=1)

            # 从正文中提取引用
            citations = self.extract_citations_from_text(doc.page_content)
            for citation in citations[:10]:  # 限制引用数量
                cited_paper = f"Cited_{citation}"
                if cited_paper not in self.graph:
                    self.graph.add_node(cited_paper, type="cited", size=200)
                if not self.graph.has_edge(paper_title, cited_paper):
                    self.graph.add_edge(paper_title, cited_paper, weight=0.5)

        return self.graph

    def visualize_network(self, figsize=(12, 8)):
        """可视化网络"""
        plt.figure(figsize=figsize)

        # 计算节点位置
        pos = nx.spring_layout(self.graph, k=2, iterations=50)

        # 节点颜色和大小
        node_colors = []
        node_sizes = []
        for node in self.graph.nodes():
            node_type = self.graph.nodes[node].get("type", "unknown")
            if node_type == "main":
                node_colors.append("red")
                node_sizes.append(1000)
            elif node_type == "reference":
                node_colors.append("blue")
                node_sizes.append(300)
            else:
                node_colors.append("green")
                node_sizes.append(200)

        # 绘制节点
        nx.draw_networkx_nodes(self.graph, pos, node_color=node_colors,
                              node_size=node_sizes, alpha=0.7)

        # 绘制边
        edges = self.graph.edges()
        weights = [self.graph[u][v].get('weight', 1) for u, v in edges]
        nx.draw_networkx_edges(self.graph, pos, width=[w*2 for w in weights],
                              alpha=0.5, edge_color='gray')

        # 绘制标签（只为主节点和主要引用显示）
        labels = {}
        for node in self.graph.nodes():
            if self.graph.nodes[node].get("type") == "main":
                labels[node] = node
            elif len(self.graph.nodes[node].get("title", "")) > 0:
                labels[node] = self.graph.nodes[node]["title"][:30] + "..."

        nx.draw_networkx_labels(self.graph, pos, labels, font_size=8)

        plt.title("论文引用关系网络", fontsize=16)
        plt.axis('off')
        return plt.gcf()