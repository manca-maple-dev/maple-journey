# Benefits API Data Structure & Example Responses

## 1. Complete Benefit Object

```json
{
  "name": "Canada Child Benefit",
  "description": "Monthly payment for families with children under 18",
  "id": "canada_child_benefit",
  "category": "tax",
  "eligibility": [
    "Have Canadian income or reside in Canada",
    "Child under 18 years old",
    "Canadian resident for tax purposes"
  ],
  "max_benefit": "$7,437/year per child (varies by income)",
  "how_to_apply_free": [
    "1. Register child's birth with vital statistics (free)",
    "2. File tax return with CRA (free at NETFILE partners)",
    "3. Apply through CRA My Account (free online)"
  ],
  "free_resources": [
    {
      "name": "CRA My Account",
      "url": "https://www.canada.ca/myaccount",
      "type": "Official portal"
    },
    {
      "name": "Free Tax Clinic",
      "url": "https://www.canada.ca/taxes/freeclinic",
      "type": "Government program"
    },
    {
      "name": "Settlement services (FREE)",
      "url": "https://www.211.ca",
      "type": "211 directory"
    }
  ],
  "avoid_paying_for": "Do NOT pay agents/accountants to apply - it's free through CRA",
  "estimated_yearly_value": "$7437"
}
```

---

## 2. Example Responses

### GET /api/benefits/all
```json
{
  "total_benefits": 12,
  "note": "All benefits shown can be obtained for FREE - never pay agents for these",
  "benefits": [
    { "full benefit objects..." },
    { "..." }
  ]
}
```

### GET /api/benefits/canada_child_benefit
```json
{
  "benefit": {
    "name": "Canada Child Benefit (CCB)",
    "description": "Monthly payment for families with children under 18",
    "category": "tax",
    "eligibility": ["..."],
    "max_benefit": "$7,437/year per child",
    "estimated_yearly_value": "$7437"
  },
  "warning": "⚠️  This benefit is FREE to apply for - never pay agents or consultants",
  "direct_contact": {
    "phone": "1-800-959-8281",
    "website": "https://www.canada.ca/ccb",
    "online": "https://www.canada.ca/myaccount"
  }
}
```

### GET /api/benefits/canada_child_benefit/free-application
```json
{
  "benefit_name": "Canada Child Benefit",
  "free_steps": [
    "1. Register child's birth with vital statistics (free)",
    "2. File tax return with CRA (free at NETFILE partners)",
    "3. Apply through CRA My Account (free online)"
  ],
  "free_resources": [
    {
      "name": "CRA My Account",
      "url": "https://www.canada.ca/myaccount",
      "type": "Official portal"
    }
  ],
  "warning": "Do NOT pay agents/accountants to apply - it's free through CRA",
  "estimated_value": "$7437",
  "typical_scam_cost": "Would cost $100-500 through agent",
  "your_cost": "$0 - FREE"
}
```

### GET /api/benefits/category/tax
```json
{
  "category": "tax",
  "count": 3,
  "benefits": [
    {
      "name": "Canada Child Benefit (CCB)",
      "category": "tax",
      "max_benefit": "$7,437/year per child",
      "estimated_yearly_value": "$7437"
    },
    {
      "name": "Canada Earned Income Tax Credit (EITC)",
      "category": "tax",
      "max_benefit": "$3,995/year",
      "estimated_yearly_value": "$3995"
    }
  ]
}
```

### GET /api/benefits/avoid/scams
```json
{
  "warning": "🚨 Do NOT pay agents for these services - they are FREE from government",
  "potential_money_saved": "$2,500+ if you avoid these scams",
  "common_scams": [
    {
      "scam": "Agent charging to apply for CCB",
      "why_scam": "CCB is free to apply through CRA",
      "cost": "Typically $50-200 per child",
      "actual_cost": "$0 - completely free",
      "free_alternative": "Use CRA My Account or local settlement agency"
    },
    {
      "scam": "Immigration consultant charging for credential assessment",
      "why_scam": "Most assessments are $100-300 from official bodies, agents add markup",
      "cost": "$300-800",
      "actual_cost": "$100-300 direct",
      "free_alternative": "Contact provincial credential recognition body directly"
    }
  ],
  "how_to_report_scam": {
    "rcmp": "1-888-773-8888",
    "consumer_protection": "Contact your provincial consumer protection office",
    "scam_alert": "https://www.antifraudcentre.ca"
  }
}
```

