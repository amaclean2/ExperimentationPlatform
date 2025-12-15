# Experimentation Platform

## Get started

Clone this repo and run `docker compose up --build` to build and launch the application.

Get `localhost:8000/api/experiments` to view a list of current experiments.

To run tests, run `docker compose exec fastapi pytest`

To run an example run `python example.py`

## Description

Started off with the project, defined in `ProjectDefinition.md`, to build an experimentation platform to test different flows in order to track app growth There's four main parts to this: experiments, variants, segments, and users.

This implementation goes beyond the required endpoints prodivded in the project definition, but I believe these are the minimum to enable full working behavior.

There's a framework included for building user interface views to make it easier to manage experiments, but implementing that was taking too much work. Further efforts on that can be made later. Depending on integrations, this is probably the next most useful thing to finish. It enables a user to visually ingest the information about their experiments.

There's two results endpoints, `GET events/`, and `GET /{experiment_id}/results`. The first enables tracking event data related to an experiment in a way that can be output to a graph or other UI chart.

The second gives statistical information about the experiment including measured events, confidence levels, significance thresholds, and variant winners. More observations can be added as requirements change.

Caching happens on experiments and segments, so when a user needs to access their variant, the request is as fast as possible.

Variants have an `enabled` boolean so a variant could be turned on or off from the api.

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

## Changes

- I moved `GET /experiments/{id}/assignment/{user_id}` to `POST /experiments/check-eligibility`. The new endpoint accomodates making sure the user is in the experiment as well as getting the variant.
- I moved individual result data from `GET /experiments/{experiment_id}/results` to `GET /events/{event_id}`. This way individual event data is returned from the get event endpoint, and statistical data is returned from the experiments endpoint

## Usage

APIs are documented in APIDoc.md

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
