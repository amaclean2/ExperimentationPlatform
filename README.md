# Experimentation Platform

## Get started

Clone this repo and run `docker compose up --build` to build and launch the application. Get `localhost:8000/api/experiments` to view a list of current experiments.

To run tests, run `docker compose exec fastapi pytest`

## Description

Started off with the project, defined in `ProjectDefinition.md`, to build an experimentation platform to test different flows in order to track app growth There's four main parts to this: experiments, variants, segments, and users.

This implementation goes beyond the required endpoints prodivded in the project definition, but I believe these are the minimum to enable full working behavior.

There's a framework included for building user interface views to make it easier to manage experiments, but implementing that was taking too much work. Further efforts on that can be made later. Depending on integrations, this is probably the next most useful thing to finish. It enables a user to visually ingest the information about their experiments.

There's two results endpoints, `GET events/`, and `GET /{experiment_id}/results`. The first enables tracking event data related to an experiment in a way that can be output to a graph or other UI chart.

The second gives statistical information about the experiment including measured events, confidence levels, significance thresholds, and variant winners. More observations can be added as requirements change.

Caching happens on experiments and segments, so when a user needs to access their variant, the request is as fast as possible.

I changed some of the endpoints slightly from the project definition, because I felt like these were more representative places for the application logic to go, and I added a few more endpoints than required.

### Experiment

Each experiment is a layer containing statistics about some functionality in a codebase about which version of a block of code performs differently according to defined criteria.

### Variant

A variant is a version of the code to be tested against the control. The control is usually defined as the standard code as it exists in production. Each variant on top of that is some alteration intended to test metrics such as conversion, signup, clicks or some traffic behavior.

### Segment

A segment is a group of the population eligible to be in the experiment, maybe it's mobile users, users in Argentina, or a predefined set of assigned user_ids.

### User

A user is the actor being tested on. They are the ones specifically interacting with the application and generating events.

### Events

Lastly events are what's logged by users interacting with the application. They're used to create metrics about the experiment's efficacy.

## Workflow

### Auth

An auth token is generated allowing the controller of the experiment access to platform APIs

```
POST localhost:8000/api/auth/keys
BODY { name: str }
RESPONSE {
  id: int
  key: str
  name: str
  is_active: bool
  created_at: datetime
  last_used_at: Optional[datetime]
}

Example: curl -X POST http://localhost:8000/api/auth/keys \
  -H "Content-Type: application/json" \
  -d '{"name": "my_api_key"}'
```

Once an auth token is acquired, it can be used to access the rest of the APIs by including in the header `Headers: { Authorization: "Bearer {token}" }`

All the tokens can be seen at `GET localhost:8000/api/auth/keys`. This endpoint isn't secured which would expose all the API keys. In a production environment, this endpoint shouldn't be exposed.

```
Example: curl http://localhost:8000/api/auth/keys
```

A key can be removed at `DELETE localhost:8000/api/auth/keys/{key_id}`. Again, this endpoint isn't secured.

```
Example: curl -X DELETE http://localhost:8000/api/auth/keys/123
```

### Experiment Module

**Create an Experiment**

```
POST localhost:8000/api/experiments
BODY {
  name: str
  description: Optional[str] = None
}
RESPONSE {
  id: int
  name: str
  description: Optional[str]
  status: ExperimentStatus
  created_at: datetime
  started_at: Optional[datetime]
  ended_at: Optional[datetime]
}

Example: curl -X POST http://localhost:8000/api/experiments \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -d '{"name": "new_checkout_flow"}'
```

**Get All Experiments**

```
GET localhost:8000/api/experiments
RESPONSE {
  id: int
  name: str
  description: Optional[str]
  status: ExperimentStatus
  created_at: datetime
  started_at: Optional[datetime]
  ended_at: Optional[datetime]
}[]

Example: curl http://localhost:8000/api/experiments \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

**Get One Experiment**

```
GET localhost:8000/api/experiments/{experiment_id}
RESPONSE {
  id: int
  name: str
  description: Optional[str]
  status: ExperimentStatus
  created_at: datetime
  started_at: Optional[datetime]
  ended_at: Optional[datetime]
  variants: List[VariantResponse] = []
  segments: List['SegmentResponse'] = []
}

Example: curl http://localhost:8000/api/experiments/{experiment_id} \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

**Add an Experiment Variant**

```
POST localhost:8000/api/experiments/{experiment_id}/variants
BODY {
  name: str
  percent_allocated: float
}
RESPONSE {
  id: int
  experiment_id: int
  name: str
  percent_allocated: float
  created_at: datetime
}

Example: curl -X POST http://localhost:8000/api/experiments/1/variants \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -d '{"name": "control", "percent_allocated": 50.0}'
```