### POST /api/benefits/assess-my-eligibility
**Request:**
```json
{
  "age": 32,
  "annual_income": 28000,
  "has_children": true,
  "immigration_status": "permanent_resident"
}
```

**Response:**
```json
{
  "your_profile": {
    "age": 32,
    "annual_income": 28000,
    "has_children": true,
    "immigration_status": "permanent_resident"
  },
  "assessment": {
    "eligible_benefits": [
      {
        "benefit": "Canada Child Benefit",
        "value": "$7,437/year per child",
        "priority": "HIGH"
      },
      {
        "benefit": "Canada Earned Income Tax Credit",
        "value": "$3,995/year",
        "priority": "HIGH"
      }
    ],
    "total_potential_value": "$11,432/year",
    "total_numeric": 11432,
    "next_steps": [
      "Contact CRA at 1-800-959-8281",
      "Visit local settlement agency via 211.ca",
      "Apply through canada.ca (always free)"
    ]
  },
  "action_plan": [
    {
      "step": 1,
      "benefit": "Canada Child Benefit",
      "priority": "HIGH",
      "estimated_value": "$7,437/year per child",
      "action": "Get free guide at /benefits/canada_child_benefit/free-application"
    },
    {
      "step": 2,
      "benefit": "Canada Earned Income Tax Credit",
      "priority": "HIGH",
      "estimated_value": "$3,995/year",
      "action": "Get free guide at /benefits/earned_income_tax_credit/free-application"
    }
  ],
  "important_note": "All these benefits are FREE to apply for - use the phone numbers and websites provided"
}
```

### GET /api/benefits/my-benefits (Authenticated)
```json
{
  "your_potential_annual_value": "$11,432/year",
  "eligible_benefits": [
    {
      "benefit": "Canada Child Benefit",
      "value": "$7,437/year per child",
      "priority": "HIGH"
    },
    {
      "benefit": "Canada Earned Income Tax Credit",
      "value": "$3,995/year",
      "priority": "HIGH"
    }
  ],
  "recommended_first_steps": [
    "Contact CRA at 1-800-959-8281",
    "Visit local settlement agency via 211.ca",
    "Apply through canada.ca (always free)"
  ],
  "critical_deadlines": [
    {
      "benefit": "Canada Child Benefit",
      "deadline": "ASAP - back payments go back 11 months",
      "impact": "You may be missing thousands in payments"
    }
  ]
}
```

### POST /api/benefits/track-application
**Request:**
```
POST /api/benefits/track-application?benefit_id=canada_child_benefit&status=submitted
```

**Response:**
```json
{
  "benefit": "Canada Child Benefit",
  "current_status": "submitted",
  "next_step": "Wait 4-6 weeks for processing. Check status online.",
  "free_help_phone": "1-800-959-8281",
  "free_legal_help": "Contact legal aid in your province for appeals"
}
```

---

## 3. Error Responses

### Benefit Not Found
```json
{
  "error": "Benefit 'invalid_id' not found"
}
```

### Missing Profile for Personalization
```json
{
  "message": "Please complete your profile first to see personalized benefits",
  "next_step": "Fill out your immigration status, age, family size at /domain/profile"
}
```

---

## 4. Database Schema (MongoDB)

### db.benefits collection
```javascript
{
  "_id": ObjectId(),
  "id": "canada_child_benefit",
  "name": "Canada Child Benefit",
  "description": "Monthly payment for families with children under 18",
  "category": "tax",  // Index on this
  "eligibility": ["..."],
  "max_benefit": "$7,437/year per child (varies by income)",
  "how_to_apply_free": ["..."],
  "free_resources": [
    {
      "name": "CRA My Account",
      "url": "https://...",
      "type": "Official portal"
    }
  ],
  "avoid_paying_for": "Do NOT pay agents/accountants...",
  "estimated_yearly_value": "$7437",
  "created_at": ISODate(),
  "updated_at": ISODate(),
  "province": "National",  // Optional: for province-specific benefits
  "impact_score": 7437     // For sorting by value
}
```

