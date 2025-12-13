import httpx
import asyncio
import random
from datetime import datetime


BASE_URL = "http://localhost:8000/api"

# Configuration
NUM_ITERATIONS = 1000
CONTROL_CONVERSION_RATE = 0.35
TREATMENT_CONVERSION_RATE = 0.45


async def create_api_key(client):
    """Create and return an API key."""
    response = await client.post(f"{BASE_URL}/auth/keys", json={"name": "demo_key"})
    return response.json()["key"]


async def create_experiment(client, headers, timestamp):
    """Create an experiment with control and treatment variants."""
    experiment_name = f"checkout_flow_test_{timestamp}"

    # Create experiment
    response = await client.post(
        f"{BASE_URL}/experiments/",
        headers=headers,
        json={
            "name": experiment_name,
            "description": "Testing new checkout flow for conversion optimization"
        }
    )

    if response.status_code != 200:
        print(f"❌ Error creating experiment: {response.status_code}")
        print(f"Response: {response.text}")
        return None, None, None

    experiment = response.json()
    experiment_id = experiment["id"]

    # Get control variant
    response = await client.get(f"{BASE_URL}/experiments/{experiment_id}", headers=headers)
    experiment_detail = response.json()
    control_variant_id = experiment_detail["variants"][0]["id"]

    # Update control to 70%
    await client.put(
        f"{BASE_URL}/experiments/{experiment_id}/variants/{control_variant_id}",
        headers=headers,
        json={"percent_allocated": 70.0}
    )

    # Add treatment variant at 30%
    response = await client.post(
        f"{BASE_URL}/experiments/{experiment_id}/variants",
        headers=headers,
        json={"name": "new_checkout", "percent_allocated": 30.0}
    )
    treatment_variant_id = response.json()["id"]

    return experiment_id, control_variant_id, treatment_variant_id


async def create_users(client, headers, timestamp):
    """Create test users with different attributes."""
    users = []

    # 4 UK users (2 premium, 2 regular)
    for i in range(4):
        response = await client.post(
            f"{BASE_URL}/users/",
            headers=headers,
            json={
                "first_name": f"UK_User_{i+1}",
                "last_name": "Smith",
                "email": f"uk_user_{i+1}_{timestamp}@example.com",
                "country_code": "GB",
                "is_premium": i < 2
            }
        )
        users.append(response.json())

    # 3 Premium US users
    for i in range(3):
        response = await client.post(
            f"{BASE_URL}/users/",
            headers=headers,
            json={
                "first_name": f"Premium_User_{i+1}",
                "last_name": "Johnson",
                "email": f"premium_{i+1}_{timestamp}@example.com",
                "country_code": "US",
                "is_premium": True
            }
        )
        users.append(response.json())

    # 3 Regular users from various countries
    countries = ["CA", "DE", "AU"]
    for i in range(3):
        response = await client.post(
            f"{BASE_URL}/users/",
            headers=headers,
            json={
                "first_name": f"User_{i+1}",
                "last_name": "Doe",
                "email": f"user_{i+1}_{timestamp}@example.com",
                "country_code": countries[i],
                "is_premium": False
            }
        )
        users.append(response.json())

    return users


async def create_segments(client, headers, timestamp, users):
    """Create rule-based and manual segments."""
    # UK users segment (rule-based)
    response = await client.post(
        f"{BASE_URL}/segments/",
        headers=headers,
        json={
            "name": f"uk_users_{timestamp}",
            "description": "Users from the United Kingdom",
            "rules": {"country_code": "GB"}
        }
    )
    uk_segment_id = response.json()["id"]

    # Premium users segment (rule-based)
    response = await client.post(
        f"{BASE_URL}/segments/",
        headers=headers,
        json={
            "name": f"premium_users_{timestamp}",
            "description": "Premium subscribers",
            "rules": {"is_premium": True}
        }
    )
    premium_segment_id = response.json()["id"]

    # VIP test group (manual assignment)
    explicit_users = [users[1], users[3], users[7]]
    response = await client.post(
        f"{BASE_URL}/segments/",
        headers=headers,
        json={
            "name": f"vip_test_group_{timestamp}",
            "description": "Hand-picked VIP users for testing"
        }
    )
    vip_segment_id = response.json()["id"]

    # Assign users to VIP segment
    for user in explicit_users:
        await client.post(
            f"{BASE_URL}/segments/assign-user",
            headers=headers,
            json={"user_id": user["id"], "segment_id": vip_segment_id}
        )

    return uk_segment_id, premium_segment_id, vip_segment_id, explicit_users


async def assign_segments_to_experiment(client, headers, experiment_id, segment_ids):
    """Assign all segments to the experiment."""
    for segment_id, _ in segment_ids:
        await client.post(
            f"{BASE_URL}/segments/assign-experiment",
            headers=headers,
            json={"experiment_id": experiment_id, "segment_id": segment_id}
        )


