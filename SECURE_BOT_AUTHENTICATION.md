# Secure Bot Authentication System

This document explains how to use the secure bot authentication system for the CapitalX API.

## Overview

Instead of using username/password authentication, bots can use a secret passphrase system for authentication. This provides several security benefits:

1. **No password exposure** - Bots never need to store or transmit user passwords
2. **Revocable access** - Secrets can be regenerated to revoke bot access
3. **Unique per user** - Each user has their own unique bot secret
4. **Easy to manage** - Users can generate and regenerate secrets through the web interface

## How It Works

1. **Generate a Bot Secret** - Users generate a unique secret through the web interface
2. **Use Secret for Authentication** - Bots use this secret for all API requests
3. **Validate Secret** - API validates the secret and authenticates the user
4. **Access Financial Data** - Authenticated bots can access financial information

## Setup Process

### Step 1: Generate Your Bot Secret

1. Log in to your CapitalX account through the web interface
2. Visit the bot secret generation endpoint:
   ```
   http://127.0.0.1:8000/api/generate-bot-secret/
   ```
3. Copy the generated secret from the JSON response:
   ```json
   {
     "success": true,
     "secret": "YOUR_BOT_SECRET_HERE",
     "message": "Bot secret generated successfully. Keep this secret safe!"
   }
   ```

### Step 2: Use the Secret in Your Bot

Store the secret securely in your bot's configuration and use it for authentication:

```python
import requests

# Your bot secret
BOT_SECRET = "YOUR_BOT_SECRET_HERE"
BASE_URL = "http://127.0.0.1:8000"

# Validate the secret (optional but recommended)
def validate_secret():
    url = f"{BASE_URL}/api/validate-bot-secret/"
    data = {'secret': BOT_SECRET}
    response = requests.post(url, json=data)
    return response.json()

# Get financial information
def get_financial_info():
    url = f"{BASE_URL}/api/bot/financial-info/"
    data = {'secret': BOT_SECRET}
    response = requests.post(url, json=data)
    return response.json()
```

## API Endpoints

### 1. Generate Bot Secret
- **Endpoint**: `/api/generate-bot-secret/`
- **Method**: GET
- **Authentication**: Requires user login session
- **Response**:
  ```json
  {
    "success": true,
    "secret": "abcd1234efgh5678ijkl9012mnop3456qrst7890",
    "message": "Bot secret generated successfully. Keep this secret safe!"
  }
  ```

### 2. Validate Bot Secret
- **Endpoint**: `/api/validate-bot-secret/`
- **Method**: POST
- **Authentication**: None (public endpoint)
- **Request Body**:
  ```json
  {
    "secret": "abcd1234efgh5678ijkl9012mnop3456qrst7890"
  }
  ```
- **Response** (valid secret):
  ```json
  {
    "success": true,
    "valid": true,
    "user": {
      "id": 1,
      "username": "user123",
      "email": "user@example.com"
    }
  }
  ```
- **Response** (invalid secret):
  ```json
  {
    "success": true,
    "valid": false,
    "error": "Invalid secret"
  }
  ```

### 3. Get Financial Information
- **Endpoint**: `/api/bot/financial-info/`
- **Method**: POST
- **Authentication**: Bot secret in request body
- **Request Body**:
  ```json
  {
    "secret": "abcd1234efgh5678ijkl9012mnop3456qrst7890"
  }
  ```
- **Response**:
  ```json
  {
    "success": true,
    "user": {
      "username": "user123",
      "email": "user@example.com"
    },
    "wallet": {
      "balance": 1000.00
    },
    "investments": {
      "active": [
        {
          "id": 1,
          "company": "Company Name",
          "amount": 500.00,
          "return_amount": 600.00,
          "start_date": "2025-01-01T00:00:00",
          "end_date": "2025-01-08T00:00:00",
          "days_remaining": 7
        }
      ],
      "total_active_amount": 500.00
    },
    "plan_investments": {
      "active": [],
      "total_active_amount": 0.00
    },
    "recent_deposits": [
      {
        "id": 1,
        "amount": 1000.00,
        "payment_method": "card",
        "created_at": "2025-01-01T10:00:00"
      }
    ],
    "recent_withdrawals": [],
    "summary": {
      "total_balance": 1000.00,
      "total_active_investments": 500.00,
      "total_plan_investments": 0.00
    }
  }
  ```

## Security Best Practices

### 1. Keep Secrets Secure
- Never hardcode secrets in source code
- Use environment variables or secure configuration files
- Rotate secrets periodically
- Revoke secrets if they might be compromised

### 2. Transport Security
- Use HTTPS in production (HTTP is only for development)
- Validate SSL certificates
- Use secure connections for all API requests

### 3. Access Control
- Generate separate secrets for different bots/applications
- Monitor API usage
- Revoke unused secrets

### 4. Error Handling
- Handle authentication failures gracefully
- Log security-related events
- Implement rate limiting to prevent abuse

## Example Implementation

See `secure_bot_example.py` for a complete example implementation:

```bash
python secure_bot_example.py
```

## Troubleshooting

### Common Issues

1. **Invalid Secret**: Generate a new secret through the web interface
2. **Connection Refused**: Ensure the Django server is running
3. **Timeout Errors**: Check network connectivity
4. **JSON Parsing Errors**: Verify the server is returning valid JSON

### Debugging Steps

1. **Verify server is running**:
   ```bash
   curl http://127.0.0.1:8000/api/test/
   ```

2. **Test secret validation**:
   ```bash
   curl -X POST -H "Content-Type: application/json" \
        -d '{"secret":"YOUR_SECRET_HERE"}' \
        http://127.0.0.1:8000/api/validate-bot-secret/
   ```

3. **Test financial info endpoint**:
   ```bash
   curl -X POST -H "Content-Type: application/json" \
        -d '{"secret":"YOUR_SECRET_HERE"}' \
        http://127.0.0.1:8000/api/bot/financial-info/
   ```

## Support

For issues with the bot authentication system:
1. Ensure you're using the correct bot secret
2. Verify the Django server is running
3. Check that you have network connectivity
4. Review the security logs for authentication failures