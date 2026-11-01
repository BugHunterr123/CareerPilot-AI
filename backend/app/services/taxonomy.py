"""
The skill dictionary used by the rule-based (demo mode) extractor.

Each entry: canonical name -> (category, [regex patterns]).
Patterns are matched case-insensitively on word boundaries.
Add a skill here and the whole app (extraction, gaps, roadmap) picks it up.
"""
import re

CATEGORIES = [
    "Programming", "Data Structures and Algorithms", "SQL and Databases", "Data Analysis",
    "Data Engineering", "Machine Learning", "Artificial Intelligence", "Web Development", "Backend Development",
    "Cloud and Deployment", "Software Engineering", "CS Fundamentals", "Aptitude", "Communication and Behavioural",
]

SKILLS: dict[str, tuple[str, list[str]]] = {
    # Programming
    "Python": ("Programming", [r"python"]),
    "Java": ("Programming", [r"java(?!\s*script)"]),
    "C++": ("Programming", [r"c\+\+", r"cpp"]),
    "C": ("Programming", [r"c programming", r"ansi c"]),  # bare "C" is matched only in the skills list
    "JavaScript": ("Programming", [r"javascript", r"\bjs\b", r"es6"]),
    "TypeScript": ("Programming", [r"typescript"]),
    "C#": ("Programming", [r"c#", r"\.net"]),
    "Go": ("Programming", [r"golang"]),
    "OOP": ("Programming", [r"\boops?\b", r"object[- ]oriented"]),
    # DSA
    "Data Structures": ("Data Structures and Algorithms", [r"data structures?", r"\bdsa\b", r"arrays?", r"linked lists?", r"hashing", r"hash ?maps?", r"binary trees?", r"stacks? and queues?"]),
    "Algorithms": ("Data Structures and Algorithms", [r"algorithms?", r"dynamic programming", r"leetcode", r"competitive programming"]),
    # Databases
    "SQL": ("SQL and Databases", [r"\bsql\b", r"joins?\b"]),
    "MySQL": ("SQL and Databases", [r"mysql"]),
    "PostgreSQL": ("SQL and Databases", [r"postgres(?:ql)?"]),
    "MongoDB": ("SQL and Databases", [r"mongo(?:db)?"]),
    "SQLite": ("SQL and Databases", [r"sqlite"]),
    "DBMS": ("SQL and Databases", [r"\bdbms\b", r"normali[sz]ation", r"database management"]),
    "Redis": ("SQL and Databases", [r"redis"]),
    # Data engineering
    "ETL": ("Data Engineering", [r"\betl\b", r"\belt\b", r"data pipelines?", r"extract,? transform"]),
    "Apache Spark": ("Data Engineering", [r"apache spark", r"pyspark", r"\bspark\b", r"databricks"]),
    "Data Modelling": ("Data Engineering", [r"data model(?:l)?ing", r"star schema", r"snowflake schema", r"dimensional model(?:l)?ing"]),
    "Data Warehousing": ("Data Engineering", [r"data ?warehous\w*", r"bigquery", r"redshift", r"snowflake(?! schema)"]),
    "Airflow": ("Data Engineering", [r"airflow"]),
    "Kafka": ("Data Engineering", [r"kafka"]),
    # Data analysis
    "Pandas": ("Data Analysis", [r"pandas"]),
    "NumPy": ("Data Analysis", [r"numpy"]),
    "Excel": ("Data Analysis", [r"excel", r"spreadsheets?"]),
    "Power BI": ("Data Analysis", [r"power\s?bi"]),
    "Tableau": ("Data Analysis", [r"tableau"]),
    "Data Visualization": ("Data Analysis", [r"matplotlib", r"seaborn", r"plotly", r"data visuali[sz]ation", r"dashboards?"]),
    "Statistics": ("Data Analysis", [r"statistics", r"statistical", r"hypothesis test"]),
    "EDA": ("Data Analysis", [r"\beda\b", r"exploratory data analysis"]),
    # ML / AI
    "Machine Learning": ("Machine Learning", [r"machine learning", r"\bml\b", r"classification", r"regression"]),
    "scikit-learn": ("Machine Learning", [r"scikit[- ]?learn", r"sklearn"]),
    "Deep Learning": ("Machine Learning", [r"deep learning", r"neural networks?", r"\bcnn\b", r"\blstm\b", r"\brnn\b"]),
    "TensorFlow": ("Machine Learning", [r"tensorflow", r"keras"]),
    "PyTorch": ("Machine Learning", [r"pytorch"]),
    "Ensemble Models": ("Machine Learning", [r"xgboost", r"lightgbm", r"random forest", r"gradient boosting"]),
    "Feature Engineering": ("Machine Learning", [r"feature engineering", r"feature selection"]),
    "Model Evaluation": ("Machine Learning", [r"precision", r"recall", r"f1[- ]score", r"roc[- ]auc", r"cross[- ]validation", r"confusion matrix"]),
    "NLP": ("Artificial Intelligence", [r"\bnlp\b", r"natural language", r"text classification", r"spacy", r"nltk"]),
    "Computer Vision": ("Artificial Intelligence", [r"computer vision", r"opencv", r"image classification", r"object detection", r"yolo"]),
    "LLMs": ("Artificial Intelligence", [r"\bllms?\b", r"large language model", r"gpt", r"langchain", r"\brag\b", r"prompt engineering", r"hugging\s?face", r"transformers?"]),
    # Web
    "HTML": ("Web Development", [r"html5?"]),
    "CSS": ("Web Development", [r"\bcss3?\b", r"tailwind", r"bootstrap"]),
    "React": ("Web Development", [r"react(?:\.js|js)?\b"]),
    "Next.js": ("Web Development", [r"next\.?js"]),
    "Node.js": ("Backend Development", [r"node\.?js", r"express(?:\.js)?\b"]),
    # Backend
    "FastAPI": ("Backend Development", [r"fastapi"]),
    "Flask": ("Backend Development", [r"flask"]),
    "Django": ("Backend Development", [r"django"]),
    "Spring Boot": ("Backend Development", [r"spring\s?boot", r"\bspring\b"]),
    "REST APIs": ("Backend Development", [r"rest(?:ful)?\s?apis?", r"\bapis?\b", r"endpoints?"]),
    "Authentication": ("Backend Development", [r"\bjwt\b", r"oauth", r"authentication"]),
    # Cloud
    "AWS": ("Cloud and Deployment", [r"\baws\b", r"amazon web services", r"\bec2\b", r"aws lambda"]),
    "Cloud Computing": ("Cloud and Deployment", [r"cloud computing", r"\biaas\b", r"\bpaas\b", r"\bsaas\b"]),
    "Azure": ("Cloud and Deployment", [r"azure"]),
    "GCP": ("Cloud and Deployment", [r"\bgcp\b", r"google cloud"]),
    "IBM Cloud": ("Cloud and Deployment", [r"ibm cloud", r"watsonx", r"granite"]),
    "Docker": ("Cloud and Deployment", [r"docker"]),
    "Kubernetes": ("Cloud and Deployment", [r"kubernetes", r"\bk8s\b"]),
    "Linux": ("Cloud and Deployment", [r"linux", r"ubuntu", r"bash", r"shell scripting"]),
    "CI/CD": ("Cloud and Deployment", [r"ci/cd", r"github actions", r"jenkins"]),
    # Software engineering
    "Git": ("Software Engineering", [r"\bgit\b", r"github", r"gitlab"]),
    "Testing": ("Software Engineering", [r"pytest", r"unit tests?", r"junit", r"testing"]),
    "Selenium": ("Software Engineering", [r"selenium", r"playwright", r"cypress"]),
    "API Testing": ("Software Engineering", [r"postman", r"api testing", r"rest assured"]),
    "Agile": ("Software Engineering", [r"agile", r"scrum", r"\bjira\b"]),
    "System Design": ("Software Engineering", [r"system design", r"scalab", r"microservices?", r"caching"]),
    # CS fundamentals
    "Pseudocode": ("CS Fundamentals", [r"pseudo-?code"]),
    "Bit Manipulation": ("Data Structures and Algorithms", [r"bit manipulation", r"bitwise", r"\bxor\b", r"bit shifts?"]),
    "Operating Systems": ("CS Fundamentals", [r"operating systems?", r"\bos\b"]),
    "Computer Networks": ("CS Fundamentals", [r"computer networks?", r"networking", r"tcp/ip"]),
    "Cyber Security": ("CS Fundamentals", [r"cyber\s?security", r"network security", r"information security", r"honeypot", r"owasp", r"penetration testing"]),
    # Aptitude (campus drives test these even though resumes rarely list them)
    "Quantitative Aptitude": ("Aptitude", [r"quantitative aptitude", r"\bquant\b", r"aptitude"]),
    "Logical Reasoning": ("Aptitude", [r"logical reasoning", r"critical reasoning", r"abstract reasoning"]),
    "Verbal Ability": ("Aptitude", [r"verbal ability", r"english grammar", r"reading comprehension"]),
    # Behavioural
    "Troubleshooting": ("CS Fundamentals", [r"troubleshoot\w*", r"debugging hardware", r"help ?desk"]),
    "Communication": ("Communication and Behavioural", [r"communication", r"presented", r"presentation", r"public speaking"]),
    "Teamwork": ("Communication and Behavioural", [r"team(?:work)?", r"collaborat"]),
    "Leadership": ("Communication and Behavioural", [r"\bled\b", r"lead(?:er|ing)", r"coordinator", r"captain", r"head of"]),
}