**Update an experiment variant**

```
PUT localhost:8000/api/experiments/{experiment_id}/variants/{variant_id}
BODY {
  name: Optional[str] = None
  percent_allocated: Optional[float] = None
}
RESPONSE {
  id: int
  experiment_id: int
  name: str
  percent_allocated: float
  created_at: datetime
}

Example: curl -X PUT http://localhost:8000/api/experiments/1/variants/2 \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -d '{"percent_allocated": 60.0}'
```

**Check Experiment Eligibility and Get Variant**

> [!NOTE]
> When a user interacts with a workflow, there may be multiple experiments they're eligible for. This checks against all possible experiments, and returns a dictionary with the eligible experiments and the assigned variant for each. Each variant is calculated based on a hash of the user_id and experiment_id so a user will always be in the same variant

```
POST localhost:8000/api/experiments/check-eligibility
BODY {
  user_id: str
  experiment_ids: List[int]
}
RESPONSE {
  eligible_experiment_ids: dict[experiment_id, dict[variant_id, int]]
}

Example: curl -X POST http://localhost:8000/api/experiments/check-eligibility \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -d '{"user_id": "user_12345", "experiment_ids": [1, 2, 3]}'
```

**Get experiment results**

> [!NOTE]
> To get individual data for an experiment, go to the section [Get Events](https://github.com/amaclean2/ExperimentationPlatform/blob/main/README.md#events-1). Here is a basic output of standard statistical outputs from an experiment. To get more details, more requirements would have to be added.

```
POST localhost:8000/api/experiments/{experiment_id}/results
BODY {
  conversion_event_type: str = "conversion"
  confidence_level: float = 0.95
  significance_threshold: float = 0.05
}
RESPONSE {
  experiment_id: int
  experiment_name: str
  conversion_event_type: str
  confidence_level: float
  significance_threshold: float
  variants: List[VariantResult]
  winner: Optional[Winner] = None
}

Example: curl -X POST http://localhost:8000/api/experiments/1/results \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -d '{"conversion_event_type": "conversion", "confidence_level": 0.95}'
```

### Segment Module

**Create a Segment**

> [!NOTE]
> Rules would be something like `{ country_code: "US" }`, or `{ is_premium: true }`

```
POST localhost:8000/api/segments
BODY {
  name: str
  description: Optional[str] = None
  rules: Optional[dict] = None
}
RESPONSE {
  id: int
  name: str
  description: Optional[str]
  rules: Optional[dict]
  created_at: datetime
}

Example: curl -X POST http://localhost:8000/api/segments \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -d '{"name": "US Premium Users", "description": "Premium users from the US", "rules": {"country_code": "US", "is_premium": true}}'
```

**Get All Segments**

```
GET localhost:8000/api/segments
RESPONSE List[{
  id: int
  name: str
  description: Optional[str]
  rules: Optional[dict]
  created_at: datetime
}]

Example: curl http://localhost:8000/api/segments \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

**Get Segment By Id**

```
GET localhost:8000/api/segments/{segment_id}
RESPONSE {
  id: int
  name: str
  description: Optional[str]
  rules: Optional[dict]
  created_at: datetime
}

Example: curl http://localhost:8000/api/segments/1 \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

**Edit Segment**

```
PUT localhost:8000/api/segments/{segment_id}
BODY {
  name: Optional[str] = None
  description: Optional[str] = None
  rules: Optional[dict] = None
}
RESPONSE {
  id: int
  name: str
  description: Optional[str]
  rules: Optional[dict]
  created_at: datetime
}

Example: curl -X PUT http://localhost:8000/api/segments/1 \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -d '{"description": "Updated description"}'
```

**Assign User to a Segment**

```
POST localhost:8000/api/segments/assign-user
BODY {
  user_id: str
  segment_id: int
}
RESPONSE {
  "message": "User assigned to segment successfully"
}

Example: curl -X POST http://localhost:8000/api/segments/assign-user \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -d '{"user_id": "user_12345", "segment_id": 1}'
```

**Assign Segment to an Experiment**

```
POST localhost:8000/api/segments/assign-experiment
BODY {
  experiment_id: int
  segment_id: int
}
RESPONSE {
  "message": "Segment assigned to experiment successfully"
}

Example: curl -X POST http://localhost:8000/api/segments/assign-experiment \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -d '{"experiment_id": 1, "segment_id": 1}'
```

**Remove Segment from an Experiment**

```
DELETE localhost:8000/api/segments/unassign-experiment
BODY {
  experiment_id: int
  segment_id: int
}
RESPONSE {
  "message": "Segment removed from experiment successfully"
}

Example: curl -X DELETE http://localhost:8000/api/segments/unassign-experiment \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -d '{"experiment_id": 1, "segment_id": 1}'
```

### Users

> [!NOTE]
> For the case of this project, we're creating users, but in a production situation, users would already have been created in the client's application and we would just access whatever data is necessary to log the appropriate events on experiments

**Create a User**

```
POST localhost:8000/api/users/
BODY {
  first_name: str
  last_name: str
  email: EmailStr
  is_premium: bool = False
  country_code: Optional[str] = None
}
RESPONSE {
  id: str
  first_name: str
  last_name: str
  email: str
  is_premium: bool
  country_code: Optional[str]
  created_at: datetime
}

Example: curl -X POST http://localhost:8000/api/users/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -d '{"first_name": "John", "last_name": "Doe", "email": "john.doe@example.com", "is_premium": true, "country_code": "US"}'
```

**Get Users**

```
GET localhost:8000/api/users/
RESPONSE List[{
  id: str
  first_name: str
  last_name: str
  email: str
  is_premium: bool
  country_code: Optional[str]
  created_at: datetime
}]

Example: curl http://localhost:8000/api/users/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

**Get User by Id**

```
GET localhost:8000/api/users/{user_id}
RESPONSE {
  id: str
  first_name: str
  last_name: str
  email: str
  is_premium: bool
  country_code: Optional[str]
  created_at: datetime
}

Example: curl http://localhost:8000/api/users/user_12345 \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

**Update User**

> `is_premium` and `country_code` are example rules that a user might be filtered by in a segment

```
PUT localhost:8000/api/users/{user_id}
BODY {
  first_name: Optional[str] = None
  last_name: Optional[str] = None
  email: Optional[EmailStr] = None
  is_premium: Optional[bool] = None
  country_code: Optional[str] = None
}
RESPONSE {
  id: str
  first_name: str
  last_name: str
  email: str
  is_premium: bool
  country_code: Optional[str]
  created_at: datetime
}

Example: curl -X PUT http://localhost:8000/api/users/user_12345 \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -d '{"is_premium": true, "country_code": "CA"}'
```

**Delete User**

```
DELETE localhost:8000/api/users/{user_id}
RESPONSE {
  "message": "User deleted successfully"
}

Example: curl -X DELETE http://localhost:8000/api/users/user_12345 \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

### Events

**Create an Event**

```
POST localhost:8000/api/events
BODY {
  user_id: str
  experiment_id: Optional[int] = None
  variant_id: Optional[int] = None
  type: str
  properties: Optional[dict] = None
}
RESPONSE {
  id: int
  user_id: str
  experiment_id: Optional[int]
  variant_id: Optional[int]
  type: str
  timestamp: datetime
  properties: Optional[dict]
}

Example: curl -X POST http://localhost:8000/api/events \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -d '{"user_id": "user_12345", "experiment_id": 1, "variant_id": 2, "type": "conversion", "properties": {"value": 99.99}}'
```

**Get Events**

> [!NOTE]
> This endpoint allows filtering events by various criteria including time range, variant, event types, and specific users.

```
POST localhost:8000/api/events/{experiment_id}
BODY {
  start_time: Optional[datetime]
  end_time: Optional[datetime]
  variant_id: Optional[int]
  event_types: Optional[List[string]]
  user_ids: Optional[List[string]]
}
RESPONSE List[{
  id: int
  user_id: str
  experiment_id: Optional[int]
  variant_id: Optional[int]
  type: str
  timestamp: datetime
  properties: Optional[dict]
}]

Example: curl -X POST http://localhost:8000/api/events/1 \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -d '{"variant_id": 2, "event_types": ["click", "conversion"]}'
```

## Usage

To get the variants applicable to a specific user once in a flow, call the `/check-eligibility` endpoint with all possible experiments in that workflow.

```
curl -X POST http://localhost:8000/api/experiments/check-eligibility \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -d '{"user_id": "user_12345", "experiment_ids": [1, 2, 3]}'
```

This will return a dictionary with all the eligible experiments as keys, and objects as values containing the corresponding variant per the user. In the tested application, different workflows can be called depending on variant. In each flow, at the desired action, an event can be triggered.

```
curl -X POST http://localhost:8000/api/events \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -d '{"user_id": "user_12345", "experiment_id": 1, "variant_id": 2, "type": "conversion", "properties": {"value": 99.99}}'
```

These events can then be accumulated and watched from the `GET /events` endpoint.

```
curl -X POST http://localhost:8000/api/events/1 \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -d '{"variant_id": 2, "event_types": ["click", "conversion"]}'
```
