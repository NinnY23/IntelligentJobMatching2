# Resume Parsing Setup Instructions

## Enhanced PDF Resume Parsing with PyMuPDF and spaCy

This guide explains how to set up and use the advanced resume parsing features.

### Installation

1. **Install Python dependencies:**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

2. **Download spaCy language model:**
   ```bash
   python -m spacy download en_core_web_sm
   ```

   The model download size is ~40MB. This is required for Name Extraction using NLP.

### Features

The resume parsing system now extracts:

1. **Name** - Extracted using spaCy NER (Named Entity Recognition)
2. **Email** - Extracted using regex pattern matching
3. **Phone** - Extracted using regex pattern matching (supports multiple formats)
4. **Skills** - Matched against a predefined list of 30+ technical keywords
5. **Education** - Extracted by identifying education-related keywords

### API Endpoints

#### 1. Upload PDF Resume
**Endpoint:** `POST /api/upload-resume`

**Request:**
- File input: PDF file (.pdf only)
- Authorization: Bearer token

**Response:**
```json
{
  "message": "Resume parsed successfully",
  "resume_data": {
    "name": "John Doe",
    "email": "john@example.com",
    "phone": "+1-234-567-8900",
    "skills": ["Python", "React", "AWS"],
    "education": ["Bachelor of Science in Computer Science", "University Name"]
  },
  "extracted_skills": ["Python", "React", "AWS"],
  "user": { ... }
}
```

#### 2. Parse Resume Text Manually
**Endpoint:** `POST /api/parse-resume-text`

**Request:**
```json
{
  "resumeText": "Your resume content here..."
}
```

**Response:** Same as PDF endpoint

### Supported Skills (30+)

- **Languages:** Python, JavaScript, Java, C++, C#, PHP, Ruby, Go, Rust
- **Frontend:** HTML, CSS, React, Angular, Vue
- **Backend:** Node.js, Express, Flask, Django
- **Databases:** SQL, MySQL, PostgreSQL, MongoDB, Redis
- **Tools:** Docker, Kubernetes, Git, Linux, AWS, Azure, GCP
- **Other:** Machine Learning, Data Analysis, Pandas, NumPy, TensorFlow, PyTorch, Agile, Scrum

### Troubleshooting

**Error: "spacy model 'en_core_web_sm' not found"**
- Solution: Run `python -m spacy download en_core_web_sm`

**Error: "PyMuPDF import error"**
- Solution: Ensure PyMuPDF is installed: `pip install PyMuPDF==1.23.8`

**No phone/email extracted:**
- The regex patterns support common formats. Complex formats may not be detected.

**No name extracted:**
- The fallback is to use the first line of the resume as the name.

### Example Usage Flow

1. User logs in to the application
2. Goes to Profile → Edit Profile
3. Either:
   - **Option A:** Upload PDF resume → System extracts all data
   - **Option B:** Click "Or Input Manually" → Paste resume text → Parse
4. System displays:
   - Extracted name, email, phone
   - Detected skills
   - Identified education background
5. Skills are automatically added to user profile
6. User can save or make manual adjustments

### Performance Notes

- PDF parsing: Usually < 1 second for standard resumes
- Text parsing: < 500ms for typical resume length (up to 3000 chars)
- File size limit: No hard limit, but large PDFs (>10MB) may be slow

### Security

- Only authenticated users can upload/parse resumes
- Files are processed in-memory (not stored)
- CORS enabled for frontend communication
- Content-Type validation for PDF files