# "If the resume shows X, the student very likely touched Y."  Shown as AI-INFERRED,
# never as proven. Each rule carries the reason we display.
INFERENCES: list[tuple[str, str, str]] = [
    ("FastAPI", "REST APIs", "FastAPI apps are REST APIs, so you have likely built API endpoints."),
    ("Flask", "REST APIs", "Flask projects usually expose HTTP endpoints."),
    ("Django", "REST APIs", "Django projects usually expose HTTP endpoints."),
    ("MySQL", "SQL", "Using MySQL means writing SQL queries."),
    ("PostgreSQL", "SQL", "Using PostgreSQL means writing SQL queries."),
    ("SQLite", "SQL", "Using SQLite means writing SQL queries."),
    ("scikit-learn", "Machine Learning", "scikit-learn is a machine learning library."),
    ("Pandas", "EDA", "Pandas is the usual tool for exploring a dataset."),
    ("TensorFlow", "Deep Learning", "TensorFlow/Keras is mainly used for neural networks."),
    ("PyTorch", "Deep Learning", "PyTorch is mainly used for neural networks."),
    ("React", "JavaScript", "React is written in JavaScript."),
    ("Next.js", "React", "Next.js is built on React."),
    ("Docker", "Linux", "Docker images are mostly Linux based."),
    ("Spring Boot", "Java", "Spring Boot is a Java framework."),
]


def compile_patterns() -> dict[str, list[re.Pattern]]:
    out = {}
    for name, (_, pats) in SKILLS.items():
        out[name] = [re.compile(rf"(?<![\w.+#]){p}(?![\w+#])" if not p.startswith(r"\b") else p, re.I) for p in pats]
    return out


PATTERNS = compile_patterns()


def category_of(name: str) -> str:
    return SKILLS.get(name, ("Other", []))[0]


def canonical(name: str) -> str | None:
    """Map free text like 'reactjs' or 'Postgres' to a canonical skill name."""
    for canon, pats in PATTERNS.items():
        if canon.lower() == name.strip().lower() or any(p.search(name) for p in pats):
            return canon
    return None
