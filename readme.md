Integrated Project Economics API
This project exposes a series of endpoints built with FastAPI to run several integrated economic and process models. The API provides endpoints for:

Chemical Process Model (/chemprocess)
Microeconomic Model (/microeconomic)
Integrated Analytics Model (/analytics)
The analytics endpoint integrates data from CSV files (e.g., project_data.csv and sectorwise_multipliers.csv) along with model computations.

Table of Contents
Features
Requirements
Installation
Running Locally
API Usage Examples
Integrating with WordPress
Deploying on Render
Additional Resources
Features
FastAPI-based endpoints: Provides RESTful endpoints for running model calculations.
Flexible Input: Accepts JSON payloads with model parameters.
CSV Data Integration: Loads project data and sector multipliers for advanced analytics.
JSON Responses: Returns results as JSON, making it easy to integrate with front-end apps or WordPress sites.
Requirements
Python 3.7+
FastAPI
Uvicorn
Pandas, NumPy, and other dependencies (listed in requirements.txt)
Installation
Clone the Repository:

git clone https://github.com/yourusername/integrated-project-economics-api.git
cd integrated-project-economics-api
Install Dependencies:

pip install -r requirements.txt
Ensure CSV Files are Available:
Place project_data.csv and sectorwise_multipliers.csv in the same directory as main.py.

Running Locally
You can run the API locally using Uvicorn:

uvicorn main:app --reload
The API will be accessible at http://127.0.0.1:8000. You can also view the interactive documentation at http://127.0.0.1:8000/docs.

API Usage Examples
1. Analytics Endpoint
URL: POST /analytics

Sample JSON Payload:

{
  "location": "USA",
  "product": "Ethylene",
  "plant_mode": "Brown",
  "fund_mode": "Equity",
  "opex_mode": "Inflated",
  "carbon_value": "No"
}
You can test these endpoints using tools like Postman or cURL.

Integrating with WordPress
To connect your WordPress website to this API, you can use WordPress’s HTTP API (using functions such as wp_remote_post()) or JavaScript’s fetch() method.

Example using PHP in WordPress
Add the following snippet to your theme’s functions.php or a custom plugin:

function call_project_economics_api() {
    $url = 'https://your-api-domain.com/analytics'; // Replace with your deployed API URL
    $body = json_encode(array(
         'location'      => 'USA',
         'product'       => 'Ethylene',
         'plant_mode'    => 'Brown',
         'fund_mode'     => 'Equity',
         'opex_mode'     => 'Inflated',
         'carbon_value'  => 'No'
    ));

    $args = array(
       'body'      => $body,
       'headers'   => array('Content-Type' => 'application/json'),
       'timeout'   => 60,
    );

    $response = wp_remote_post($url, $args);
    if (is_wp_error($response)) {
        return 'Error: ' . $response->get_error_message();
    } else {
        return wp_remote_retrieve_body($response);
    }
}
You can call this function in your theme template to display API results on your WordPress site.

Example using JavaScript (Fetch API)
If you prefer a client-side solution, use the following JavaScript code snippet (ensure CORS is enabled on your API):

javascript
Copy
Edit
fetch("https://your-api-domain.com/analytics", {
    method: "POST",
    headers: {
        "Content-Type": "application/json"
    },
    body: JSON.stringify({
         location: "USA",
         product: "Ethylene",
         plant_mode: "Brown",
         fund_mode: "Equity",
         opex_mode: "Inflated",
         carbon_value: "No"
    })
})
.then(response => response.json())
.then(data => {
    console.log(data);
    // Process and display data on your WordPress page
})
.catch(error => console.error("Error:", error));
Deploying on Render
Render is a cloud platform that makes it easy to deploy web services. Follow these steps to host your API on Render:

Create a Render Account:
Sign up at Render.

Push Your Code to GitHub:
Ensure your API code (including main.py and requirements.txt) is pushed to a GitHub repository.

Create a New Web Service on Render:

Go to the Render dashboard and click on New + and then Web Service.
Connect your GitHub account and select your repository.
Configure the service:
Name: Choose an appropriate name.
Environment: Select Python.
Build Command:
pip install -r requirements.txt
Start Command:
uvicorn main:app --host 0.0.0.0 --port $PORT
Render automatically sets the $PORT environment variable for your service.
Click Create Web Service.
Deployment:
Render will build and deploy your API. Once deployed, you will receive a URL (e.g., https://your-service.onrender.com) that you can use in your WordPress integrations or Postman.
