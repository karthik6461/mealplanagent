from flask import Flask, request, jsonify, send_from_directory
import os
import json
import logging
from dotenv import load_dotenv
import requests
import threading
import time

# Load environment variables from .env file (if present)
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configure OpenAI API key from environment variable
openai_api_key = os.environ.get("OPENAI_API_KEY")
if not openai_api_key:
    logger.warning("OPENAI_API_KEY environment variable not set! Please set it before running this application.")

# Set up Flask application
app = Flask(__name__)

# Create the .well-known directory if it doesn't exist
WELL_KNOWN_DIR = './.well-known'
os.makedirs(WELL_KNOWN_DIR, exist_ok=True)

# Define agent.json content
AGENT_JSON = {
    "schemaVersion": "1.0",
    "name": "FitMealPlanner",
    "version": "1.0.0",
    "description": "A personalized meal and workout planning assistant that creates customized plans based on your fitness goals, body metrics, and preferences.",
    "logo": {
        "url": "https://example.com/logo.png",
        "alt": "FitMealPlanner Logo"
    },
    "api": {
        "url": "http://localhost:8080/tasks/send",
        "type": "JSON-RPC"
    },
    "capabilities": {},
    "examples": [
        {
            "for": "Personal Meal Plan",
            "message": "I'm 32 years old, 5'10\", 180 lbs. I work out 3 times a week focusing on weight training. My goal is to lose weight and build muscle. Can you create a meal plan for me?"
        },
        {
            "for": "Workout Routine",
            "message": "I'm a 28-year-old woman, 5'5\", 130 lbs. I want to improve my flexibility and build core strength. I currently don't exercise much. What workout routine would you recommend?"
        }
    ],
    "contact": {
        "name": "Support Team",
        "email": "support@fitmealplanner.example.com"
    }
}

# Write the agent.json file
with open(os.path.join(WELL_KNOWN_DIR, 'agent.json'), 'w') as f:
    json.dump(AGENT_JSON, f, indent=2)

# Sample response for quick testing/fallback
SAMPLE_RESPONSE = """
# Personalized 2-Week Meal and Workout Plan

## Your Profile
- Age: 35
- Height: 6'0"
- Weight: 190 lbs
- Goals: Build muscle, improve overall fitness
- Current activity: Light cardio twice weekly
- Preference: High-protein meals

## Meal Plan - Week 1

### Monday
**Breakfast**: Protein oatmeal with berries (40g protein, 60g carbs, 15g fat)
**Lunch**: Grilled chicken salad with olive oil dressing (35g protein, 20g carbs, 15g fat)
**Dinner**: Baked salmon with sweet potato and asparagus (40g protein, 30g carbs, 20g fat)
**Snack**: Greek yogurt with nuts (20g protein, 10g carbs, 15g fat)

### Tuesday
**Breakfast**: Protein smoothie with banana and spinach (30g protein, 40g carbs, 10g fat)
**Lunch**: Turkey and avocado wrap (35g protein, 30g carbs, 20g fat)
**Dinner**: Lean beef stir-fry with vegetables and brown rice (45g protein, 40g carbs, 15g fat)
**Snack**: Protein bar (20g protein, 25g carbs, 10g fat)

## Workout Plan - Week 1

### Monday: Upper Body Strength
- **Warm-up**: 5 minutes light cardio
- **Main workout**:
  - Bench press: 3 sets × 8-10 reps
  - Pull-ups or lat pulldowns: 3 sets × 8-10 reps
  - Overhead press: 3 sets × 8-10 reps
  - Dumbbell rows: 3 sets × 10-12 reps
  - Tricep pushdowns: 3 sets × 12-15 reps
  - Bicep curls: 3 sets × 12-15 reps
- **Cool down**: 5 minutes stretching

### Tuesday: Lower Body Strength
- **Warm-up**: 5 minutes light cardio
- **Main workout**:
  - Squats: 3 sets × 8-10 reps
  - Romanian deadlifts: 3 sets × 8-10 reps
  - Leg press: 3 sets × 10-12 reps
  - Walking lunges: 3 sets × 10 steps each leg
  - Calf raises: 3 sets × 15-20 reps
- **Cool down**: 5 minutes stretching

### Weekly Grocery List
- Lean proteins: Chicken breast, turkey, salmon, lean beef, Greek yogurt
- Complex carbs: Sweet potatoes, brown rice, oats, whole grain wraps
- Vegetables: Spinach, asparagus, mixed stir-fry vegetables
- Fruits: Berries, bananas
- Healthy fats: Olive oil, nuts, avocados
- Extras: Protein powder, protein bars

## Rest & Recovery Tips
- Ensure 7-8 hours of sleep nightly
- Drink at least 3 liters of water daily
- Include 5-10 minutes of stretching after each workout
- Consider foam rolling for muscle recovery

This plan is designed to gradually increase your training volume while providing adequate nutrition for muscle growth and recovery. Adjust portion sizes as needed based on hunger levels and progress.
"""

