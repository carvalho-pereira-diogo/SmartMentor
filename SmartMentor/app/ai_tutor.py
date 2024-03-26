# ai_agent.py
import openai
from PyPDF2 import PdfFileReader
from langchain import CharacterTextSplitter
from langchain.embeddings import OpenAIEmbeddings
from langchain.vector_store import FAISS
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationalRetrievalChain
from langchain.chat_models import ChatOpenAI

OPENAI_API_KEY = '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'

# generate response by using the different functions
def generate_response(pdf_document):
    text = get_pdf_text(pdf_document)
    chunks = get_text_chunks(text)
    vectorstore = get_vector_store(chunks)
    conversation_chain = get_conversation_chain(vectorstore)
    return conversation_chain


# get pdf content to text
def get_pdf_text(pdf_document):
    text = ''
    for pdf in pdf_document:
        pdf_reader = PdfFileReader(pdf)
        for page in pdf_reader.pages:
            text += page.extract_text()
    return text

# get text chunks
def get_text_chunks(raw_text):
    text_splitter = CharacterTextSplitter(
        seperator ="\n",
        chunk_size = 1000,
        chunk_overlap = 100,
        length_function = len
    )
    chunks = text_splitter.split_text(raw_text)
    return chunks

#Create vector store
def get_vector_store(text_chunks):
    embeddings = OpenAIEmbeddings()
    vectorstore = FAISS.from_texts(texts=text_chunks, embedding=embeddings)
    return vectorstore

# Create conversation chain
def get_conversation_chain(vectorstore):
    llm = ChatOpenAI()
    memory = ConversationBufferMemory(memory_key='chat_history', return_messages=True)
    conversation_chain = ConversationalRetrievalChain.from_llm(
        llm=llm, 
        retriever=vectorstore.as_retriever(), 
        memory=memory
    )
    return conversation_chain

