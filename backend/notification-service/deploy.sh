#!/bin/bash

echo "🚀 Deploying Notification Service for Edo Sushi Bar..."
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Step 1: Deploy notification-service
echo -e "${YELLOW}Step 1/3: Deploying notification-service...${NC}"
cd backend/notification-service
sls deploy --stage dev

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Notification service deployed successfully!${NC}"
else
    echo "❌ Error deploying notification-service"
    exit 1
fi

echo ""
echo -e "${YELLOW}⚠️  IMPORTANT: Copy the SNS Topic ARN and SQS Queue URL from above${NC}"
echo ""
read -p "Press Enter to continue..."

# Step 2: Configure SNS Email Subscription
echo ""
echo -e "${YELLOW}Step 2/3: Configure SNS Email Subscription${NC}"
echo "1. Go to AWS Console → SNS → Topics"
echo "2. Select 'EdoOrderNotifications'"
echo "3. Click 'Create subscription'"
echo "4. Protocol: Email"
echo "5. Endpoint: your-email@example.com"
echo "6. Click 'Create subscription'"
echo "7. Check your email and CONFIRM the subscription"
echo ""
read -p "Press Enter when you've confirmed the email subscription..."

# Step 3: Update orders-service
echo ""
echo -e "${YELLOW}Step 3/3: Update orders-service environment variables${NC}"
echo "Add this to backend/orders-service/serverless.yml:"
echo ""
echo "provider:"
echo "  environment:"
echo "    NOTIFICATION_QUEUE_URL: <YOUR_SQS_QUEUE_URL>"
echo ""
read -p "Press Enter when you've updated serverless.yml..."

cd ../orders-service
sls deploy --stage dev

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Orders service updated successfully!${NC}"
else
    echo "❌ Error deploying orders-service"
    exit 1
fi

echo ""
echo -e "${GREEN}🎉 Deployment Complete!${NC}"
echo ""
echo "Next steps:"
echo "1. Create a test order from the frontend"
echo "2. Check your email for the confirmation"
echo "3. Update order status from staff panel"
echo "4. Check your email for status updates"
echo ""
echo "To monitor: sls logs -f processNotification --tail"
