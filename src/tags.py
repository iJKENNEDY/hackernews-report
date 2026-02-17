"""Tag system for categorizing posts by topic."""

import re
from typing import List, Set


class TagSystem:
    """
    System for automatically tagging posts based on keywords in titles.
    
    Tags help organize posts by technical topics like AI, programming languages,
    science, etc.
    """
    
    # Define tag categories with their keywords
    TAG_KEYWORDS = {
        # AI & Machine Learning - Priority
        "OpenAI": ["openai", "chatgpt", "gpt", "dall-e", "sora"],
        "Claude": ["claude", "anthropic"],
        "Google AI": ["gemini", "deepmind", "bard"],
        "xAI": ["xai", "grok"],
        "Mistral": ["mistral"],
        "LLMs": ["llm", "large language model", "foundation model"],
        "GenAI": ["genai", "generative ai"],
        "Agents": ["agent", "agents", "autonomous agents"],
        "RAG": ["rag", "retrieval augmented generation"],
        "NLP": ["nlp", "natural language processing"],

        # General AI (for catch-all)
        "AI": [
            "artificial intelligence", "machine learning", "ml", "deep learning",
            "neural network", "copilot", "transformer", "diffusion",
            "stable diffusion", "midjourney", "llama"
        ],
        
        # Programming Languages
        "Python": ["python", "django", "flask", "fastapi", "pytorch", "tensorflow"],
        "JavaScript": ["javascript", "js", "typescript", "ts", "node", "nodejs", "react", "vue", "angular", "next.js", "svelte"],
        "Rust": ["rust", "cargo", "rustc"],
        "Go": ["golang", "go "],
        "C/C++": ["c++", "cpp", " c ", "clang", "gcc"],
        "Java": ["java", "jvm", "kotlin", "spring"],
        
        # Web & Frontend
        "Web Dev": ["web", "frontend", "backend", "fullstack", "html", "css", "browser", "chrome", "firefox", "safari"],
        
        # Cloud & Infrastructure
        "Cloud": ["aws", "azure", "gcp", "google cloud", "cloud", "kubernetes", "k8s", "docker", "container"],
        "DevOps": ["devops", "ci/cd", "jenkins", "github actions", "gitlab"],
        
        # Databases
        "Database": ["database", "sql", "postgresql", "postgres", "mysql", "mongodb", "redis", "elasticsearch"],
        
        # Science & Research
        "Science": ["science", "research", "study", "paper", "arxiv", "nature", "physics", "chemistry", "biology"],
        "Space": ["space", "nasa", "spacex", "rocket", "satellite", "mars", "moon", "astronomy"],
        "Climate": ["climate", "global warming", "carbon", "renewable", "solar", "wind energy"],
        
        # Security & Privacy
        "Security": ["security", "vulnerability", "exploit", "hack", "breach", "encryption", "crypto", "password"],
        "Privacy": ["privacy", "gdpr", "tracking", "surveillance", "data collection"],
        
        # Blockchain & Crypto
        "Blockchain": ["blockchain", "bitcoin", "ethereum", "crypto", "cryptocurrency", "web3", "nft", "defi"],
        
        # Hardware
        "Hardware": ["hardware", "chip", "processor", "cpu", "gpu", "nvidia", "amd", "intel", "arm", "risc-v"],
        
        # Mobile
        "Mobile": ["mobile", "ios", "android", "iphone", "app store", "play store", "swift"],
        
        # Startups & Business
        "Startup": ["startup", "founder", "vc", "venture capital", "funding", "series a", "ipo"],
        "Business": ["business", "company", "ceo", "revenue", "profit", "market"],
        
        # Open Source
        "Open Source": ["open source", "opensource", "github", "gitlab", "license", "mit", "apache", "gpl"],
        
        # Operating Systems
        "Linux": ["linux", "ubuntu", "debian", "arch", "fedora", "kernel"],
        "macOS": ["macos", "mac os", "apple", "m1", "m2", "m3"],
        "Windows": ["windows", "microsoft", "windows 11"],
        
        # Tools & Productivity
        "Tools": ["tool", "cli", "terminal", "vim", "emacs", "vscode", "ide"],
        
        # Gaming
        "Gaming": ["game", "gaming", "unity", "unreal", "steam", "nintendo", "playstation", "xbox"],
        
        # Other Tech Topics
        "API": ["api", "rest", "graphql", "grpc"],
        "Performance": ["performance", "optimization", "speed", "benchmark", "latency"],
        "Testing": ["test", "testing", "qa", "unit test", "integration test"],
    }

    # Priority Tags for Highlighting
    PRIORITY_TAGS = {
        "OpenAI", "Claude", "Google AI", "xAI", "Mistral", 
        "LLMs", "GenAI", "Agents", "RAG", "NLP"
    }
    
    @staticmethod
    def extract_tags(title: str, max_tags: int = 5) -> List[str]:
        """
        Extract relevant tags from a post title based on keywords.
        
        Args:
            title: The post title to analyze
            max_tags: Maximum number of tags to return (default: 5)
            
        Returns:
            List of tag names that match keywords in the title
        """
        if not title:
            return []
        
        # Convert title to lowercase for case-insensitive matching
        title_lower = title.lower()
        
        # Find matching tags
        matched_tags = []
        
        for tag_name, keywords in TagSystem.TAG_KEYWORDS.items():
            for keyword in keywords:
                # Use word boundaries for better matching
                # This prevents "go" from matching "google" etc.
                pattern = r'\b' + re.escape(keyword) + r'\b'
                if re.search(pattern, title_lower):
                    matched_tags.append(tag_name)
                    break  # Only add tag once even if multiple keywords match
        
        # Return up to max_tags
        return matched_tags[:max_tags]
    
    @staticmethod
    def get_all_tags() -> List[str]:
        """
        Get a list of all available tags.
        
        Returns:
            Sorted list of all tag names
        """
        return sorted(TagSystem.TAG_KEYWORDS.keys())
    
    @staticmethod
    def get_tag_keywords(tag_name: str) -> List[str]:
        """
        Get the keywords associated with a specific tag.
        
        Args:
            tag_name: Name of the tag
            
        Returns:
            List of keywords for the tag, or empty list if tag doesn't exist
        """
        return TagSystem.TAG_KEYWORDS.get(tag_name, [])
