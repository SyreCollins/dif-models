Economic Model API
==================

Description
-----------
This project implements an integrated economic model API using FastAPI. The API aggregates outputs
from chemical process, microeconomic, and macroeconomic models to provide financial, economic, and
environmental metrics based on user input parameters. Data is sourced from CSV files (project_data.csv
and sectorwise_multipliers.csv), and the API is designed for flexibility and integration with other systems,
including WordPress.

Features:
- Processes economic and environmental data to compute breakeven prices, cash flows, and more.
- Provides a single endpoint (/run_model) for executing the integrated model.
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
   http://127.0.0.1:8000/run_model?plant_mode=Green&plant_size=Large&plant_effy=High&fund_mode=Debt&opex_mode=Standard&location=USA&product=Ethylene&carbon_value=No

Deploying on Render
-------------------
Render is a cloud hosting platform that simplifies deployment of web services. To host your API on Render:

1. **Create a Render Account:**
   - Sign up at https://render.com if you don’t already have an account.

2. **Prepare Your Repository:**
   - Push your project repository (including modelapi.py, CSV files, and requirements.txt) to a Git provider such as GitHub, GitLab, or Bitbucket.

3. **Create a New Web Service on Render:**
   - Log in to your Render dashboard.
   - Click the "New" button and select "Web Service".
   - Connect your Git repository to Render.
   - In the "Environment" section, select the appropriate branch.
   - Set the **Build Command** to:
     pip install -r requirements.txt
   - Set the **Start Command** to:
     uvicorn modelapi:app --host 0.0.0.0 --port $PORT
   - Choose your preferred region and plan, then click "Create Web Service".

4. **Configure Environment Variables (if needed):**
   - If your project requires additional environment-specific settings (e.g., API keys, file paths), add these in the Render dashboard under the "Environment" tab.

5. **Deploy and Test:**
   - Render will automatically build and deploy your application.
   - Once deployed, your API will be accessible via the URL provided by Render (e.g., https://your-app-name.onrender.com).
   - Test the deployed API using a URL such as:
     https://your-app-name.onrender.com/run_model?plant_mode=Green&plant_size=Large&plant_effy=High&fund_mode=Debt&opex_mode=Standard&location=USA&product=Ethylene&carbon_value=No

Using the API on WordPress
--------------------------
You can integrate the Economic Model API with your WordPress site by making HTTP requests to the API endpoint. There are several ways to do this. Here’s an example using the built-in WordPress HTTP API and a shortcode:

1. **Add the following code to your theme’s functions.php file or a custom plugin:**

   ```php
   // Function to fetch data from the Economic Model API
   function get_economic_model_data() {
       // Replace with your deployed API URL or local URL for testing.
       $api_url = 'https://your-app-name.onrender.com/run_model?plant_mode=Green&plant_size=Large&plant_effy=High&fund_mode=Debt&opex_mode=Standard&location=USA&product=ProductA&carbon_value=50';
       
       $response = wp_remote_get($api_url);
       if (is_wp_error($response)) {
           return 'Error fetching data from the Economic Model API.';
       }
       
       $body = wp_remote_retrieve_body($response);
       $data = json_decode($body, true);
       
       // Process the data as needed. For simplicity, we return it as JSON.
       return '<pre>' . print_r($data, true) . '</pre>';
   }
   
   // Shortcode to display the Economic Model API data
   function economic_model_shortcode() {
       return get_economic_model_data();
   }
   add_shortcode('economic_model', 'economic_model_shortcode');
