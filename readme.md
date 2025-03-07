Economic Model API
==================

Description
-----------
This project implements an integrated economic model API using FastAPI.
It aggregates outputs from chemical process, microeconomic, and macroeconomic models to
provide financial, economic, and environmental metrics based on user input parameters.
The API uses CSV files (project_data.csv and sectorwise_multipliers.csv) as data sources
for the underlying models.

Features:
- Processes economic and environmental data to compute breakeven prices, cash flows, etc.
- Provides an endpoint (/run_model) for executing the integrated model.
- Uses FastAPI for API routing and Pydantic for data validation.

Requirements
------------
- Python 3.8 or higher
- FastAPI
- Uvicorn
- Pandas
- NumPy
- Pydantic

Installation
------------
1. Clone the repository:
   git clone <your-repo-url>
2. Change to the project directory:
   cd <your-project-directory>
3. Create a virtual environment:
   python -m venv venv
4. Activate the virtual environment:
   - On Windows: venv\Scripts\activate
   - On macOS/Linux: source venv/bin/activate
5. Install the required packages:
   pip install -r requirements.txt

Running Locally
---------------
1. Ensure that the CSV files (project_data.csv and sectorwise_multipliers.csv) are present in the root directory.
2. Start the API server with Uvicorn:
   uvicorn modelapi:app --reload
3. The API will be available at:
   http://127.0.0.1:8000
4. To test the API, you can use a web browser, Postman, or cURL. For example, use the URL below:
   http://127.0.0.1:8000/run_model?plant_mode=Green&plant_size=Large&plant_effy=High&fund_mode=Debt&opex_mode=Standard&location=USA&product=ProductA&carbon_value=50

Deploying on Render
-------------------
Render is a cloud hosting platform that makes it easy to deploy web services. To host your API on Render, follow these steps:

1. **Create a Render Account:**
   - Sign up at https://render.com if you do not already have an account.

2. **Prepare Your Repository:**
   - Push your project repository (including modelapi.py, CSV files, and requirements.txt) to a Git provider like GitHub, GitLab, or Bitbucket.

3. **Create a New Web Service on Render:**
   - Log in to your Render dashboard.
   - Click on the "New" button and select "Web Service".
   - Connect your Git repository to Render.
   - In the "Environment" section, choose the appropriate branch.
   - For the **Build Command**, enter:
     pip install -r requirements.txt
   - For the **Start Command**, enter:
     uvicorn modelapi:app --host 0.0.0.0 --port $PORT or sh start.sh
   - Choose your preferred region and plan, then click "Create Web Service".

4. **Configure Environment Variables (if needed):**
   - If your project requires environment-specific settings (e.g., file paths or API keys), add these in the Render dashboard under the "Environment" tab.

5. **Deploy and Test:**
   - Render will automatically build and deploy your application.
   - Once deployed, your API will be accessible via the URL provided by Render.
   - You can test the deployed API by visiting the endpoint (e.g., https://your-app-name.onrender.com/run_model?plant_mode=Green&plant_size=Large&plant_effy=High&fund_mode=Debt&opex_mode=Standard&location=USA&product=Ethylene&carbon_value=No).

6. **Updates and Redeployment:**
   - Any commit pushed to the connected branch will trigger a new deployment on Render.


