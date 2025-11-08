# Quota System - Investment Performance Tracking

## Overview

The Quota System is a sophisticated feature that allows you to track the **real investment performance** of each wallet, similar to how investment funds calculate quota values. This system separates the effects of cash deposits/withdrawals from actual investment gains/losses.

## Key Concepts

### What is a Quota?

A **quota** is similar to a share in an investment fund. When you deposit money (cash in), you receive quotas at the current quota value. When you withdraw money (cash out), you redeem quotas at the current quota value.

### How It Works

1. **Initial Setup**: When you make your first deposit, you set an initial quota value (default: $1.00)
2. **Cash In**: New deposits buy quotas at the current quota value
3. **Cash Out**: Withdrawals sell quotas at the current quota value
4. **Performance Tracking**: The quota value changes based on your wallet's actual performance, not on deposits/withdrawals

### Example

```
Day 1: Deposit $10,000 at $1.00/quota
  → You receive 10,000 quotas
  → Quota value: $1.00

Day 30: Wallet grows to $11,000 (10% gain)
  → Quota value: $11,000 / 10,000 = $1.10
  → Your performance: +10%

Day 31: Deposit another $5,000
  → You receive 5,000 / $1.10 = 4,545.45 new quotas
  → Total quotas: 14,545.45
  → Net worth: $16,000
  → Quota value: still $1.10 (unchanged by deposit)

Day 60: Wallet grows to $17,000
  → Quota value: $17,000 / 14,545.45 = $1.169
  → Your performance: +16.9% (from initial $1.00)
```

## Features

### 1. Cash Flow Management

- **Manual Registration**: Record cash in/out transactions manually
- **Timestamp Support**: Backdate transactions if needed
- **Description Field**: Add notes to each transaction
- **Automatic Calculation**: Quotas are calculated automatically

### 2. Performance Metrics

The system provides several key metrics:

- **Current Quota Value**: The current value of one quota
- **Performance %**: Percentage change from initial quota value
- **Total Invested**: Net cash deposited (cash in - cash out)
- **Current Net Worth**: Current wallet balance
- **Absolute Gain/Loss**: Net worth - Total invested
- **ROI %**: Return on investment percentage

### 3. Quota Value Chart

Track your quota value over time to see your true investment performance, independent of deposits and withdrawals.

## How to Use

### Step 1: Initialize Quotas

1. Go to a wallet's detail page
2. Click on the "Quota System" tab
3. Click "Add Cash Flow"
4. Record your first deposit:
   - Type: Cash In
   - Amount: Your initial investment
   - Date: When you made the investment
   - Description: "Initial investment"

### Step 2: Record Cash Flows

Whenever you deposit or withdraw funds:

1. Click "Add Cash Flow"
2. Select type (Cash In or Cash Out)
3. Enter the amount in USD
4. Set the date and time
5. Add a description (optional)
6. Click "Add Cash Flow"

### Step 3: Monitor Performance

The system automatically:
- Calculates quota values based on current net worth
- Updates performance metrics
- Generates quota value history charts
- Shows your true ROI

## Important Notes

### ⚠️ Manual Registration Required

The system does **NOT** automatically detect deposits/withdrawals from blockchain transactions. You must manually register all cash flows.

### ✅ Best Practices

1. **Record Immediately**: Register cash flows as soon as they happen
2. **Be Accurate**: Use the exact USD value at the time of transaction
3. **Sync First**: Always sync your wallet before recording cash flows to ensure accurate quota calculations
4. **Consistent Currency**: All amounts should be in USD

### 🔄 Quota Calculation Logic

The quota value is calculated as:

```
Quota Value = Current Net Worth / Total Quota Quantity
```

When you add cash:
```
New Quotas = Cash Amount / Current Quota Value
```

When you withdraw cash:
```
Redeemed Quotas = Cash Amount / Current Quota Value
```

### 📊 Performance vs Net Worth

- **Net Worth Chart**: Shows total wallet value (affected by deposits/withdrawals)
- **Quota Value Chart**: Shows investment performance (NOT affected by deposits/withdrawals)

This separation allows you to see your true trading/investment performance.

## Migration to Production

### Step 1: Run Migration Script

```bash
# SSH into Railway or run in Railway shell
python3 migrate_quota_system.py
```

This will:
- Add quota columns to the wallets table
- Create the cash_flows table
- Create the quota_history table

### Step 2: Deploy Updated Code

The quota system is already integrated into the codebase. Just deploy:

```bash
git add .
git commit -m "Add quota system for investment performance tracking"
git push origin main
```

Railway will automatically deploy the changes.

### Step 3: Verify

1. Visit your application
2. Go to any wallet detail page
3. You should see a new "Quota System" tab
4. Try adding a cash flow

## API Endpoints

### Get Cash Flows
```
GET /api/quota/wallets/<wallet_id>/cash-flows/
```

### Add Cash Flow
```
POST /api/quota/wallets/<wallet_id>/cash-flows/
Body: {
  "type": "in" | "out",
  "amount": 1000.00,
  "description": "Initial investment",
  "timestamp": "2024-10-16T10:00:00"  // optional
}
```

### Delete Cash Flow
```
DELETE /api/quota/wallets/<wallet_id>/cash-flows/<flow_id>/
```

### Get Quota History
```
GET /api/quota/wallets/<wallet_id>/quota-history/?days=30
```

## Troubleshooting

### "No balance history found" Error

**Solution**: Sync your wallet first before adding cash flows. The system needs at least one balance snapshot to calculate quota values.

### Quota Value Seems Wrong

**Possible causes**:
1. Wallet not synced recently
2. Cash flows not recorded accurately
3. Missing cash flow records

**Solution**: 
1. Sync the wallet
2. Review all cash flow records
3. Delete and re-add incorrect entries

### Can't See Quota Tab

**Solution**: 
1. Clear browser cache
2. Hard refresh (Ctrl+Shift+R or Cmd+Shift+R)
3. Check if migration was run successfully

## Support

For issues or questions about the quota system, check:
1. This README
2. The migration script output
3. Browser console for errors
4. Backend logs for API errors

---

**Version**: 1.2.0  
**Last Updated**: October 16, 2024  
**Feature Branch**: feature/quota-system

