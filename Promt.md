## 🚀 Claude Code Prompt cho Dự Án Burp AI MCP

### **Main Prompt:**

```markdown
Create a Burp Suite extension that integrates with a local AI model through MCP (Model Context Protocol) for automated vulnerability detection. The project should have three main components:

1. A Burp Suite extension (Java) that intercepts HTTP traffic
2. An MCP server (Python) that handles communication between Burp and AI
3. Integration with Ollama for local LLM analysis

Project structure:
- burp-extension/ (Java project with Burp API)
- mcp-server/ (Python Flask server with MCP protocol)
- tests/ (Test cases for common vulnerabilities)

The extension should:
- Intercept HTTP requests/responses from Burp
- Send them to MCP server for analysis
- Display vulnerability findings in Burp UI
- Support detection of: SQL Injection, XSS, IDOR, Path Traversal

Use simple, educational code that's easy to understand and modify.
```

### **Detailed Implementation Prompts:**

#### **1. Burp Extension Setup**
```markdown
Create a Burp Suite extension in Java with these requirements:

1. File: burp-extension/src/BurpExtender.java
- Implement IBurpExtender and IHttpListener interfaces
- Register as "AI MCP Analyzer" extension
- Intercept HTTP responses
- Send request data to MCP server at http://localhost:8000/analyze
- Parse JSON response and log vulnerabilities
- Add Burp issues when vulnerabilities are found

2. File: burp-extension/build.gradle
- Setup Gradle build for Burp extension
- Include necessary dependencies (Burp API, JSON handling)
- Create fat JAR for easy loading in Burp

Keep the code simple and well-commented for educational purposes.
```

#### **2. MCP Server Implementation**
```markdown
Create a Python MCP server that bridges Burp and AI:

1. File: mcp-server/server.py
- Flask server on port 8000
- POST endpoint /analyze that receives HTTP request data
- Extract parameters from requests (GET params, POST body)
- Call AI handler for analysis
- Return JSON with vulnerability findings

2. File: mcp-server/ai_handler.py
- AIAnalyzer class using Ollama Python client
- Use llama2:7b model for analysis
- Create security-focused prompts for vulnerability detection
- Parse AI responses into structured format
- Detect: SQL Injection, XSS, IDOR, Path Traversal

3. File: mcp-server/requirements.txt
- flask
- ollama
- Standard Python libraries only

Include error handling and logging for debugging.
```

#### **3. Test Cases**
```markdown
Create test cases to validate the vulnerability detection:

1. File: tests/test_vulnerabilities.py
- Test SQL injection detection with common payloads
- Test XSS detection with script tags
- Test IDOR with sequential ID parameters
- Test path traversal with ../ patterns
- Measure detection accuracy

2. File: tests/test_requests/
- Create sample HTTP requests for each vulnerability type
- Include both vulnerable and safe examples
- Format as raw HTTP requests

Make tests runnable with simple Python script.
```

#### **4. Setup and Documentation**
```markdown
Create setup scripts and documentation:

1. File: setup.sh
- Install Ollama
- Pull llama2:7b model
- Setup Python virtual environment
- Install Python dependencies
- Build Burp extension
- Start MCP server

2. File: README.md
- Project overview and architecture diagram
- Installation instructions
- Usage guide with screenshots placeholders
- How to test with DVWA/WebGoat
- Troubleshooting common issues

3. File: docker-compose.yml (optional)
- Containerize MCP server
- Include Ollama service
- Make it easy to deploy

Keep everything beginner-friendly with clear instructions.
```

### **Code Quality Requirements:**
```markdown
For all code files:
1. Add comprehensive comments explaining logic
2. Use clear variable names
3. Include error handling with helpful messages
4. Add logging for debugging
5. Keep functions small and focused
6. Use type hints in Python
7. Follow standard conventions (PEP8 for Python, Java conventions)

This is an educational research project, so clarity > optimization.
```

### **Testing Instructions:**
```markdown
Include a TESTING.md file with:
1. How to set up a test environment (DVWA recommended)
2. Step-by-step testing procedure
3. Expected results for each test case
4. How to verify the AI is working correctly
5. Performance benchmarks to expect

Add example curl commands to test the MCP server directly.
```

### **Bonus Features (Optional):**
```markdown
If time permits, add these enhancements:
1. Simple web UI for MCP server (view analysis history)
2. Export findings to JSON/CSV
3. Confidence scoring for each finding
4. Rate limiting to prevent overloading the AI
5. Basic authentication for MCP server

Mark these clearly as optional extensions.
```

### **Final Output Structure:**
```
burp-ai-mcp/
├── burp-extension/
│   ├── src/
│   │   └── BurpExtender.java
│   ├── build.gradle
│   └── README.md
├── mcp-server/
│   ├── server.py
│   ├── ai_handler.py
│   ├── requirements.txt
│   └── README.md
├── tests/
│   ├── test_vulnerabilities.py
│   └── test_requests/
│       ├── sqli.http
│       ├── xss.http
│       └── idor.http
├── setup.sh
├── docker-compose.yml
├── README.md
├── TESTING.md
└── LICENSE
```

### **Execution Note for Claude Code:**
```markdown
This is a multi-file project. Create all files with proper directory structure. Each component should be independently testable. The final result should be a working proof-of-concept that can be demonstrated in an academic setting.

Start with the MCP server (Python) as it's easier to test independently, then create the Burp extension, and finally add the test suite.
```

---

**Sử dụng prompt này với Claude Code:**
1. Copy toàn bộ prompt trên
2. Paste vào Claude Code terminal
3. Claude Code sẽ tạo toàn bộ project structure
4. Follow up với các câu hỏi cụ thể nếu cần

**Ví dụ follow-up prompts:**
- "Add more detailed logging to the AI handler"
- "Create a simple UI panel for the Burp extension"
- "Add support for detecting XXE vulnerabilities"
- "Improve the prompt engineering for better accuracy"