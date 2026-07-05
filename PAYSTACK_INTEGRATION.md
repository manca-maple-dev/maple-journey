# Paystack Live Integration - MapleJourney

## Quick Start

### 1. Get Paystack Credentials

Visit https://dashboard.paystack.com/

1. Sign up / Log in
2. Go to **Settings → API Keys & Webhooks**
3. Copy your **Secret Key** and **Public Key**

### 2. Configure Environment

**Backend (.env or Railway environment variables):**

```bash
PAYSTACK_SECRET_KEY="sk_live_xxxxx" # Production key
PAYSTACK_PUBLIC_KEY="pk_live_xxxxx"
```

### 3. Set Up Webhook

In Paystack dashboard:
- Go to **Settings → API Keys & Webhooks**
- Add webhook URL: `https://web-production-1acc6.up.railway.app/api/paystack/webhook`
- Select events: `charge.success`, `charge.failed`, `subscription.create`, `subscription.disable`

### 4. Frontend Integration

```javascript
// Initialize Paystack checkout
const response = await fetch('/api/paystack/checkout/initialize', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ plan_id: 'plus' })
});

const { authorization_url } = await response.json();
window.location.href = authorization_url;
```

## API Endpoints

### One-Time Payment

**POST `/api/paystack/checkout/initialize`**
- Initialize payment for plan upgrade
- Returns Paystack checkout URL
- Accepted payment methods: card, bank, USSD, mobile money

**GET `/api/paystack/verify/{reference}`**
- Verify payment after user returns from Paystack
- Updates transaction status and user plan

### Recurring Subscriptions

**POST `/api/paystack/subscription/subscribe`**
- Subscribe user to recurring plan
- Requires authorization code from initial payment

**POST `/api/paystack/webhook`**
- Handle Paystack webhook events
- Automatically processes charge success/failure
- Updates subscription status

### Customer Info

**GET `/api/paystack/customer/{email}`**
- Get Paystack customer details
- Returns saved payment methods

## Payment Flow

```
1. User clicks "Upgrade to Plus"
   ↓
2. Frontend calls /api/paystack/checkout/initialize
   ↓
3. Backend creates transaction (pending), returns Paystack URL
   ↓
4. User redirected to Paystack checkout (pays with card/bank/USSD)
   ↓
5. After payment, Paystack calls webhook /api/paystack/webhook
   ↓
6. Backend updates transaction status (success/failed)
   ↓
7. Frontend polls /api/paystack/verify/{reference}
   ↓
8. Backend upgrades user plan if payment successful
   ↓
9. Confirmation email sent to user
```

## Pricing - MapleJourney Plans

| Plan | Amount | Currency | Duration |
|------|--------|----------|----------|
| Newcomer | Free | - | - |
| Plus | ₦2,990/mo | NGN (Naira) | Monthly |
| Family | ₦4,990/mo | NGN (Naira) | Monthly |

**Amount in API:** Stored in **kobo** (1/100 of Naira)
- Plus: 299000 kobo = ₦2,990
- Family: 499000 kobo = ₦4,990

## Testing

### Paystack Test Mode

1. Log in to Paystack dashboard
2. Toggle **"Test Mode"** (top-right)
3. Use test card: `4111 1111 1111 1111`
4. Any expiry (future date)
5. Any CVV

### Test Cards
- **Visa**: 4111 1111 1111 1111
- **Mastercard**: 5555 5555 5555 4444
- **Verve** (NG only): 5061 0200 0000 0000

## Advantages

✅ **African Market Leader** - 50+ African countries
✅ **Multiple Payment Methods** - Card, Bank, USSD, Mobile Money
✅ **Instant Verification** - Webhook confirmation
✅ **Recurring Billing** - Built-in subscription support
✅ **Excellent Docs** - Comprehensive API documentation
✅ **Live Support** - 24/7 Nigerian support team

## Security

- ✅ Webhooks signed with HMAC-SHA512
- ✅ Signature verification on every webhook
- ✅ PCI DSS Level 1 compliant
- ✅ No sensitive payment data stored locally

## Troubleshooting

### Issue: "PAYSTACK_SECRET_KEY not configured"
- Check Railway environment variables
- Ensure keys are in production environment (not staging)

### Issue: Webhook not receiving events
- Verify webhook URL in Paystack dashboard
- Check that endpoint is publicly accessible
- Test webhook manually from Paystack dashboard

### Issue: Customer not found in Paystack
- First transaction must complete successfully
- Customer code is then created automatically

## Next Steps

1. ✅ Configure environment variables (PAYSTACK_SECRET_KEY, PAYSTACK_PUBLIC_KEY)
2. ✅ Set webhook in Paystack dashboard
3. ✅ Test with test cards
4. ✅ Switch to production keys for live payments
5. ✅ Monitor transactions in Paystack dashboard

## Support

- Paystack Docs: https://paystack.com/docs/api/
- MapleJourney Issues: Create ticket in repo
- Paystack Support: https://paystack.com/support
