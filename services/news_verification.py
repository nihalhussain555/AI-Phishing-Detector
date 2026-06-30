from sentence_transformers import SentenceTransformer, util
import requests
from bs4 import BeautifulSoup
import trafilatura
from urllib.parse import quote_plus
from utils.source_manager import SourceManager

class NewsVerificationService:
    """Module 5: Fact Verification using Semantic Similarity."""
    
    def __init__(self):
        # Load the model only when initialized
        print("Loading SentenceTransformer model...")
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.source_manager = SourceManager()
        
    def search_news(self, query):
        """Searches Google News for relevant articles (Simplified for no paid APIs)."""
        # Note: This is a very basic scraper for demonstration since Paid APIs are not allowed.
        # In a real production scenario, a robust News API is recommended.
        search_url = f"https://news.google.com/search?q={quote_plus(query)}&hl=en-IN&gl=IN&ceid=IN%3Aen"
        headers = {'User-Agent': 'Mozilla/5.0'}
        
        articles = []
        try:
            res = requests.get(search_url, headers=headers, timeout=10)
            soup = BeautifulSoup(res.text, 'html.parser')
            
            for item in soup.find_all('a', class_='JtKRv')[:5]: # Top 5
                link = "https://news.google.com" + item['href'][1:]
                articles.append(link)
        except Exception as e:
            print(f"Error fetching news: {e}")
            
        return articles

    def extract_text(self, url):
        """Extracts article text using trafilatura."""
        downloaded = trafilatura.fetch_url(url)
        if downloaded:
            return trafilatura.extract(downloaded)
        return None

    def verify_claim(self, claim):
        """Verifies a claim against retrieved articles."""
        article_urls = self.search_news(claim)
        
        if not article_urls:
            return {
                "prediction": "Insufficient Evidence",
                "confidence": 0,
                "similarity_score": 0,
                "supporting_sources": [],
                "error": "No articles found to verify the claim."
            }
            
        texts = []
        sources = []
        
        for url in article_urls:
            text = self.extract_text(url)
            if text:
                texts.append(text)
                sources.append(url)
                
        if not texts:
             return {
                "prediction": "Insufficient Evidence",
                "confidence": 0,
                "similarity_score": 0,
                "supporting_sources": [],
                "error": "Could not extract text from articles."
            }
            
        # Generate Embeddings
        claim_embedding = self.model.encode(claim, convert_to_tensor=True)
        article_embeddings = self.model.encode(texts, convert_to_tensor=True)
        
        # Calculate Cosine Similarity
        cosine_scores = util.cos_sim(claim_embedding, article_embeddings)[0]
        
        best_score = float(cosine_scores.max())
        best_idx = int(cosine_scores.argmax())
        
        # Threshold logic
        prediction = "Insufficient Evidence"
        if best_score > 0.8:
            prediction = "True"
        elif best_score > 0.6:
            prediction = "Mostly True"
        elif best_score > 0.4:
            prediction = "Partially True"
        elif best_score > 0.2:
            prediction = "Misleading"
        else:
            prediction = "False"
            
        confidence = round(best_score * 100, 2)
        
        return {
            "prediction": prediction,
            "confidence": confidence,
            "similarity_score": round(best_score, 4),
            "closest_article": sources[best_idx],
            "supporting_sources": sources
        }
