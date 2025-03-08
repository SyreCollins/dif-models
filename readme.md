---

# Integrated Project Economics API

The **Integrated Project Economics API** provides RESTful endpoints to run advanced process and economic models developed in Python. This API is built with [FastAPI](https://fastapi.tiangolo.com/) and includes endpoints for:
- **Integrated Analytics Model** (`/analytics`)

It also shows how to integrate the API with a WordPress website and deploy it on [Render](https://render.com).

---

## Table of Contents

- [Features](#features)
- [Requirements](#requirements)
- [Installation](#installation)
- [Running Locally](#running-locally)
- [API Usage Examples](#api-usage-examples)
  - [Analytics Endpoint](#analytics-endpoint)
- [Integrating with WordPress](#integrating-with-wordpress)
  - [PHP Example](#php-example)
  - [JavaScript (Fetch API) Example](#javascript-fetch-api-example)
- [Deploying on Render](#deploying-on-render)

---

## Features

- **RESTful Endpoints** – Easily run each model with simple POST requests.
- **JSON Payloads** – Accepts JSON data, making it ideal for integration with various front-end frameworks.
- **CSV Data Integration** – Utilizes local CSV files (`project_data.csv` and `sectorwise_multipliers.csv`) for advanced analytics.
- **WordPress Integration** – Connect to your WordPress site using PHP or JavaScript.
- **Deployable on Render** – Quick and hassle-free deployment on Render for scalable hosting.

---

## Requirements

- Python 3.7+
- [FastAPI](https://fastapi.tiangolo.com/)
- [Uvicorn](https://www.uvicorn.org/)
- [Pandas](https://pandas.pydata.org/), [NumPy](https://numpy.org/)
- Other dependencies listed in `requirements.txt`

---

## Installation

1. **Clone the Repository:**

   ```bash
   git clone https://github.com/yourusername/integrated-project-economics-api.git
   cd integrated-project-economics-api
   ```

2. **Install Dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

3. **CSV Files:**  
   Ensure that `project_data.csv` and `sectorwise_multipliers.csv` are placed in the same directory as `main.py`.

---

## Running Locally

Start the API locally using Uvicorn:

```bash
uvicorn main:app --reload
```

The API will run at [http://127.0.0.1:8000](http://127.0.0.1:8000)

---

## API Usage Examples

### Analytics Endpoint

**URL:** `POST /analytics`

**Sample JSON Payload:**

```json
{
  "location": "USA",
  "product": "Ethylene",
  "plant_mode": "Brown",
  "fund_mode": "Equity",
  "opex_mode": "Inflated",
  "carbon_value": "No"
}
```

You can test these endpoints using Postman or cURL.

---

## Integrating with WordPress

You can connect your WordPress site to this API using either PHP (server-side) or JavaScript (client-side).

### PHP Example

Add the following snippet to your theme’s `functions.php` or a custom plugin:

```php
function call_project_economics_api() {
    $url = 'https://your-api-domain.com/analytics'; // Replace with your API URL
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
```

You can call this function from your theme template to display API results.

### JavaScript (Fetch API) Example

Ensure CORS is enabled on your API, then add the following script to your WordPress page:

```javascript
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
```

---

## Deploying on Render

[Render](https://render.com) provides an easy way to deploy web services. Follow these steps:

1. **Create a Render Account:**  
   Sign up at [Render](https://render.com).

2. **Push Your Code to GitHub:**  
   Ensure your repository contains `main.py`, `requirements.txt`, and your CSV files.

3. **Create a New Web Service on Render:**
   - Log in to your Render dashboard.
   - Click **New +** and choose **Web Service**.
   - Connect your GitHub account and select your repository.
   - Configure the service:
     - **Name:** Choose a suitable name.
     - **Environment:** Select `Python`.
     - **Build Command:**  
       ```bash
       pip install -r requirements.txt
       ```
     - **Start Command:**  
       ```bash
       uvicorn main:app --host 0.0.0.0 --port $PORT
       ```
   - Click **Create Web Service**.

4. **Access Your API:**  
   Once deployed, Render will provide a URL (e.g., `https://your-service.onrender.com`) to use in your WordPress integrations or API tests.

---
