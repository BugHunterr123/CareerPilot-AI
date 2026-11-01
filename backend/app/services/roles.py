"""
Entry-level role definitions used for recommendations and gap analysis.

weight: 3 = core (you are expected to show it), 2 = important, 1 = nice to have.
These are general expectations for Indian campus / fresher roles, written by us;
company-specific requirements come from the seeded company data instead.
"""

ROLES: dict[str, dict] = {
    "software_developer": {
        "title": "Software Developer",
        "summary": "Builds and maintains application features. The default campus role at most service companies.",
        "skills": {"Data Structures": 3, "Algorithms": 3, "OOP": 3, "SQL": 2, "DBMS": 2, "Git": 2,
                   "Operating Systems": 2, "Computer Networks": 1, "Python": 2, "Java": 2, "Testing": 1, "Agile": 1},
        "any_of": [["Python", "Java", "C++", "C#", "JavaScript"]],
        "interests": ["software", "development", "coding", "programming"],
        "projects": ["A CRUD web app with login and a database, deployed online",
                     "A command-line tool with unit tests and a clean README"],
    },
    "backend_developer": {
        "title": "Backend Developer",
        "summary": "Designs APIs, databases and server logic.",
        "skills": {"REST APIs": 3, "SQL": 3, "Python": 2, "Java": 2, "DBMS": 2, "Authentication": 2, "Git": 2,
                   "Data Structures": 2, "Docker": 1, "Testing": 2, "Linux": 1, "System Design": 1, "Redis": 1},
        "any_of": [["FastAPI", "Flask", "Django", "Spring Boot", "Node.js"]],
        "interests": ["backend", "api", "server", "database"],
        "projects": ["A REST API with JWT login, pagination and tests, documented with OpenAPI",
                     "Add caching and background jobs to an existing API"],
    },
    "full_stack_developer": {
        "title": "Full-Stack Developer",
        "summary": "Works on both the user interface and the server.",
        "skills": {"HTML": 2, "CSS": 2, "JavaScript": 3, "React": 2, "REST APIs": 3, "SQL": 2, "Git": 2,
                   "Authentication": 1, "Data Structures": 2, "Docker": 1, "TypeScript": 1},
        "any_of": [["FastAPI", "Flask", "Django", "Node.js", "Spring Boot"]],
        "interests": ["full stack", "web", "frontend", "ui"],
        "projects": ["A full-stack app with a React frontend, an API and a database, deployed",
                     "Rebuild a college utility (attendance, notes) as a responsive web app"],
    },
    "data_analyst": {
        "title": "Data Analyst",
        "summary": "Turns data into answers with SQL, spreadsheets and dashboards.",
        "skills": {"SQL": 3, "Excel": 3, "Statistics": 2, "Data Visualization": 2, "Pandas": 2, "Python": 2,
                   "Power BI": 1, "Tableau": 1, "EDA": 2, "Communication": 2},
        "any_of": [],
        "interests": ["data", "analytics", "analysis", "business", "dashboard"],
        "projects": ["A sales or placement-data dashboard in Power BI/Tableau with 5 clear insights",
                     "An SQL case study (joins, window functions) on a public dataset"],
    },
    "data_scientist": {
        "title": "Data Scientist",
        "summary": "Builds models and experiments to answer business questions.",
        "skills": {"Python": 3, "Statistics": 3, "Machine Learning": 3, "Pandas": 2, "SQL": 2, "scikit-learn": 2,
                   "Model Evaluation": 2, "Feature Engineering": 2, "Data Visualization": 1, "EDA": 2},
        "any_of": [],
        "interests": ["data science", "machine learning", "statistics", "ml"],
        "projects": ["An end-to-end ML project with a baseline, error analysis and a short write-up",
                     "A Kaggle-style notebook with clear EDA and model comparison"],
    },
    "ml_engineer": {
        "title": "Machine Learning Engineer",
        "summary": "Trains models and ships them into real products.",
        "skills": {"Python": 3, "Machine Learning": 3, "Deep Learning": 2, "scikit-learn": 2, "Model Evaluation": 2,
                   "REST APIs": 2, "Docker": 2, "Git": 2, "Data Structures": 2, "SQL": 1, "Linux": 1},
        "any_of": [["TensorFlow", "PyTorch"]],
        "interests": ["machine learning", "ml", "deep learning", "mlops"],
        "projects": ["Serve a trained model behind a FastAPI endpoint in Docker",
                     "Track experiments and compare 3 models with proper validation"],
    },
    "ai_engineer": {
        "title": "AI Engineer",
        "summary": "Builds features on top of LLMs and other AI models.",
        "skills": {"Python": 3, "LLMs": 3, "REST APIs": 2, "NLP": 2, "Machine Learning": 2, "Git": 2,
                   "SQL": 1, "Docker": 1, "Testing": 1, "Deep Learning": 1},
        "any_of": [["FastAPI", "Flask", "Django", "Node.js"]],
        "interests": ["ai", "llm", "genai", "generative", "nlp"],
        "projects": ["A RAG question-answering app over your college notes with citations",
                     "An LLM feature with structured (JSON) outputs and an evaluation set"],
    },
    "data_engineer": {
        "title": "Data Engineer",
        "summary": "Builds the pipelines and databases that analysts and models use.",
        "skills": {"SQL": 3, "Python": 3, "ETL": 3, "Data Modelling": 2, "Data Warehousing": 2, "Apache Spark": 2,
                   "DBMS": 2, "Linux": 1, "Pandas": 1, "Airflow": 1, "Git": 1, "Data Structures": 1},
        "any_of": [["AWS", "Azure", "GCP"]],
        "interests": ["data engineering", "pipeline", "etl", "big data"],
        "projects": ["An ETL pipeline that loads a public API into PostgreSQL daily",
                     "A small data warehouse with star schema and documented queries"],
    },
    "bi_analyst": {
        "title": "Business Intelligence Analyst",
        "summary": "Builds reports and dashboards for business teams.",
        "skills": {"SQL": 3, "Power BI": 3, "Excel": 3, "Tableau": 2, "Data Visualization": 2,
                   "Statistics": 1, "Communication": 2, "DBMS": 1},
        "any_of": [],
        "interests": ["business intelligence", "bi", "reporting", "dashboard"],
        "projects": ["A Power BI report with DAX measures and a one-page summary for managers"],
    },
    "qa_automation": {
        "title": "QA Automation Engineer",
        "summary": "Writes automated tests so software ships without regressions.",
        "skills": {"Testing": 3, "Selenium": 3, "API Testing": 2, "Python": 2, "Java": 2, "SQL": 2, "Git": 2,
                   "Agile": 2, "JavaScript": 1, "CI/CD": 1, "OOP": 2},
        "any_of": [],
        "interests": ["testing", "qa", "quality", "automation"],
        "projects": ["A Selenium/Playwright test suite for a public demo site, run in GitHub Actions"],
    },
    "tech_support": {
        "title": "Technical Support Engineer",
        "summary": "Helps users solve technical problems; strong basics and communication matter most.",
        "skills": {"Computer Networks": 3, "Operating Systems": 3, "Communication": 3, "Troubleshooting": 3,
                   "Linux": 2, "SQL": 1, "Cyber Security": 1, "Teamwork": 1},
        "any_of": [],
        "interests": ["support", "networking", "it", "customer"],
        "projects": ["A home-lab write-up: set up Linux, configure networking, troubleshoot and document it"],
    },
}

WEIGHT_WORD = {3: "core", 2: "important", 1: "nice to have"}


def role_title(key: str) -> str:
    return ROLES.get(key, {}).get("title", key.replace("_", " ").title())