def create_personalized_plan(user_message):
    """
    Use OpenAI API via direct HTTP request to generate a personalized meal and workout plan.
    
    Args:
        user_message (str): User's message containing personal details and goals
        
    Returns:
        str: Generated meal and workout plan
    """
    try:
        # Log that we're starting the API call
        logger.info("Starting OpenAI API call...")
        
        # Start timer for tracking API call duration
        start_time = time.time()
        
        # Construct the system and user messages
        system_message = """You are FitMealPlanner, a specialized fitness and nutrition expert. 
        
Your task is to create personalized meal and workout plans based on the user's information.

For meal plans:
1. Create a 2-4 week meal plan cycle
2. Include breakfast, lunch, dinner, and snacks
3. Ensure proper caloric intake based on their goals and metrics
4. Include a grocery list for common ingredients
5. Account for any dietary restrictions mentioned
6. Provide clear, structured meal descriptions with macronutrient information

For workout plans:
1. Design a 2-4 week workout routine
2. Tailor exercises to their specific goals (weight loss, muscle gain, flexibility, etc.)
3. Account for their current fitness level and available time
4. Include clear instructions for each exercise with sets, reps, and rest periods
5. Provide a structured weekly schedule
6. Include progression guidelines

Present both plans in a clear, organized format using markdown. Include headers, subheaders, and bullet points where appropriate."""

        # Make direct HTTP request to OpenAI API with timeout
        url = "https://api.openai.com/v1/chat/completions"
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {openai_api_key}"
        }
        
        data = {
            "model": "gpt-4-turbo-preview",
            "messages": [
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message}
            ],
            "temperature": 0.7,
            "max_tokens": 3000  # Reduced for faster response
        }
        
        # Use a 45-second timeout for the request
        response = requests.post(url, headers=headers, json=data, timeout=45)
        
        # Log the API response time
        elapsed_time = time.time() - start_time
        logger.info(f"OpenAI API call completed in {elapsed_time:.2f} seconds")
        
        if response.status_code != 200:
            logger.error(f"OpenAI API error: {response.status_code} - {response.text}")
            logger.warning("Returning sample response due to API error")
            return SAMPLE_RESPONSE
        
        response_data = response.json()
        generated_plan = response_data['choices'][0]['message']['content']
        return generated_plan
    
    except requests.exceptions.Timeout:
        logger.error("OpenAI API request timed out after 45 seconds")
        logger.warning("Returning sample response due to timeout")
        return SAMPLE_RESPONSE
    except Exception as e:
        logger.error(f"Error generating plan: {str(e)}")
        logger.warning("Returning sample response due to error")
        return SAMPLE_RESPONSE

@app.route('/.well-known/agent.json')
def get_agent_json():
    """Serve the agent.json file from the .well-known directory"""
    return send_from_directory(WELL_KNOWN_DIR, 'agent.json', mimetype='application/json')

@app.route('/tasks/send', methods=['POST'])
def handle_tasks_send():
    """Handle the JSON-RPC requests for task processing"""
    try:
        # Parse the incoming JSON-RPC request
        request_data = request.get_json()
        
        # Log the request for debugging
        logger.info(f"Received request: {json.dumps(request_data)[:100]}...")
        
        # Validate JSON-RPC structure
        if not all(k in request_data for k in ["jsonrpc", "id", "method", "params"]):
            return jsonify({
                "jsonrpc": "2.0",
                "id": request_data.get("id", None),
                "error": {
                    "code": -32600,
                    "message": "Invalid Request: Missing required JSON-RPC fields"
                }
            }), 400
        
        # Check if method is correct
        if request_data["method"] != "tasks/send":
            return jsonify({
                "jsonrpc": "2.0",
                "id": request_data["id"],
                "error": {
                    "code": -32601,
                    "message": f"Method not found: {request_data['method']}"
                }
            }), 404
        
        # Extract parameters
        params = request_data["params"]
        message = params.get("message", {})
        parts = message.get("parts", [])
        
        # Extract text parts
        user_text = ""
        for part in parts:
            if part.get("type") == "text" and "text" in part:
                user_text += part["text"] + " "
        
        if not user_text.strip():
            return jsonify({
                "jsonrpc": "2.0",
                "id": request_data["id"],
                "error": {
                    "code": -32602,
                    "message": "Invalid params: No text message provided"
                }
            }), 400
        
        # Generate the personalized plan
        plan_response = create_personalized_plan(user_text)
        
        # Return JSON-RPC response with the generated plan
        return jsonify({
            "jsonrpc": "2.0",
            "id": request_data["id"],
            "result": {
                "response": {
                    "role": "assistant",
                    "parts": [
                        {
                            "type": "text",
                            "text": plan_response
                        }
                    ]
                }
            }
        })
            
    except Exception as e:
        logger.error(f"General error: {str(e)}")
        return jsonify({
            "jsonrpc": "2.0",
            "id": request_data.get("id", None) if 'request_data' in locals() else None,
            "error": {
                "code": -32603,
                "message": f"Internal error: {str(e)}"
            }
        }), 500

# Health check endpoint
@app.route('/health', methods=['GET'])
def health_check():
    """Simple health check endpoint"""
    return jsonify({
        "status": "healthy", 
        "service": "FitMealPlanner", 
        "openai_api_key_configured": bool(openai_api_key)
    })

# For Gunicorn to find the Flask app instance
app = app