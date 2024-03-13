# LLM NFO Backend 

## Summary
This project aims to leverage LLM with the help of LangChain to help Domain Experts generate competency questions (CQs) for ontology development within specified domains and scopes. It utilizes OpenAI's GPT models through a custom implementation that includes interactive user inputs and automated question generation and validation.

## Requirements
- Python 3.8+
- Flask
- OpenAI API access
- Google OAuth2 client secrets
- Additional Python libraries as listed in `requirements.txt`

## Installation
### 1. Clone the repository:

```bash
git clone https://github.com/hidayattaufiqur/onotolgy-BE.git
cd onotolgy-BE
```

### 2. Install requirements: 
#### Option 1: Standard Python Environment
```bash
pip install -r requirements.txt
```

#### Option 2: Using Nix
If you are using Nix, you can directly run nix-shell and the requirements will be automatically installed for you. 
```bash
nix-shell
```

### 3. Set up your environment variables:
Before running the project, ensure you have the necessary credentials:

- **OpenAI API Key**: Obtain an API key by creating an account at [OpenAI](https://openai.com/product).
- **Google OAuth2 Credentials**: Set up a project in the [Google Developer Console](https://console.cloud.google.com/) to get your `client_secrets.json`, `GOOGLE_CLIENT_ID`, and `GOOGLE_CLIENT_SECRET`.

Copy the downloaded `client_secrets.json` in the root directory. 
Create a `.env` file in the root directory and add these:

```plaintext
OPENAI_API_KEY="your_openai_api_key_here"
FLASK_SECRET_KEY="your_flask_secret_key_here"
GOOGLE_CLIENT_ID="your_google_client_id_here"
GOOGLE_CLIENT_SECRET="your_client_secret_here"
```

## Running the Project
To start the Flask server, run:

```bash
python server.py
```

Navigate to `http://localhost:5000` and you should see a message `hello, world!`

## Current Available Endpoints
### 1. Login Using Google Account

- **Endpoint**: `/login`
- **Method**: `GET`
- **Description**: Initiates the authentication process using Google OAuth2. Users are redirected to the Google sign-in page.
- **Example Usage**: Navigate to `http://localhost:5000/login` in your web browser to start the login process.

### 2. User Profile Information

- **Endpoint**: `/profile`
- **Method**: `GET`
- **Description**: Displays profile information for the currently authenticated user. Requires a successful login.
- **Example Usage**: After logging in, navigate to `http://localhost:5000/profile` to view your profile information.

### 3. Generate Competency Questions (CQs)

- **Endpoint**: `/chat/`
- **Method**: `POST`
- **Description**: Generates a specified number of competency questions based on user input, focusing on a particular domain and scope.
- **Required Body**:
  - `message` (string): Detailed description from the user including the domain, scope, and number of CQs requested.
- **Example Request**:

  ```bash
  curl -X POST http://localhost:5000/chat/ \
      -H 'Content-Type: application/json' \
      -d '{
          "message": "Generate 9 competency questions focused on the integration and impact of solar panel technology within the renewable energy domain. Consider aspects such as efficiency, cost, environmental impact, and adoption barriers."
      }'
  ```

  This sends a POST request to the `/chat/` endpoint with a JSON body containing the user's message. The backend processes this input to generate and return the requested CQs.

## TODO
List any pending tasks or features that are planned for future development: 

- [ ] Implement user authorization and session management
- [ ] Implement error handling for API calls
- [ ] Implement interaction between user and LLM through langchain for validating or revising generated CQs
- [ ] Implement generated CQs storing to a database
- [ ] Implement logging 
