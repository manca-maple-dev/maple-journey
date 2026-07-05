# MapleJourney Benefits API - Quick Reference

## 🎯 Purpose
Help newcomers access government benefits for **FREE** and avoid paying agents $100-500+ for services the government provides free.

---

## 📚 Available Endpoints

### Public Endpoints (No Login Required)

#### 1. Get All Benefits
```bash
GET /api/benefits/all
```
**Returns:** All 12+ benefits with full details
- Eligibility criteria
- Max benefits amount
- FREE application steps
- Direct resource links

#### 2. Get Specific Benefit
```bash
GET /api/benefits/{benefit_id}

Examples:
- /api/benefits/canada_child_benefit
- /api/benefits/gis_benefit
- /api/benefits/student_financial_aid
- /api/benefits/legal_aid
```

#### 3. Get FREE Application Guide
```bash
GET /api/benefits/{benefit_id}/free-application

Returns:
- Step-by-step FREE process
- Free resources and phone numbers
- Estimated value
- What NOT to pay for
```

#### 4. Browse by Category
```bash
GET /api/benefits/category/{category}

Categories:
- tax (tax credits, EITC, etc.)
- settlement (resettlement allowance, programs)
- employment (job support, income assistance)
- housing (rent subsidies)
- education (student aid, grants)
- healthcare (prescriptions, medical)
- legal (legal aid services)
```

#### 5. Avoid Scams
```bash
GET /api/benefits/avoid/scams

Returns:
- Common scams (agents charging for free services)
- How much agents charge
- Actual cost ($0)
- FREE alternatives
- How to report scams
```

---

### Authenticated Endpoints (Login Required)

#### 6. Get Your Eligibility
```bash
POST /api/benefits/assess-my-eligibility

Body:
{
  "age": 35,
  "annual_income": 30000,
  "has_children": true,
  "immigration_status": "permanent_resident"
}

Returns:
- All benefits you likely qualify for
- Total potential yearly value
- Priority order (what to apply for first)
- Action plan
```

#### 7. Get Your Personalized Benefits
```bash
GET /api/benefits/my-benefits

Returns:
- Benefits matched to your profile
- Tailored next steps
- Critical application deadlines
- Local resources (from 211.ca)
```

#### 8. Track Your Application
```bash
POST /api/benefits/track-application?benefit_id=canada_child_benefit&status=submitted

Status options:
- started
- submitted
- approved
- rejected
- appeal

Returns:
- Current status
- What to do next
- Free legal help info if needed
```

---

## 💰 Benefits Available (as of July 2026)

| Benefit | Annual Value | Min Steps | Typical Agent Cost | Your Cost |
|---------|--------------|-----------|-------------------|-----------|
| Canada Child Benefit | $7,437/yr | 3 | $100-200 | FREE |
| Guaranteed Income Supplement | $19,000+/yr | 2 | $50-100 | FREE |
| Earned Income Tax Credit | $3,995/yr | 2 | $75-150 | FREE |
| Student Loans & Grants | $15,000+/yr | 2 | $50-200 | FREE |
| Rent Subsidies | 75% of rent | 3 | $100-300 | FREE |
| Legal Aid | Full representation | 2 | Varies | FREE |
| Settlement Programs | $15,000+/yr | 1 | N/A | FREE |
| Prescription Assistance | Varies | 2 | $20-50/mo | FREE |

---

## 🔥 Example Use Cases

### Scenario 1: New Parent with Child
```bash
# Get help applying for Canada Child Benefit
GET /api/benefits/canada_child_benefit

# Response includes:
# - Eligible immediately after birth registration
# - Back-payment up to 11 months if you apply late
# - CRA phone: 1-800-959-8281
# - Online: CRA My Account (free)
# - Estimated value: $7,437/year
```

