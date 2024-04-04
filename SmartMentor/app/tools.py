import os # Get api key from exa
from exa_py import Exa
from langchain import CharacterTextSplitter
from langchain.embeddings import OpenAIEmbeddings
from langchain.vector_store import FAISS
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationalRetrievalChain
from langchain.agents import tool

class ExaSearchToolset():
    # Code tools
    @tool
    def search(query: str):
        """Search for a webpage based on the query."""
        return ExaSearchToolset._exa().search(f"{query}", use_autopromp=True, num_results=3)
    
    @tool
    def find_similar(url: str):
        """Find similar webpages based on the url."""
        return ExaSearchToolset._exa().find_similar(url, num_results=3)
    
    @tool
    def get_contents(ids: str):
        """Get the contents of a webpage based on the id."""
        return ExaSearchToolset._exa().get_contents(ids)
    
    def tools():
        return[
            ExaSearchToolset.search,
            ExaSearchToolset.find_similar,
            ExaSearchToolset.get_contents
        ]
    
    #Change so it works for me 
    def _exa():
        return Exa(os.environ['EXA_API_KEY'])