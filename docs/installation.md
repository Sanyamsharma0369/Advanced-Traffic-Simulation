# Installation Guide
 
 ## Prerequisites
 Before proceeding, ensure you have Git and Node.js (or relevant package manager) installed on your system.
 
 ## Installation Steps
 
 1. **Clone the Repository**  
    Run the following command to clone the repository to your local system:
    ```bash
    git clone https://github.com/Sanyamsharma0369/Advanced-Traffic-Simulation.git
    ```
 
 2. **Navigate to the Directory**  
    Change into the cloned repository's directory:
    ```bash
    cd Advanced-Traffic-Simulation
    ```
 
 3. **Install Dependencies**  
    Execute the following command to install required dependencies:
    ```bash
    npm install
    ```
    (or use `yarn install` if using Yarn)
 
 4. **Backend Setup**
    Navigate to the `backend` directory:
    ```bash
    cd backend
    ```
    Install backend dependencies:
    ```bash
    pip install -r requirements.txt
    ```
    Run the backend application:
    ```bash
    python start_backend.py
    ```

 5. **Frontend Setup**
    Navigate to the `frontend/traffic-dashboard` directory:
    ```bash
    cd ../frontend/traffic-dashboard
    ```
    Install frontend dependencies:
    ```bash
    npm install
    ```
    Start the frontend development server:
    ```bash
    npm start
    ```

 6. **Configure the System**  
    Create and modify the configuration file as needed:
    ```bash
    cp config.example.json config.json
    ```
    Edit the `config.json` file with your specific settings.
 
 7. **Verify Installation**  
    Run the following test to confirm the installation was successful:
    ```bash
    npm test
    ```
 
 ## Troubleshooting
 If the installation fails:
 - Verify the repository was correctly cloned
 - Ensure all dependencies are properly installed
 - Check for any error messages during the installation process
 - Confirm your system meets all requirements