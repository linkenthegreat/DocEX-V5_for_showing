"""LLM service using existing DocEX Qdrant infrastructure"""
import sys
from pathlib import Path
import json
import time
import requests

# Add project root to path to access existing modules
backend_dir = Path(__file__).parent.parent
demo_dir = backend_dir.parent
talk_to_graph_dir = demo_dir.parent
app_dir = talk_to_graph_dir.parent
project_root = app_dir.parent
sys.path.insert(0, str(project_root))

# Import existing DocEX modules with correct class names
from app.database_modules.vector_db_manager import DocEXVectorManager
from services.jsonld_embedder import JSONLDStakeholderEmbedder

class LLMService:
    """Service for LLM-based vector search queries using existing Qdrant infrastructure"""
    
    def __init__(self):
        # Configuration
        self.jsonld_dir = project_root / 'database' / 'jsonld'
        self.llm_base_url = 'http://localhost:11434'
        self.llm_model = 'llama3.1:8b-instruct-q8_0'
        
        self.vector_manager = None
        self.embedder = None
        self._initialize()
    
    def _initialize(self):
        """Initialize using existing DocEX infrastructure"""
        print("🔧 Initializing with existing DocEX Qdrant infrastructure...")
        
        try:
            # Use existing vector DB manager
            self.vector_manager = DocEXVectorManager()
            print("✅ Vector DB manager initialized")
            
            # Use custom JSON-LD embedder for stakeholders
            self.embedder = JSONLDStakeholderEmbedder(vector_manager=self.vector_manager)
            print("✅ JSON-LD stakeholder embedder initialized")
            
        except Exception as e:
            print(f"❌ Error initializing: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    def embed_all_jsonld(self) -> dict:
        """Embed all stakeholders from JSON-LD files"""
        print(f"📚 Embedding stakeholders from JSON-LD files...")
        
        try:
            result = self.embedder.embed_all_stakeholders()
            return result
            
        except Exception as e:
            print(f"❌ Error during embedding: {e}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'error': str(e)
            }
    
    def query_with_vector_search(self, question: str, n_results: int = 10) -> dict:
        """Query using vector search in stakeholder collection and LLM"""
        start_time = time.time()
        
        try:
            # Generate embedding for the question
            question_embedding = self.vector_manager.embed_text(question)
            
            # Search in stakeholder_data collection
            search_results = self.vector_manager.qdrant_client.search(
                collection_name='stakeholder_data',
                query_vector=question_embedding,
                limit=n_results
            )
            
            print(f"🔍 Found {len(search_results)} stakeholder results")
            
            # Format results
            context_parts = []
            sources = []
            
            for result in search_results:
                payload = result.payload
                
                # Get the full text
                text = payload.get('text', '')
                
                if text:
                    context_parts.append(text)
                    
                    sources.append({
                        'type': 'stakeholder',
                        'doc_title': payload.get('doc_title', 'Unknown'),
                        'name': payload.get('name', 'Unknown'),
                        'role': payload.get('role', 'N/A'),
                        'relevance': f"{result.score * 100:.0f}%",
                        'snippet': text[:200] + '...' if len(text) > 200 else text
                    })
            
            context = "\n\n".join(context_parts)
            print(f"📊 Total context length: {len(context)} characters from {len(context_parts)} sources")
            
            # If we have context, generate answer with LLM
            if context and context.strip():
                answer = self._generate_answer_with_llm(question, context)
            else:
                answer = "❌ No stakeholder information found in the vector database.\n\n💡 Click the 'Embed Documents' button to index the stakeholder data first."
            
            execution_time = time.time() - start_time
            
            return {
                'answer': answer,
                'sources': sources,
                'context_used': len(context_parts),
                'execution_time': execution_time
            }
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            
            # Check if collection doesn't exist
            if 'not found' in str(e).lower() or 'does not exist' in str(e).lower():
                return {
                    'answer': f"❌ The stakeholder collection doesn't exist yet.\n\n💡 Click 'Embed Documents' to create it.",
                    'sources': [],
                    'context_used': 0,
                    'execution_time': time.time() - start_time
                }
            
            return {
                'answer': f"Error performing vector search: {str(e)}",
                'sources': [],
                'context_used': 0,
                'execution_time': time.time() - start_time
            }
    
    def _generate_answer_with_llm(self, question: str, context: str) -> str:
        """Generate answer using LLM with context"""
        if not context or context.strip() == "":
            return "No relevant information found in the knowledge graph to answer your question."
        
        system_prompt = """You are a knowledge graph assistant for the DocEX system.
Answer questions about stakeholders based ONLY on the provided context from extracted documents.

Guidelines:
- Be concise and accurate
- List stakeholders with their roles and organizations
- Use bullet points for multiple stakeholders
- If asked about specific roles, filter to show only matching stakeholders
- Maintain professional tone"""

        user_prompt = f"""Context from knowledge graph (stakeholder data):

{context}

Question: {question}

Please provide a clear, accurate answer based only on the stakeholder information above."""

        try:
            # Check if Ollama is running
            health_response = requests.get(f"{self.llm_base_url}/api/tags", timeout=2)
            if health_response.status_code != 200:
                return f"⚠️ Cannot connect to Ollama server. Please ensure Ollama is running on {self.llm_base_url}"
            
            print(f"🤖 Sending {len(context)} characters to LLM...")
            
            # Make the generate request
            response = requests.post(
                f"{self.llm_base_url}/api/generate",
                json={
                    "model": self.llm_model,
                    "prompt": f"{system_prompt}\n\n{user_prompt}",
                    "stream": False,
                    "options": {
                        "temperature": 0.3,
                        "num_predict": 500
                    }
                },
                timeout=500
            )
            
            if response.status_code == 200:
                result = response.json()
                answer = result.get('response', 'No response from LLM')
                print(f"✅ LLM generated {len(answer)} character response")
                return answer
            elif response.status_code == 404:
                return f"⚠️ Model '{self.llm_model}' not found. Please pull it with: ollama pull {self.llm_model}"
            else:
                return f"Error generating answer (HTTP {response.status_code}): {response.text}"
                
        except requests.exceptions.Timeout:
            return "⏱️ LLM request timed out. The model might be loading. Please try again."
        except requests.exceptions.ConnectionError:
            return f"⚠️ Cannot connect to Ollama server at {self.llm_base_url}. Please ensure Ollama is running:\n\nRun: ollama serve"
        except Exception as e:
            return f"Error connecting to LLM: {str(e)}"
    
    def get_stats(self) -> dict:
        """Get vector database statistics"""
        try:
            # Get collection info from Qdrant
            collections = self.vector_manager.qdrant_client.get_collections()
            
            collections_info = []
            total_vectors = 0
            
            for collection in collections.collections:
                try:
                    collection_info = self.vector_manager.qdrant_client.get_collection(collection.name)
                    
                    # Try different ways to get vectors count
                    vectors_count = 0
                    if hasattr(collection_info, 'vectors_count') and collection_info.vectors_count is not None:
                        vectors_count = collection_info.vectors_count
                    elif hasattr(collection_info, 'points_count'):
                        vectors_count = collection_info.points_count
                    else:
                        # Try to count via scroll
                        try:
                            scroll_result = self.vector_manager.qdrant_client.scroll(
                                collection_name=collection.name,
                                limit=1,
                                with_payload=False,
                                with_vectors=False
                            )
                            # This doesn't give us count, but at least we know if empty
                            vectors_count = 0 if not scroll_result[0] else "unknown"
                        except:
                            vectors_count = "unknown"
                    
                    collections_info.append({
                        'name': collection.name,
                        'vectors': vectors_count
                    })
                    
                    if isinstance(vectors_count, int):
                        total_vectors += vectors_count
                        
                except Exception as e:
                    print(f"⚠️  Error getting info for collection {collection.name}: {e}")
                    collections_info.append({
                        'name': collection.name,
                        'vectors': 'error'
                    })
            
            return {
                'total_items': total_vectors if total_vectors > 0 else 0,
                'collections': collections_info,
                'status': 'active',
                'qdrant_url': self.vector_manager.qdrant_url
            }
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return {
                'total_items': 0,
                'collections': [],
                'status': 'error',
                'error': str(e)
            }