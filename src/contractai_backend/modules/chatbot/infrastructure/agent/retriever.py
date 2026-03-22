"""Adapter from LlamaIndex to LangChain retriever interface."""

from typing import Any

from langchain_core.callbacks import AsyncCallbackManagerForRetrieverRun, CallbackManagerForRetrieverRun
from langchain_core.documents import Document as LCDocument
from langchain_core.retrievers import BaseRetriever
from llama_index.core import QueryBundle
from llama_index.core.postprocessor import MetadataReplacementPostProcessor
from llama_index.core.schema import NodeWithScore


class LlamaIndexWindowRetriever(BaseRetriever):
    index: Any
    top_k: int = 5

    def _get_relevant_documents(
        self, query: str, *, _run_manager: CallbackManagerForRetrieverRun | None = None
    ) -> list[LCDocument]:
        raise NotImplementedError("Este retriever está diseñado solo para uso asíncrono (ainvoke).")

    async def _aget_relevant_documents(
        self, query: str, *, _run_manager: AsyncCallbackManagerForRetrieverRun | None = None
    ) -> list[LCDocument]:
        retriever = self.index.as_retriever(similarity_top_k=self.top_k)
        nodes: list[NodeWithScore] = await retriever.aretrieve(query)

        processor = MetadataReplacementPostProcessor(target_metadata_key="window")
        new_nodes = processor.postprocess_nodes(nodes, query_bundle=QueryBundle(query))

        langchain_docs = []
        for node in new_nodes:
            langchain_docs.append(
                LCDocument(
                    page_content=node.text,
                    metadata=node.metadata
                )
            )

        return langchain_docs
