# API Description

## Auth

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

## Experiment Module

### Create an Experiment

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

### Get All Experiments

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

### Get One Experiment

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

### Add an Experiment Variant

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

### Update an Experiment Variant

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

### Check Experiment Eligibility and Get Variant

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

### Get Experiment Results

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

## Segment Module

### Create a Segment

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

### Get All Segments

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

### Get Segment By Id

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

### Edit Segment

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

### Assign User to a Segment

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

### Assign Segment to an Experiment

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

### Remove Segment from an Experiment

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

### Create a User

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

### Get Users

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

### Get User by Id

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

### Update User

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

### Delete User

```
DELETE localhost:8000/api/users/{user_id}
RESPONSE {
  "message": "User deleted successfully"
}

Example: curl -X DELETE http://localhost:8000/api/users/user_12345 \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

## Events

### Create an Event

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

### Get Events

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