### Scenario 2: Low-Income Worker
```bash
# Discover all benefits you might qualify for
POST /api/benefits/assess-my-eligibility
{
  "age": 45,
  "annual_income": 25000,
  "has_children": false,
  "immigration_status": "permanent_resident"
}

# Response suggests:
# 1. EITC ($3,995/yr) - APPLY FIRST
# 2. Rent subsidies - IF YOU RENT
# 3. Provincial programs - LOCATION-DEPENDENT
# Total potential: $18,000+/yr
```

### Scenario 3: Student
```bash
# Get student aid information
GET /api/benefits/student_financial_aid

# Response includes:
# - Grants (never repay)
# - Loans (government interest-free options)
# - Work-study programs
# - Scholarship databases (free search)
# Total potential: $15,000+/year
```

### Scenario 4: Avoid Paying Agent
```bash
# See what scammers charge vs. reality
GET /api/benefits/avoid/scams

# Response shows:
# Scam: "Agent charging $200 to apply for CCB"
# Reality: "Apply FREE on CRA My Account in 10 minutes"
# Money saved: $200
```

---

## 🌐 Direct Government Resources

### By Category

**Tax Benefits:**
- CRA My Account: https://www.canada.ca/myaccount
- Call: 1-800-959-8281
- Free Tax Clinics: https://www.canada.ca/taxes/freeclinic

**Settlement:**
- 211.ca: Find local FREE settlement services
- IRCC: https://www.canada.ca/ircc
- Call: 1-888-242-2342

**Student Aid:**
- National: https://www.canada.ca/studentloans
- Call: 1-888-815-4514
- Provincial programs (varies)

**Employment:**
- Job Bank: https://www.jobbank.gc.ca (FREE job search)
- Service Canada: 1-800-O-CANADA

**Legal:**
- Legal Aid: Search your province via 211.ca
- Community Legal Clinics (FREE consultations)

---

## 🚨 Red Flags - Never Pay For:

❌ **Paid Services That Should Be FREE:**
- CCB (Child Benefit) applications
- Tax credit applications
- Student aid applications
- Housing subsidy applications
- Credential assessments (direct = cheaper)
- Immigration renewals
- SIN applications
- Language training (settlement offers FREE)

**Cost of paying wrong person:** $100-500 per benefit
**Actual cost:** $0

---

## 📊 Quick Stats

- **12+ benefits** covered
- **$0 cost** to apply for any benefit
- **Up to $100,000+** in potential benefits over 10 years
- **20+ direct government resources** linked
- **9+ common scams** documented with FREE alternatives

---

## 🔐 Privacy & Security

- ✅ All endpoints use HTTPS
- ✅ No personal data shared with third parties
- ✅ Authentication required for personalized benefits
- ✅ Direct government links only
- ✅ No agent/consultant intermediaries

---

## 💡 Pro Tips

1. **Apply ASAP** - Many benefits have retroactive periods (like CCB = 11 months back)
2. **Check 211.ca** - Find local FREE settlement services in your area
3. **Call first** - Government offices often answer questions free over phone
4. **Use My Account** - CRA's online portal is faster than calling
5. **Track your applications** - Use the `/track-application` endpoint
6. **Set calendar reminders** - For renewal dates and deadlines

---

## 📞 Emergency Contacts

| Issue | Contact | Cost |
|-------|---------|------|
| Tax questions | CRA 1-800-959-8281 | FREE |
| Immigration | IRCC 1-888-242-2342 | FREE |
| Settlement help | 211.ca | FREE |
| Legal issues | Legal Aid (Province) | FREE if eligible |
| Job search | Service Canada | FREE |
| General info | 1-800-O-CANADA | FREE |

---

## 🚀 Coming Soon

- ✅ Province-specific benefits filtering
- ✅ Application deadline reminders  
- ✅ Integration with Maple Wing (AI assistant)
- ✅ Multilingual support (French, Spanish, Mandarin)
- ✅ Community reviews of government programs
- ✅ Mobile app push notifications

---

## Questions?

Use `/api/benefits/all` to explore all available benefits, or contact local settlement agency via 211.ca for personalized guidance.

**Remember: The government NEVER charges fees for benefits applications. If someone asks for money, it's a scam.**
