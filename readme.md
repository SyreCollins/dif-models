################ *OVERVIEW* #################

- The API exposes the following major functionalities:

    > ChemProcess_Model
    > MicroEconomic_Model: Computes project economics based on various funding scenarios.
    > MacroEconomic_Model: Estimates macroeconomic impacts using multipliers.
    > Analytics_Model: Integrates all models to produce a comprehensive analysis and project economics outputs.
    > Additionally, the `/run_model` endpoint runs the full integrated model, reading input CSV files and generating a complete output.

<Note: Make sure the paths in the code correctly points to the CSV files in the data_inputs folder.
You can find the complete package list in requirements.txt file.


- *Install Dependencies:*
    `pip install -r requirements.txt`

- *Running the API*
    -You can run the API locally using Uvicorn. In your terminal, execute:

        `uvicorn main:app --reload`
        The --reload flag enables auto-reloading for code changes.
        The API will be available at http://127.0.0.1:8000.
        Open your browser and navigate to http://127.0.0.1:8000/docs to view the automatically generated OpenAPI documentation and try out the endpoints interactively.

- *Endpoints Overview*
    - The API includes the following endpoints:

        GET `/`
            Returns a welcome message.

        POST `/chemprocess`
            Calls the ChemProcess_Model function.
            Input: JSON object with keys matching the chemical process model parameters.
            Output: Calculated arrays for product output, feed, heat, etc.

        POST `/microeconomic`
            Calls the MicroEconomic_Model function.
            Input: JSON with the model data and parameters such as plant_mode, fund_mode, opex_mode, and carbon_value.
            Output: Breakeven prices and a timeline (Years array).

        POST `/macroeconomic`
            Calls the MacroEconomic_Model function.
            Input: JSON containing both the data and multiplier parameters, along with location and funding modes.
            Output: Macroeconomic impact arrays and timeline.

        POST /analytics
            Calls the Analytics_Model function which integrates all models.
            Input: JSON with parameters like location, product, plant_mode, fund_mode, opex_mode, and carbon_value.
            Output: A detailed DataFrame of project economics as JSON.

        GET `/run_model`
            Runs the full integrated model. It reads the required CSV files, processes the models, concatenates results, and returns the complete output as JSON.

- *How the API Works*
    -Model Integration:
        The code from the original Python script is used in the api code without any changes. Each section (process, microeconomic, macroeconomic, and analytics models) is defined as a function. These functions perform all calculations and transformations using NumPy and Pandas.

- *FastAPI Endpoints:*
    Each endpoint in the FastAPI application calls one of the model functions:

    Input data is validated using Pydantic models.
    The model function is executed with the validated input.
    The result (often arrays or DataFrames) is returned as JSON. When needed, Pandas DataFrames are converted to dictionaries.
    *File I/O*:
        The integrated run (`/run_model` and `/analytics`) reads external CSV files from the data_inputs folder. Ensure that the file paths in the code match your project structure.

- *Error Handling:*
    Each endpoint uses a try-except block to catch errors and return an HTTP 500 status with the error message. This helps developers diagnose issues quickly.

- *Calling the API from WordPress*
    There are several ways to call the API from WordPress. Below are two common approaches:

    1. Using WordPress HTTP API (Server-to-Server)
        You can use the built-in WordPress function wp_remote_post() to call the API from a plugin or theme’s functions.php file.

        Example PHP snippet:
                <?php
                function call_ipem_api() {
                    $url = 'http://your-api-domain.com/analytics';
                    $args = array(
                        'body'        => json_encode( array(
                            'location'   => 'SAU',
                            'product'    => 'Methanol',
                            'plant_mode' => 'Green',
                            'fund_mode'  => 'Equity',
                            'opex_mode'  => 'Inflated',
                            'carbon_value' => 'No'
                        )),
                        'headers'     => array(
                            'Content-Type' => 'application/json'
                        ),
                        'timeout'     => 60
                    );
    
                    $response = wp_remote_post( $url, $args );
                    if ( is_wp_error( $response ) ) {
                        return 'Error: ' . $response->get_error_message();
                    }
    
                    $body = wp_remote_retrieve_body( $response );
                    $result = json_decode( $body, true );
                    return $result;
                }

                // You can hook this function to a shortcode or AJAX action to display results in WordPress.
                add_shortcode('ipem_api', 'call_ipem_api');
                ?> """

2. Using AJAX from the Front-End
If you prefer to call the API from JavaScript (for example, via an AJAX call in a custom theme or plugin), you can use the fetch API or jQuery’s AJAX functions.

Example using fetch:
"""
<script>
document.addEventListener("DOMContentLoaded", function() {
    fetch('http://your-api-domain.com/analytics', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            location: 'SAU',
            product: 'Methanol',
            plant_mode: 'Green',
            fund_mode: 'Equity',
            opex_mode: 'Inflated',
            carbon_value: 'No'
        })
    })
    .then(response => response.json())
    .then(data => {
        console.log("API response:", data);
        // Process and display the data as needed on your WordPress site.
    })
    .catch(error => console.error("Error:", error));
});
</script>"""

Note:

Replace http://your-api-domain.com with the actual domain where your API is hosted.
Optimizing and Updating the Code
Junior developers can improve or extend the API by:

Refactoring:
Break the large main.py into separate modules (e.g., models.py, endpoints.py, utils.py) to improve maintainability.

Testing:
Add unit tests using frameworks such as pytest to cover the functionality of each model function.

Documentation:
Keep inline comments and update the OpenAPI docs by leveraging FastAPI’s automatic documentation features.

Performance Improvements:
Profile the functions with large datasets to ensure that the API remains responsive. Consider caching frequently used data (like CSV inputs) or using async functions where appropriate.

Configuration Management:
Use environment variables or configuration files (e.g., with Python’s pydantic.BaseSettings) to manage file paths, host URLs, or other deployment settings.

Troubleshooting
CSV File Paths:
Ensure that the CSV file paths in the model functions match the file structure on your server.

Dependency Issues:
If you run into dependency issues, verify your Python version and reinstall packages using pip install -r requirements.txt.

Error Handling:
Check the error messages returned by the API endpoints for clues. FastAPI’s interactive docs (http://127.0.0.1:8000/docs) can help test endpoints locally.