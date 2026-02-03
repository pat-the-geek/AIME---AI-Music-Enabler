# Advanced Analytics API Documentation

## Overview

The Advanced Analytics module provides comprehensive music listening analysis with temporal filtering, discovery tracking, comparative analysis, and mood-based insights.

## Base URL
```
/api/v1/analytics
```

## Endpoints

### 1. Advanced Statistics
**Endpoint**: `GET /advanced-stats`

Retrieves comprehensive listening statistics for a specified date range.

**Query Parameters**:
- `start_date` (string, ISO 8601) - Start date for analysis
- `end_date` (string, ISO 8601) - End date for analysis

**Response**:
```json
{
  "period": {
    "start_date": "2025-01-01",
    "end_date": "2025-01-31",
    "total_tracks": 450,
    "avg_per_day": 14.5,
    "unique_days": 31
  },
  "top_artists": [
    {
      "name": "Artist Name",
      "count": 45
    }
  ],
  "top_albums": [
    {
      "name": "Album Name",
      "count": 23
    }
  ],
  "top_genres": [
    {
      "genre": "Rock",
      "count": 120
    }
  ],
  "mood_distribution": {
    "energetic": 150,
    "calm": 100,
    "melancholic": 150,
    "joyful": 50
  },
  "monthly_trend": {
    "2025-01": 450
  },
  "total_hours": 18.5
}
```

**Example**:
```bash
curl "http://localhost:8000/api/v1/analytics/advanced-stats?start_date=2025-01-01&end_date=2025-01-31"
```

---

### 2. Discovery Statistics
**Endpoint**: `GET /discovery-stats`

Tracks new artist discovery and listening patterns over a specified period.

**Query Parameters**:
- `days` (integer, default: 30) - Number of days to analyze

**Response**:
```json
{
  "total_new_artists": 12,
  "new_artists": [
    {
      "name": "New Artist",
      "first_listened": "2025-01-15T10:30:00Z",
      "count": 5
    }
  ],
  "most_replayed": [
    {
      "name": "Artist Name",
      "count": 45
    }
  ]
}
```

**Example**:
```bash
curl "http://localhost:8000/api/v1/analytics/discovery-stats?days=30"
```

---

### 3. Period Comparison
**Endpoint**: `GET /comparison`

Compares listening patterns between two time periods.

**Query Parameters**:
- `period1_start` (string, ISO 8601) - Start of first period
- `period1_end` (string, ISO 8601) - End of first period
- `period2_start` (string, ISO 8601) - Start of second period
- `period2_end` (string, ISO 8601) - End of second period

**Response**:
```json
{
  "period1": {
    "label": "Jan 1-15",
    "total_tracks": 200,
    "total_hours": 8.5,
    "unique_artists": 25
  },
  "period2": {
    "label": "Jan 16-31",
    "total_tracks": 250,
    "total_hours": 10.2,
    "unique_artists": 30
  },
  "changes": {
    "tracks_change": 25,
    "hours_change": 1.7,
    "artists_change": 5
  }
}
```

**Example**:
```bash
curl "http://localhost:8000/api/v1/analytics/comparison?period1_start=2025-01-01&period1_end=2025-01-15&period2_start=2025-01-16&period2_end=2025-01-31"
```

---

### 4. Listening Heatmap
**Endpoint**: `GET /listening-heatmap`

Generates a heatmap of listening activity by hour of day and day of week.

**Query Parameters**:
- `days` (integer, default: 90) - Number of days to analyze

**Response**:
```json
{
  "data": [
    {
      "hour": "00:00",
      "Monday": 5,
      "Tuesday": 3,
      "Wednesday": 4,
      "Thursday": 6,
      "Friday": 8,
      "Saturday": 12,
      "Sunday": 10
    }
  ],
  "max_value": 42,
  "min_value": 0
}
```

**Example**:
```bash
curl "http://localhost:8000/api/v1/analytics/listening-heatmap?days=90"
```

---

### 5. Mood Timeline
**Endpoint**: `GET /mood-timeline`

Tracks mood distribution over time as a timeline.

**Query Parameters**:
- `days` (integer, default: 30) - Number of days to analyze

**Response**:
```json
{
  "data": [
    {
      "date": "2025-01-01",
      "energetic": 40,
      "calm": 30,
      "melancholic": 20,
      "joyful": 10
    }
  ],
  "moods": ["energetic", "calm", "melancholic", "joyful"],
  "period_days": 30
}
```

**Example**:
```bash
curl "http://localhost:8000/api/v1/analytics/mood-timeline?days=30"
```

---

## Error Responses

All endpoints return appropriate HTTP status codes:

- **200 OK** - Successful request
- **400 Bad Request** - Invalid parameters (e.g., invalid date format)
- **500 Internal Server Error** - Database or server error

**Error Response Format**:
```json
{
  "detail": "Error message describing what went wrong"
}
```

---

## Date Format

All dates should be in ISO 8601 format:
- **Format**: `YYYY-MM-DD`
- **Example**: `2025-01-31`

---

## Rate Limiting

No rate limiting is currently implemented. For production deployment, consider implementing rate limiting to prevent abuse.

---

## Performance Considerations

1. **Large Date Ranges**: Querying with very large date ranges may take longer. Consider limiting to 6-12 months.
2. **Database Indexing**: Ensure `listening_history` table has indexes on `timestamp` and `artist_id` for optimal performance.
3. **Caching**: Results can be cached on the client side for 5-10 minutes.

---

## Integration with Frontend

The `AnalyticsAdvanced.tsx` component integrates all these endpoints:

```typescript
// Advanced stats query
const { data: advancedStats } = useQuery({
  queryKey: ['advanced-stats', startDate, endDate],
  queryFn: async () => {
    const response = await apiClient.get('/api/v1/analytics/advanced-stats', {
      params: { start_date: startDate, end_date: endDate }
    })
    return response.data
  }
})

// Discovery stats query
const { data: discoveryStats } = useQuery({
  queryKey: ['discovery-stats'],
  queryFn: async () => {
    const response = await apiClient.get('/api/v1/analytics/discovery-stats', {
      params: { days: 30 }
    })
    return response.data
  }
})
```

---

## Testing

Run the analytics test suite:
```bash
bash scripts/test-analytics.sh
```

This will test all endpoints and display formatted responses.

---

## Related Endpoints

- `/api/v1/history/patterns` - Basic listening patterns (hourly, weekday)
- `/api/v1/history/haiku` - Generate AI-powered haiku from listening data
- `/api/v1/history` - Raw listening history data

---

## Future Enhancements

- [ ] Artist recommendation based on listening patterns
- [ ] Genre preference prediction
- [ ] Mood prediction from time of day
- [ ] Social sharing of listening stats
- [ ] Custom date range presets ("Last 7 days", "This month", etc.)
- [ ] Export analytics as PDF/CSV
