# Elite Command Data API Documentation

## Overview

The Elite Command Data API serves as the central data backbone for an Executive OS designed for multi-business founders managing multiple portfolio companies. It provides unified data ingestion, normalization, intelligence, and insights across all business entities.

## Base URL
```
https://your-domain.com/api
```

## Authentication
All endpoints require proper authentication. Include your API key in the request headers:
```
Authorization: Bearer YOUR_API_KEY
```

## Core Endpoints

### 1. Data Ingestion Endpoints

#### Webhook Ingestion
```http
POST /ingestion/webhook/{source_id}
Content-Type: application/json

{
  "data": {
    "metric_name": "value",
    "timestamp": "2024-01-15T10:30:00Z"
  },
  "source": "custom_tool",
  "event_type": "metric_update"
}
```

#### File Upload
```http
POST /files/upload/{source_id}
Content-Type: multipart/form-data

file: [CSV, PDF, Excel, JSON, or Markdown file]
```

#### Email Processing
```http
POST /email/ingest
Content-Type: application/json

{
  "from": "reports@company.com",
  "subject": "Monthly Business Update",
  "body": "Revenue: $125,000...",
  "attachments": []
}
```

#### OAuth Integration
```http
POST /oauth/connect/{platform}
Content-Type: application/json

{
  "company_id": "company-uuid"
}
```

### 2. Data Normalization Endpoints

#### Process Pending Data
```http
POST /normalize/batch
Content-Type: application/json

{
  "batch_size": 100
}
```

#### Normalize Specific Entry
```http
POST /normalize/entry/{entry_id}
```

#### Get Normalization Status
```http
GET /normalize/status
```

### 3. Intelligence Layer Endpoints

#### Company Brief
```http
GET /intelligence/brief/{company_id}?days=7

Response:
{
  "status": "success",
  "company": {
    "id": "company-uuid",
    "name": "AI Robotics Inc",
    "business_model": "saas",
    "stage": "growth"
  },
  "brief": {
    "health_score": 85,
    "key_metrics": {
      "financial": {
        "revenue": 125000,
        "arr": 1500000,
        "burn_rate": 75000
      },
      "growth": {
        "revenue_growth_rate": 0.15
      }
    },
    "trends": {
      "positive_trends": [
        {
          "metric": "revenue",
          "direction": "increasing",
          "percentage_change": 15.2
        }
      ]
    },
    "alerts": [
      {
        "type": "threshold",
        "severity": "high",
        "message": "Churn rate elevated"
      }
    ],
    "insights": [
      {
        "type": "performance",
        "title": "Strong Unit Economics",
        "description": "LTV:CAC ratio of 4.2:1 indicates healthy customer economics"
      }
    ]
  }
}
```

#### Portfolio Summary
```http
POST /intelligence/portfolio/summary
Content-Type: application/json

{
  "company_ids": ["company-1", "company-2", "company-3"]
}

Response:
{
  "status": "success",
  "portfolio_summary": {
    "total_companies": 3,
    "aggregate_metrics": {
      "total_revenue": 375000,
      "total_arr": 4500000,
      "average_health_score": 78
    },
    "portfolio_trends": [
      {
        "type": "positive",
        "description": "2 companies showing positive trends"
      }
    ],
    "company_rankings": [
      {
        "company_id": "company-1",
        "health_score": 85,
        "performance_score": 80
      }
    ]
  }
}
```

#### Network Signals
```http
GET /intelligence/signals/network

Response:
{
  "status": "success",
  "signals": {
    "intro_opportunities": [
      {
        "type": "customer_intro",
        "description": "Potential customer match identified",
        "confidence": 0.8
      }
    ],
    "relationship_insights": [
      {
        "type": "partnership_opportunity",
        "description": "Complementary business model identified"
      }
    ]
  }
}
```

#### Rituals Status
```http
GET /intelligence/rituals/status?company_id={id}&days=30

Response:
{
  "status": "success",
  "rituals_status": {
    "focus_compliance": {
      "score": 85,
      "trend": "improving"
    },
    "checkin_streaks": {
      "longest_streak": 45,
      "companies_on_streak": 8
    },
    "meeting_drift": {
      "average_drift_minutes": 12,
      "efficiency_score": 78
    }
  }
}
```

#### Company Trends
```http
GET /intelligence/trends/{company_id}?days=30

Response:
{
  "status": "success",
  "trends": {
    "positive_trends": [
      {
        "metric": "revenue",
        "direction": "increasing",
        "confidence": 0.85,
        "percentage_change": 15.2
      }
    ],
    "negative_trends": [],
    "stable_metrics": [
      {
        "metric": "churn_rate",
        "direction": "stable"
      }
    ]
  }
}
```

#### Company Alerts
```http
GET /intelligence/alerts/{company_id}?days=7&severity=high

Response:
{
  "status": "success",
  "alerts": [
    {
      "type": "threshold",
      "severity": "critical",
      "metric": "runway_months",
      "value": 4.2,
      "threshold": 6,
      "message": "Cash runway getting low",
      "action_required": true
    }
  ]
}
```

