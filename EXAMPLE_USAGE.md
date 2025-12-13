# Example Usage Script

This directory contains `example.py`, a comprehensive demonstration of the Experimentation Platform API.

1. **Authentication**: Creates an API key
2. **Experiment Setup**: Creates an experiment with two variants (70% control, 30% treatment)
3. **User Creation**: Creates 10 users with different attributes:
   - 3 UK users (1 is also premium)
   - 2 Premium US users
   - 5 Regular users from various countries
4. **Segmentation**: Creates and assigns three segments:
   - UK users (rule-based: `country_code = "GB"`)
   - Premium users (rule-based: `is_premium = True`)
   - VIP test group (manual assignment of 3 specific users)
5. **User Interactions**: Simulates 50 random user interactions
   - Checks eligibility for each user
   - Logs page view events
   - Randomly generates conversion events (40% chance)
6. **Analysis**: Displays:
   - Event logs with various filters
   - Statistical experiment results
   - Segment participation breakdown

## How to Run

### Prerequisites

Make sure the server is running:

```bash
docker compose up --build
```

### Run the Example

```bash
python example.py
```