async def simulate_user_interactions(client, headers, experiment_id, users, treatment_variant_id):
    """Simulate user sessions with page views and conversions."""
    user_variant_map = {}

    for _ in range(NUM_ITERATIONS):
        user = random.choice(users)
        user_id = user["id"]

        # Check eligibility
        response = await client.post(
            f"{BASE_URL}/experiments/check-eligibility",
            headers=headers,
            json={"user_id": user_id, "experiment_ids": [experiment_id]}
        )
        eligibility = response.json()

        if str(experiment_id) not in eligibility["eligible_experiment_ids"]:
            continue

        variant_id = eligibility["eligible_experiment_ids"][str(experiment_id)]["variant_id"]

        if user_id not in user_variant_map:
            user_variant_map[user_id] = variant_id

        # Log page view event
        await client.post(
            f"{BASE_URL}/events/",
            headers=headers,
            json={
                "user_id": user_id,
                "experiment_id": experiment_id,
                "variant_id": variant_id,
                "type": "page_view",
                "properties": {"page": "checkout"}
            }
        )

        # Log conversion event based on variant-specific conversion rate
        conversion_probability = TREATMENT_CONVERSION_RATE if variant_id == treatment_variant_id else CONTROL_CONVERSION_RATE
        if random.random() < conversion_probability:
            await client.post(
                f"{BASE_URL}/events/",
                headers=headers,
                json={
                    "user_id": user_id,
                    "experiment_id": experiment_id,
                    "variant_id": variant_id,
                    "type": "conversion",
                    "properties": {
                        "amount": round(random.uniform(20, 200), 2),
                        "currency": "USD"
                    }
                }
            )

    return user_variant_map


async def display_event_logs(client, headers, experiment_id, treatment_variant_id):
    """Query and display event logs with various filters."""
    print("\n" + "=" * 80)
    print("EVENT LOGS")
    print("=" * 80)

    # All events
    response = await client.post(f"{BASE_URL}/events/{experiment_id}", headers=headers, json={})
    all_events = response.json()
    print(f"\n[Query 1] All events for the experiment:")
    print(f"Total events: {len(all_events)}")

    event_types = {}
    for event in all_events:
        event_type = event["type"]
        event_types[event_type] = event_types.get(event_type, 0) + 1

    print("Event breakdown:")
    for event_type, count in event_types.items():
        print(f"  - {event_type}: {count}")

    # Conversion events only
    response = await client.post(
        f"{BASE_URL}/events/{experiment_id}",
        headers=headers,
        json={"event_types": ["conversion"]}
    )
    conversion_events = response.json()
    print(f"\n[Query 2] Conversion events only:")
    print(f"Total conversions: {len(conversion_events)}")

    print("\nSample conversion events:")
    for event in conversion_events[:3]:
        print(f"  - User: {event['user_id'][:12]}..., Amount: ${event['properties'].get('amount', 'N/A')}")

    # Treatment variant events only
    response = await client.post(
        f"{BASE_URL}/events/{experiment_id}",
        headers=headers,
        json={"variant_id": treatment_variant_id}
    )
    treatment_events = response.json()
    print(f"\n[Query 3] Events for treatment variant only:")
    print(f"Treatment variant events: {len(treatment_events)}")


async def display_experiment_results(client, headers, experiment_id):
    """Display statistical results of the experiment."""
    print("\n" + "=" * 80)
    print("EXPERIMENT RESULTS")
    print("=" * 80)

    response = await client.post(
        f"{BASE_URL}/experiments/{experiment_id}/results",
        headers=headers,
        json={
            "conversion_event_type": "conversion",
            "confidence_level": 0.95,
            "significance_threshold": 0.05
        }
    )
    results = response.json()

    print(f"\nExperiment: {results['experiment_name']}")
    print(f"Conversion Event: {results['conversion_event_type']}")
    print(f"Confidence Level: {results['confidence_level'] * 100}%")
    print(f"Significance Threshold: {results['significance_threshold']}")

    print("\n" + "-" * 80)
    print("VARIANT PERFORMANCE")
    print("-" * 80)

    for variant in results["variants"]:
        print(f"\n{variant['variant_name'].upper()}")
        print(f"  Total Sessions: {variant['total_users']}")
        print(f"  Conversions: {variant['conversions']}")
        print(f"  Conversion Rate: {variant['conversion_rate']}%")
        print(f"  Confidence Interval: [{variant['confidence_interval']['lower']}%, {variant['confidence_interval']['upper']}%]")

        if not variant['is_control']:
            print(f"  P-value: {variant.get('p_value', 'N/A')}")
            print(f"  Statistically Significant: {variant.get('is_significant', False)}")
            print(f"  Relative Uplift: {variant.get('relative_uplift', 0)}%")

    if results.get("winner"):
        print("\n" + "=" * 80)
        print(f"🏆 WINNER: {results['winner']['variant_name']}")
        print(f"   Relative Uplift: {results['winner']['relative_uplift']}%")
        print("=" * 80)
    else:
        print("\n" + "=" * 80)
        print("No statistically significant winner yet")
        print("=" * 80)