#### Company Insights
```http
GET /intelligence/insights/{company_id}?days=30&category=performance

Response:
{
  "status": "success",
  "insights": [
    {
      "type": "performance",
      "category": "efficiency",
      "title": "High Revenue Efficiency",
      "description": "Revenue per employee is $185,000, indicating strong productivity",
      "impact": "positive",
      "confidence": 0.8
    }
  ]
}
```

#### Anomaly Detection
```http
GET /intelligence/anomalies/{company_id}?days=30

Response:
{
  "status": "success",
  "anomalies": [
    {
      "metric": "revenue",
      "type": "spike",
      "value": 180000,
      "expected_range": [100000, 150000],
      "severity": "medium",
      "timestamp": "2024-01-15T10:30:00Z"
    }
  ]
}
```

#### Sorted Metrics
```http
GET /intelligence/metrics/sorted/{company_id}

Response:
{
  "status": "success",
  "sorted_metrics": [
    {
      "metric": "revenue",
      "value": 125000,
      "importance": 10,
      "category": "financial"
    },
    {
      "metric": "runway_months",
      "value": 18,
      "importance": 10,
      "category": "financial"
    }
  ]
}
```

## Data Models

### Company
```json
{
  "id": "uuid",
  "name": "string",
  "business_model": "saas|marketplace|ecommerce|consulting",
  "stage": "idea|mvp|growth|scale|mature",
  "domain": "string",
  "founded_date": "date",
  "description": "string"
}
```

### Metric Snapshot
```json
{
  "id": "uuid",
  "company_id": "uuid",
  "metrics": {
    "revenue": 125000,
    "arr": 1500000,
    "churn_rate": 0.032,
    "active_users": 2500
  },
  "snapshot_date": "datetime",
  "confidence_score": 0.85
}
```

### Data Source
```json
{
  "id": "uuid",
  "company_id": "uuid",
  "name": "string",
  "source_type": "webhook|oauth|email|file",
  "config": {},
  "is_active": true,
  "reliability_score": 0.95
}
```

## Error Responses

All endpoints return consistent error responses:

```json
{
  "status": "error",
  "message": "Human-readable error message",
  "error": "Technical error details",
  "code": "ERROR_CODE"
}
```

### Common Error Codes
- `INVALID_COMPANY_ID`: Company not found
- `INSUFFICIENT_DATA`: Not enough data for analysis
- `INVALID_PARAMETERS`: Request parameters are invalid
- `PROCESSING_ERROR`: Internal processing error
- `AUTHENTICATION_FAILED`: Invalid or missing API key

## Rate Limits

- **Standard endpoints**: 1000 requests per hour
- **Intelligence endpoints**: 100 requests per hour
- **File upload endpoints**: 50 requests per hour

## Webhooks

The API can send webhooks for important events:

### Alert Webhook
```json
{
  "event": "alert.created",
  "company_id": "uuid",
  "alert": {
    "type": "threshold",
    "severity": "critical",
    "message": "Cash runway critically low"
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### Data Processing Webhook
```json
{
  "event": "data.processed",
  "company_id": "uuid",
  "records_processed": 15,
  "processing_status": "success",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

## SDK Examples

### Python SDK
```python
from elite_command import EliteCommandAPI

api = EliteCommandAPI(api_key="your-api-key")

# Get company brief
brief = api.get_company_brief("company-id", days=7)

# Get portfolio summary
portfolio = api.get_portfolio_summary(["company-1", "company-2"])

# Upload data file
result = api.upload_file("source-id", "data.csv")
```

### JavaScript SDK
```javascript
import { EliteCommandAPI } from '@elite-command/api';

const api = new EliteCommandAPI({ apiKey: 'your-api-key' });

// Get company brief
const brief = await api.getCompanyBrief('company-id', { days: 7 });

// Get alerts
const alerts = await api.getCompanyAlerts('company-id', { severity: 'high' });
```

## Best Practices

### Data Ingestion
1. **Consistent Timestamps**: Always include UTC timestamps
2. **Data Validation**: Validate data before sending
3. **Batch Processing**: Use batch endpoints for large datasets
4. **Error Handling**: Implement retry logic for failed requests

### Intelligence Queries
1. **Appropriate Time Ranges**: Use reasonable date ranges (7-90 days)
2. **Caching**: Cache results for frequently accessed data
3. **Filtering**: Use filters to reduce response size
4. **Rate Limiting**: Respect rate limits for intelligence endpoints

### Security
1. **API Key Management**: Rotate API keys regularly
2. **HTTPS Only**: Always use HTTPS in production
3. **Input Validation**: Validate all input parameters
4. **Access Control**: Implement proper access controls per company

## Support

For API support and questions:
- Documentation: https://docs.elitecommand.io
- Support Email: api-support@elitecommand.io
- Status Page: https://status.elitecommand.io

