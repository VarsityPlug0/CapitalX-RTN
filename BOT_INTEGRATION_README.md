# CapitalX Bot Integration Guide

This guide explains how to connect your bot to the CapitalX financial information API.

## Prerequisites

1. The CapitalX Django application must be running
2. You need a valid user account
3. You need to obtain an API token

## Step 1: Start the Server

Make sure the Django server is running:

```bash
python manage.py runserver
```

The server should be accessible at `http://127.0.0.1:8000`

## Step 2: Get Your API Token

### Method 1: Manual (Recommended for beginners)

1. Open your web browser and navigate to: `http://127.0.0.1:8000/login/`
2. Log in with your credentials
3. After logging in, visit: `http://127.0.0.1:8000/api/generate-token/`
4. Copy the token from the JSON response:
   ```json
   {
     "success": true,
     "token": "abcd1234efgh5678ijkl9012mnop3456qrst7890",
     "user": {
       "username": "your_username",
       "email": "your_email@example.com"
     }
   }
   ```

### Method 2: Using the Helper Script

Run the helper script to get instructions:

```bash
python get_token_simple.py
```

## Step 3: Use the Token in Your Bot

Once you have your API token, you can use it to authenticate your bot's requests:

### Python Example

```python
import requests

# Replace with your actual API token
API_TOKEN = "abcd1234efgh5678ijkl9012mnop3456qrst7890"
BASE_URL = "http://127.0.0.1:8000"

# Set up authentication headers
headers = {
    'Authorization': f'Token {API_TOKEN}',
    'Content-Type': 'application/json'
}

# Get financial information
response = requests.get(
    f"{BASE_URL}/api/user/financial-info/",
    headers=headers
)

if response.status_code == 200:
    data = response.json()
    print(f"Wallet Balance: R{data['wallet']['balance']}")
    print(f"Active Investments: R{data['investments']['total_active_amount']}")
else:
    print(f"Error: {response.status_code} - {response.text}")
```

## Available API Endpoints

### 1. Financial Information
- **Endpoint**: `/api/user/financial-info/`
- **Method**: GET
- **Description**: Returns comprehensive financial information
- **Response**:
  ```json
  {
    "success": true,
    "user": {
      "username": "string",
      "email": "string"
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

### 2. Test Endpoint
- **Endpoint**: `/api/test/`
- **Method**: GET
- **Description**: Simple test endpoint to verify API connectivity
- **Response**:
  ```json
  {
    "message": "API is working!",
    "status": "success"
  }
  ```

## Example Bot Implementation

See the complete example in `complete_bot_example.py`:

```bash
python complete_bot_example.py
```

## Security Considerations

1. **Keep your API token secret** - Treat it like a password
2. **Use HTTPS in production** - The current setup uses HTTP which is not secure
3. **Limit token scope** - The token provides access to financial information
4. **Regenerate tokens periodically** - You can generate a new token which invalidates the old one

## Troubleshooting

### Common Issues

1. **401 Unauthorized**: Check that your API token is correct
2. **400 Bad Request**: Ensure the server is running and accessible
3. **Connection Refused**: Verify the server is running on the correct port
4. **JSON Parsing Error**: Check that you're receiving a valid JSON response

### Debugging Steps

1. Verify the server is running:
   ```bash
   curl http://127.0.0.1:8000/api/test/
   ```

2. Check your API token:
   ```bash
   curl -H "Authorization: Token YOUR_TOKEN_HERE" http://127.0.0.1:8000/api/test/
   ```

3. Test the financial info endpoint:
   ```bash
   curl -H "Authorization: Token YOUR_TOKEN_HERE" http://127.0.0.1:8000/api/user/financial-info/
   ```

## Support

For issues with the API or bot integration, please check:
1. That the Django server is running
2. That you're using the correct API token
3. That you have network connectivity to the server