### db.user_applications collection (Future)
```javascript
{
  "_id": ObjectId(),
  "user_id": ObjectId(),
  "benefit_id": "canada_child_benefit",
  "status": "submitted",  // started, submitted, approved, rejected, appeal
  "started_date": ISODate(),
  "submitted_date": ISODate(),
  "expected_completion": ISODate(),
  "notes": "Applied online via CRA My Account",
  "created_at": ISODate(),
  "updated_at": ISODate()
}
```

---

## 5. Status Codes

| Code | Scenario |
|------|----------|
| 200 | Success - benefit found or operation completed |
| 400 | Bad request - invalid parameters |
| 401 | Unauthorized - login required for authenticated endpoints |
| 404 | Not found - benefit doesn't exist |
| 500 | Server error |

---

## 6. Rate Limiting

- Public endpoints: 100 requests/minute
- Authenticated endpoints: 1000 requests/minute
- No rate limit for 211.ca or direct government resources

---

## 7. Response Headers

```
Content-Type: application/json
X-Total-Benefits: 12
X-API-Version: 1.0
Cache-Control: public, max-age=3600
```

---

## 8. Field Definitions

| Field | Type | Description |
|-------|------|-------------|
| name | string | Benefit name (official) |
| description | string | 1-line summary |
| category | string | tax, settlement, employment, housing, education, healthcare, legal |
| eligibility | string[] | List of requirements |
| max_benefit | string | Maximum annual/monthly/one-time value |
| how_to_apply_free | string[] | Step-by-step free application |
| free_resources | object[] | Links, phone numbers, websites |
| avoid_paying_for | string | Warning about scams |
| estimated_yearly_value | string | Annual value in $XXX format |
| priority | string | CRITICAL, HIGH, MEDIUM, LOW |

---

## 9. Testing Examples

### cURL
```bash
# Get all benefits
curl https://web-production-1acc6.up.railway.app/api/benefits/all

# Get specific benefit
curl https://web-production-1acc6.up.railway.app/api/benefits/canada_child_benefit

# Get category
curl https://web-production-1acc6.up.railway.app/api/benefits/category/tax

# Get scams (with jq for pretty print)
curl https://web-production-1acc6.up.railway.app/api/benefits/avoid/scams | jq .

# Get personalized assessment (requires auth)
curl -X POST https://web-production-1acc6.up.railway.app/api/benefits/assess-my-eligibility \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "age": 35,
    "annual_income": 30000,
    "has_children": true,
    "immigration_status": "permanent_resident"
  }'
```

### JavaScript/Node.js
```javascript
// Fetch all benefits
const response = await fetch('https://web-production-1acc6.up.railway.app/api/benefits/all');
const data = await response.json();
console.log(`Found ${data.total_benefits} benefits`);

// Get personalized assessment
const assessment = await fetch(
  'https://web-production-1acc6.up.railway.app/api/benefits/assess-my-eligibility',
  {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${jwtToken}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      age: 35,
      annual_income: 30000,
      has_children: true,
      immigration_status: 'permanent_resident'
    })
  }
);
const result = await assessment.json();
console.log(`Total potential value: ${result.assessment.total_potential_value}`);
```

### Python
```python
import requests

# Get all benefits
response = requests.get(
    'https://web-production-1acc6.up.railway.app/api/benefits/all'
)
benefits = response.json()
print(f"Found {benefits['total_benefits']} benefits")

# Get specific benefit
benefit = requests.get(
    'https://web-production-1acc6.up.railway.app/api/benefits/canada_child_benefit'
).json()
print(f"Max benefit: {benefit['benefit']['max_benefit']}")

# Track application (requires auth)
headers = {'Authorization': f'Bearer {jwt_token}'}
tracking = requests.post(
    'https://web-production-1acc6.up.railway.app/api/benefits/track-application',
    params={
        'benefit_id': 'canada_child_benefit',
        'status': 'submitted'
    },
    headers=headers
).json()
print(f"Next step: {tracking['next_step']}")
```
