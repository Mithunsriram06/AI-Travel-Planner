# 🎒 AI Travel Planner for Students

An intelligent, web-based travel planning application designed specifically for students. By combining Generative AI with open-source mapping technologies, this app creates highly personalized, budget-conscious travel itineraries and visualizes multi-stop routes on an interactive map.

## 🌟 Features

* **Dual Planning Modes:** Choose between "Plan for Budget" (find destinations that fit your wallet) or "Plan for Location" (get routes and plans for a specific destination).
* **Interactive Map Integration:** Visualizes travel routes, starting points, and stopovers using OpenStreetMap (OSRM) and Folium.
* **Click-to-Select Routing:** Users can dynamically click on map markers to select their preferred route, instantly generating a detailed itinerary.
* **Conversational Refinement:** An integrated chatbot interface allows users to ask the AI to modify the generated itinerary (e.g., "Make day 2 cheaper" or "Swap the museum for a beach").
* **Student-Centric Constraints:** The AI engine is specifically engineered to prioritize hostels, public transport, cheap eats, and currently open attractions, complete with booking links.

## ✅ Benefits

* **Cost-Effective Planning:** Solves the problem of generic travel apps by strictly adhering to student budget constraints.
* **Saves Time:** Automates the hours usually spent researching routes, estimating costs, and finding affordable accommodations.
* **100% Free Tech Stack:** Built entirely on free and open-source APIs (Streamlit, Gemini API, Nominatim, OSRM), making it highly accessible and scalable without overhead costs.

## ⚠️ Drawbacks & Limitations

* **API Timeouts:** Because the app relies on free, public routing APIs (like Nominatim and OSRM), heavy traffic or poor internet connections can occasionally cause map loading delays or timeouts.
* **LLM Hallucinations:** While heavily prompted to be accurate, the Gemini AI may occasionally suggest places that are temporarily closed or slightly miscalculate real-time travel distances.
* **No Real-Time Pricing:** The budget estimates are based on the AI's trained data, not real-time live scraping of flight or hotel prices.

## 🚀 How to Run Locally

Follow these steps to run the application on your own machine.

### 1. Prerequisites
Ensure you have Python 3.8+ installed on your system. You will also need a free API key from Google AI Studio.

### 2. Setup the Environment
Clone this repository or download the project files, then open your terminal in the project directory.

Install the required Python libraries using the following command:
```bash
pip install -r requirements.txt

### 3. Configure Your API Key
For security, the API key is handled via environment variables.

Create a new file in the root directory named exactly .env

Add your Gemini API key to the file in this format:

Plaintext
GEMINI_API_KEY="your_actual_api_key_here"
### 4. Run the Application
Start the Streamlit server by running:

Bash
streamlit run app.py
The application will automatically open in your default web browser at http://localhost:8501.
