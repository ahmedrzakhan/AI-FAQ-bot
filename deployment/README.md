# Deployment Guide - Free Tier GCP

This guide helps you deploy the FAQ bot on Google Cloud Platform using **FREE tier resources only**.

## Prerequisites

1. Google Cloud account with free trial credits
2. Google Cloud SDK (`gcloud`) installed
3. Environment variables configured

## Free Tier Deployment Options

### Option 1: Google App Engine (Recommended for demos)
- **Cost**: FREE (within free tier limits)
- **Scaling**: Automatic, scales to zero when not used
- **Perfect for**: Showcasing projects, demonstrations

```bash
# 1. Initialize gcloud (if not done)
gcloud init

# 2. Create new project (optional)
gcloud projects create your-faq-bot-project --name="FAQ Bot Demo"
gcloud config set project your-faq-bot-project

# 3. Enable required APIs
gcloud services enable appengine.googleapis.com

# 4. Deploy to App Engine
gcloud app deploy deployment/app.yaml

# 5. View your deployed app
gcloud app browse
```

### Option 2: Cloud Run (Alternative free option)
- **Cost**: FREE (within free tier limits)
- **Scaling**: Scales to zero, pay-per-request
- **Benefits**: Container-based, more flexible

```bash
# 1. Build and deploy with Cloud Run
gcloud run deploy faq-bot \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --port 8080 \
  --memory 512Mi \
  --cpu 1 \
  --max-instances 1

# 2. Get the service URL
gcloud run services describe faq-bot --platform managed --region us-central1
```

## Environment Variables Setup

Before deploying, set up your environment variables:

```bash
# Set environment variables in GCP
gcloud app deploy --set-env-vars OPENAI_API_KEY=your_key_here,LANGCHAIN_API_KEY=your_langsmith_key_here
```

Or update the `app.yaml` file with your actual keys.

## Free Tier Limits

- **App Engine**: 28 instance hours per day (FREE)
- **Cloud Run**: 2 million requests per month (FREE)
- **Storage**: 5GB (FREE)
- **Outbound Traffic**: 1GB per month (FREE)

## Local Testing

Before deploying, test locally:

```bash
# Backend
cd backend
python main.py

# Frontend (in another terminal)
cd frontend
streamlit run app.py
```

## Monitoring Costs

- Check GCP Console > Billing to monitor usage
- Set up billing alerts at $1-5 to avoid unexpected charges
- App Engine and Cloud Run both scale to zero when not in use

## Showcase Tips

1. **Demo URL**: Use the provided GCP URL for demonstrations
2. **Uptime**: Services auto-sleep when not used (saves money)
3. **Performance**: First request may be slow (cold start)
4. **Logs**: Use `gcloud app logs tail -s default` to monitor