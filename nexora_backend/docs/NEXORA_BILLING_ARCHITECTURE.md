# NEXORA Billing Architecture

## Overview

NEXORA uses a SaaS subscription model based on:
- Subscription Plans
- Credit Wallets
- Usage Tracking
- Payment Processing
- Billing Management


# Subscription Plans

## Egypt Pricing (EGP)

| Plan | Price | Credits |
|---|---:|---:|
| Free | 0 EGP | 500 |
| Starter | 199 EGP/month | 5,000 |
| Professional | 799 EGP/month | 50,000 |
| Business | 2,999 EGP/month | 250,000 |
| Enterprise | Custom | Custom |


## International Pricing (USD)

| Plan | Price | Credits |
|---|---:|---:|
| Free | $0 | 500 |
| Starter | $9/month | 5,000 |
| Professional | $39/month | 50,000 |
| Business | $149/month | 250,000 |
| Enterprise | Custom | Custom |


# Credit System

Every user owns a credit wallet.

Wallet fields:

- balance
- monthly_limit
- used_credits
- reset_date


# Credit Consumption

| Operation | Credits |
|---|---:|
| Simple AI Request | 1 |
| Report Generation | 20 |
| PDF Analysis | 50 |
| Image Analysis | 25 |
| Long Agent Task | 100 |


# Billing Modules

Future implementation:

app/billing/

- plans
- subscriptions
- credits
- payments
- invoices
- coupons
- usage


# Currency Engine

Supported currencies:

- EGP
- USD

Currency selection depends on:

- User country
- User preference
- Payment provider


# Payment Providers

Egypt:

- Paymob
- Fawry
- Bank Cards

International:

- Stripe
- PayPal
- Paddle


# Admin Billing Control Center

Platform administrators can:

- Create plans
- Update prices
- Manage credits
- Create coupons
- View subscriptions
- Manage payments
- Review usage


# Future Features

- Free Trial
- Pay As You Go Credits
- Enterprise Contracts
- Usage Analytics
- Invoice Generation
