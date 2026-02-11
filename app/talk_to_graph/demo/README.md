# Natural Language Graph Query System Demo

This demo project showcases the Natural Language Graph Query System, allowing users to query an RDF knowledge graph using both SPARQL and natural language through a language model (LLM). The demo is structured to provide a clear separation between the backend services and the frontend interface.

## Project Structure

- **backend/**: Contains the Flask application and services for handling SPARQL and LLM queries.
- **frontend/**: Contains the HTML, CSS, and JavaScript files for the user interface.
- **data/**: Contains the graph data reference loaded from the specified JSON-LD directory.
- **.env.example**: Example environment configuration file.
- **.gitignore**: Specifies files to be ignored by Git.

## Setup Instructions

1. **Clone the Repository**: 
   ```bash
   git clone <repository-url>
   cd demo
   ```

2. **Create a Virtual Environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r backend/requirements.txt
   ```

4. **Configure Environment Variables**:
   - Copy `.env.example` to `.env` and update the necessary configurations.

5. **Run the Backend**:
   ```bash
   python backend/app.py
   ```

6. **Access the Frontend**:
   Open your web browser and navigate to `http://localhost:5000` (or the port specified in your app configuration).

## Usage

- **SPARQL Queries**: Use the designated form to submit SPARQL queries directly to the backend and view the results.
- **Natural Language Queries**: Enter natural language queries to interact with the LLM and receive generated responses based on the graph data.

## Contributing

Contributions are welcome! Please submit a pull request or open an issue for any enhancements or bug fixes.

## License

This project is licensed under the MIT License. See the LICENSE file for more details.