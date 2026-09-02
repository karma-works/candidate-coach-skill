# Candidate Coach Configuration Schema

## User-level config

Store the shared pointer at `~/.codex/candidate-coach/config.yaml`:

```yaml
schema_version: 1
knowledge_base: "/absolute/path/to/candidate-knowledge-base"
search_profile: "../skills/candidate-coach-configuration/search-profile.yaml"
application_tracker: null
```

Rules:

- `schema_version` must be `1`.
- `knowledge_base` is required, absolute, user-confirmed, and readable. It may be any folder; never infer a candidate-specific default.
- `search_profile` is required and must point to `search-profile.yaml` in the installed `candidate-coach-configuration` skill directory. An absolute path is allowed; otherwise resolve it against the directory containing this user-level config. The relative default above resolves from `~/.codex/candidate-coach/` to `~/.codex/skills/candidate-coach-configuration/`.
- `application_tracker` is optional. An absolute path is allowed; otherwise resolve it under `knowledge_base`. A null value disables application tracking.
- Unknown keys should be preserved during updates so future schema extensions are not lost.

## Search profile

The configured search profile is candidate-approved preference data, not part of the evidence knowledge base. Store it as `<candidate-coach-configuration skill directory>/search-profile.yaml`, create it from `assets/search-profile.yaml`, and preserve unknown fields.

Required for job discovery:

- `schema_version: 1`
- `location`: commute origin at city/municipality granularity unless the user explicitly wants a more precise address.
- `target_roles`: one or more ordered role titles or role families.
- `skills`: evidence-backed skills to prioritize.

Supported optional fields:

- `name`
- `max_commute_minutes`
- `max_car_distance_km`
- `work_modes`: values from `Remote-only`, `Hybrid`, and `In-office`
- `career_directions`: values from `vertical_progression`, `lateral_movement`, `more_responsibility`, and `comparable_role`
- `languages`
- `work_authorization`
- `salary_minimum` and `currency`
- `must_haves`, `nice_to_haves`, and `exclusions`
- `preferred_locations` and `excluded_locations`
- `result_limit` (default `5` when omitted)

Candidate facts in this profile must agree with evidence in the separate knowledge base. Preferences such as commute limit or desired work mode do not need employment evidence, but they must come from the user rather than inference. Candidate Coach must never include this profile in evidence retrieval merely because it is readable.