async def display_segment_analysis(user_variant_map, users, explicit_users, control_variant_id):
    """Display which users participated and their segment memberships."""
    print("\n" + "=" * 80)
    print("SEGMENT ANALYSIS")
    print("=" * 80)

    print("\nUsers who participated in the experiment:")
    for user_id, variant_id in user_variant_map.items():
        user = next(u for u in users if u["id"] == user_id)
        variant_name = "control" if variant_id == control_variant_id else "new_checkout"

        segments = []
        if user["country_code"] == "GB":
            segments.append("UK")
        if user["is_premium"]:
            segments.append("Premium")
        if any(u["id"] == user_id for u in explicit_users):
            segments.append("VIP")

        segment_str = ", ".join(segments) if segments else "None"
        print(f"  {user['email']:40} | Variant: {variant_name:12} | Segments: {segment_str}")


async def main():
    async with httpx.AsyncClient(timeout=30.0) as client:
        print("=" * 80)
        print("EXPERIMENTATION PLATFORM DEMO")
        print("=" * 80)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # STEP 1: Create API Key
        print("\n[STEP 1] Creating API key...")
        api_key = await create_api_key(client)
        print(f"✓ API Key created: {api_key[:20]}...")
        headers = {"Authorization": f"Bearer {api_key}"}

        # STEP 2-4: Create Experiment with Variants
        print("\n[STEP 2] Creating experiment...")
        experiment_id, control_variant_id, treatment_variant_id = await create_experiment(client, headers, timestamp)
        if not experiment_id:
            return
        print(f"✓ Experiment created with ID: {experiment_id}")
        print("✓ Control variant: 70%")
        print("✓ Treatment variant: 30%")

        # STEP 5: Create Users
        print("\n[STEP 3] Creating 10 users...")
        users = await create_users(client, headers, timestamp)
        print(f"✓ Created {len(users)} users:")
        print(f"  - 4 UK users (2 premium, 2 regular)")
        print(f"  - 3 Premium US users")
        print(f"  - 3 Regular users from various countries")

        # STEP 6: Create Segments
        print("\n[STEP 4] Creating segments...")
        uk_segment_id, premium_segment_id, vip_segment_id, explicit_users = await create_segments(
            client, headers, timestamp, users
        )
        print(f"✓ Segment 1: 'uk_users' (rule-based: country_code=GB)")
        print(f"✓ Segment 2: 'premium_users' (rule-based: is_premium=True)")
        print(f"✓ Segment 3: 'vip_test_group' (manual: {len(explicit_users)} users)")

        # STEP 7: Assign Segments to Experiment
        print("\n[STEP 5] Assigning segments to experiment...")
        segment_ids = [
            (uk_segment_id, "uk_users"),
            (premium_segment_id, "premium_users"),
            (vip_segment_id, "vip_test_group")
        ]
        await assign_segments_to_experiment(client, headers, experiment_id, segment_ids)
        print(f"✓ Assigned 3 segments to experiment")

        # STEP 8: Simulate User Interactions
        print(f"\n[STEP 6] Simulating {NUM_ITERATIONS} user interactions...")
        print(f"  Control conversion rate: {CONTROL_CONVERSION_RATE * 100}%")
        print(f"  Treatment conversion rate: {TREATMENT_CONVERSION_RATE * 100}%")
        user_variant_map = await simulate_user_interactions(
            client, headers, experiment_id, users, treatment_variant_id
        )
        print(f"✓ Completed {NUM_ITERATIONS} interactions")
        print(f"✓ {len(user_variant_map)} unique users participated")

        control_count = sum(1 for v in user_variant_map.values() if v == control_variant_id)
        treatment_count = sum(1 for v in user_variant_map.values() if v == treatment_variant_id)
        print(f"  - Control variant: {control_count} users")
        print(f"  - Treatment variant: {treatment_count} users")

        # STEP 9: View Event Logs
        await display_event_logs(client, headers, experiment_id, treatment_variant_id)

        # STEP 10: View Experiment Results
        await display_experiment_results(client, headers, experiment_id)

        # STEP 11: Show Segment Analysis
        await display_segment_analysis(user_variant_map, users, explicit_users, control_variant_id)

        print("\n" + "=" * 80)
        print("DEMO COMPLETED SUCCESSFULLY!")
        print("=" * 80)


if __name__ == "__main__":
    print("\nStarting Experimentation Platform Demo...")
    print("Make sure the server is running: docker compose up")
    print()

    try:
        asyncio.run(main())
    except httpx.ConnectError:
        print("\n❌ ERROR: Could not connect to the server.")
        print("Please ensure the server is running with: docker compose up")
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
